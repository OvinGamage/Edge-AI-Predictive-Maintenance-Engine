import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx


def _acquire_dashboard_lock():
    lock_name = hashlib.sha256(str(Path(__file__).resolve()).encode()).hexdigest()[:16]
    lock_file = open(Path(tempfile.gettempdir()) / f"edge-ai-dashboard-{lock_name}.lock", "a+b")
    lock_file.seek(0)
    try:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (OSError, BlockingIOError):
        lock_file.close()
        return None
    return lock_file


def _release_dashboard_lock(lock_file) -> None:
    try:
        lock_file.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
    finally:
        lock_file.close()


if (
    __name__ == "__main__"
    and os.environ.get("EDGE_AI_STREAMLIT_CHILD") != "1"
    and get_script_run_ctx(suppress_warning=True) is None
):
    lock_file = _acquire_dashboard_lock()
    if lock_file is None:
        print("The dashboard is already running.")
        raise SystemExit(1)
    try:
        answer = input("Press y to start the dashboard: ").strip().lower()
        if answer != "y":
            print("Dashboard startup cancelled.")
            raise SystemExit(0)
        child_environment = os.environ.copy()
        child_environment["EDGE_AI_STREAMLIT_CHILD"] = "1"
        _release_dashboard_lock(lock_file)
        lock_file = None
        raise SystemExit(
            subprocess.call(
                [sys.executable, "-m", "streamlit", "run", str(Path(__file__).resolve())],
                env=child_environment,
            )
        )
    finally:
        if lock_file is not None:
            _release_dashboard_lock(lock_file)

import atexit
import shutil
import threading
import time
from datetime import datetime
from typing import TypedDict

import pandas as pd
import serial
from streamlit.runtime.runtime import Runtime

from uart_bridge import parse_line


class TelemetryEvent(TypedDict):
    received_at: datetime
    status: str
    mse: float | None
    message: str


st.set_page_config(
    page_title="Predictive Maintenance Telemetry",
    page_icon="PM",
    layout="wide",
)


@st.cache_resource
def _streamlit_instance_lock():
    return _acquire_dashboard_lock()


_dashboard_lock = _streamlit_instance_lock()
if _dashboard_lock is None:
    st.error("Another dashboard instance is already running. Close it before starting a new one.")
    st.stop()

st.session_state.setdefault("uart", None)
st.session_state.setdefault("events", [])
st.session_state.setdefault("connection_error", "")
st.session_state.setdefault("auto_connect_enabled", True)


def _docker_info(docker: str) -> bool:
    try:
        result = subprocess.run(
            [docker, "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _start_firmware_backend(state: dict[str, str]) -> None:
    project_root = Path(__file__).resolve().parent.parent
    firmware_path = project_root / "build" / "clang-cmake" / "firmware" / "firmware_app.elf"
    docker = shutil.which("docker")
    if docker is None:
        state["error"] = "Docker CLI was not found. Install Docker Desktop and add Docker to PATH."
        return
    if not firmware_path.is_file():
        state["error"] = f"Firmware ELF not found: {firmware_path}"
        return

    try:
        if not _docker_info(docker):
            state["message"] = "Starting Docker Desktop..."
            subprocess.run(
                [docker, "desktop", "start", "--detach", "--timeout", "120"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,
            )
            deadline = time.monotonic() + 120
            while time.monotonic() < deadline and not _docker_info(docker):
                time.sleep(2)
            if not _docker_info(docker):
                raise RuntimeError("Docker Desktop did not become ready within 120 seconds.")

        running = subprocess.run(
            [docker, "ps", "--filter", "publish=5555", "--format", "{{.ID}}"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        if running:
            state["message"] = "Firmware simulator is already running; connecting to UART."
            return

        state["message"] = "Starting firmware simulator..."
        process = subprocess.Popen(
            [
                docker,
                "compose",
                "run",
                "--rm",
                "-p",
                "127.0.0.1:5555:5555",
                "dev-environment",
                "qemu-system-arm",
                "-M",
                "mps2-an385",
                "-cpu",
                "cortex-m3",
                "-kernel",
                "build/clang-cmake/firmware/firmware_app.elf",
                "-display",
                "none",
                "-monitor",
                "none",
                "-chardev",
                "socket,id=uart0,host=0.0.0.0,port=5555,server=on,wait=on",
                "-serial",
                "chardev:uart0",
            ],
            cwd=project_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("The firmware simulator exited while starting.")
            running = subprocess.run(
                [docker, "ps", "--filter", "publish=5555", "--format", "{{.ID}}"],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout.strip()
            if running:
                state["container_id"] = running.splitlines()[0]
                state["docker"] = docker
                state["message"] = "Firmware simulator is ready; connecting to UART."
                return
            time.sleep(1)
        raise RuntimeError("The firmware simulator did not start within 180 seconds.")
    except (OSError, subprocess.SubprocessError, RuntimeError) as error:
        state["error"] = str(error)


@st.cache_resource
def start_firmware_backend() -> dict[str, str]:
    state: dict[str, str] = {"message": "Preparing firmware simulator...", "error": ""}
    threading.Thread(target=_start_firmware_backend, args=(state,), daemon=True).start()

    def stop_owned_container() -> None:
        container_id = state.get("container_id")
        docker = state.get("docker")
        if container_id and docker:
            subprocess.run(
                [docker, "stop", container_id],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=15,
            )

    atexit.register(stop_owned_container)
    return state


backend_state = start_firmware_backend()


def connect_uart(endpoint: str, baud_rate: int) -> None:
    current_uart = st.session_state.uart
    if current_uart is not None:
        current_uart.close()
    try:
        st.session_state.uart = serial.serial_for_url(
            endpoint,
            baudrate=baud_rate,
            timeout=0.05,
        )
        st.session_state.connection_error = ""
    except serial.SerialException as error:
        st.session_state.uart = None
        st.session_state.connection_error = str(error)

with st.sidebar:
    view_mode = st.radio(
        "View",
        ["Normal", "Advanced diagnostics"],
        index=0,
    )
    st.divider()
    st.header("Device connection")
    endpoint = st.text_input(
        "Device address",
        value="socket://127.0.0.1:5555",
    )
    with st.expander("Connection settings"):
        baud_rate = st.number_input("Baud rate", min_value=1200, value=115200, step=1200)

    connect_col, disconnect_col = st.columns(2)
    connect = connect_col.button("Connect", use_container_width=True)
    disconnect = disconnect_col.button("Disconnect", use_container_width=True)
    stop_dashboard = st.button("Stop dashboard", use_container_width=True)
    st.caption("Before closing this window, click Stop dashboard to shut down the server.")

    if connect:
        st.session_state.auto_connect_enabled = True
        connect_uart(endpoint, int(baud_rate))

    if disconnect:
        current_uart = st.session_state.uart
        if current_uart is not None:
            current_uart.close()
        st.session_state.uart = None
        st.session_state.auto_connect_enabled = False

    if stop_dashboard:
        current_uart = st.session_state.uart
        if current_uart is not None:
            current_uart.close()
            st.session_state.uart = None
        Runtime.instance().stop()
        st.stop()

    connected = st.session_state.uart is not None
    st.caption(f"Device: {'Connected' if connected else 'Disconnected'}")
    if st.session_state.connection_error:
        st.error(st.session_state.connection_error)


def read_uart_events() -> None:
    uart = st.session_state.uart
    if uart is None:
        return

    try:
        raw_line = uart.readline()
    except serial.SerialException as error:
        st.session_state.connection_error = str(error)
        uart.close()
        st.session_state.uart = None
        return

    if not raw_line:
        return

    parsed = parse_line(raw_line.decode("utf-8", errors="replace"))
    if parsed is not None:
        status = parsed["status"]
        message = parsed["message"]
        mse_value = parsed["mse"]
        if isinstance(status, str) and isinstance(message, str):
            mse = float(mse_value) if isinstance(mse_value, (int, float)) else None
            event: TelemetryEvent = {
                "received_at": datetime.now(),
                "status": status,
                "mse": mse,
                "message": message,
            }
            st.session_state.events.append(event)

    st.session_state.events = st.session_state.events[-500:]


def render_normal(events: list[TelemetryEvent], latest: TelemetryEvent | None) -> None:
    st.title("Machine health")
    st.caption("Current status and recent activity")

    if latest is None:
        st.info("Connect to a device to see its current health status.")
        return

    health_event = next(
        (event for event in reversed(events) if event["status"] in {"ok", "warning", "critical", "error"}),
        latest,
    )
    status = str(health_event["status"])
    messages = {
        "ok": (
            "Operating normally",
            "No abnormal behavior was reported in the latest check.",
        ),
        "warning": (
            "Inspection recommended",
            "The latest check found a possible issue. Plan an inspection.",
        ),
        "critical": (
            "Immediate attention needed",
            "The latest check found a serious issue. Follow your equipment shutdown procedure and inspect the system.",
        ),
        "error": (
            "Device reported an error",
            "Check the device connection and firmware status.",
        ),
        "system": (
            "Device is communicating",
            "The device sent a status message but has not reported a health result yet.",
        ),
    }
    title, description = messages.get(status, ("Status unavailable", "The device sent an unrecognized status."))
    if status == "ok":
        st.success(f"{title}\n\n{description}")
    elif status == "warning":
        st.warning(f"{title}\n\n{description}")
    elif status in {"critical", "error"}:
        st.error(f"{title}\n\n{description}")
    else:
        st.info(f"{title}\n\n{description}")

    received_at = latest["received_at"]
    last_update = received_at.strftime("%H:%M:%S")
    metric_columns = st.columns(2)
    metric_columns[0].metric("Last update", last_update)
    metric_columns[1].metric("Messages received", len(events))

    st.subheader("Recent activity")
    history = pd.DataFrame(events)
    history["status"] = history["status"].map(
        {
            "ok": "Operating normally",
            "warning": "Inspection recommended",
            "critical": "Immediate attention needed",
            "error": "Device error",
            "system": "Device update",
        }
    ).fillna("Status update")
    history["received_at"] = history["received_at"].map(
        lambda value: value.strftime("%H:%M:%S") if isinstance(value, datetime) else ""
    )
    st.dataframe(
        history[["received_at", "status"]].tail(10).sort_index(ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={"received_at": "Time", "status": "Status"},
    )


def render_advanced(events: list[TelemetryEvent], latest: TelemetryEvent | None) -> None:
    st.title("Advanced diagnostics")
    st.caption("Firmware status, reconstruction error, and received serial messages")

    if latest is None:
        st.info("Connect to a device to view diagnostics.")
        return

    history = pd.DataFrame(events)
    mse = next((event["mse"] for event in reversed(events) if event["mse"] is not None), None)
    mse_label = f"{mse:.5f}" if mse is not None else "N/A"
    health_event = next(
        (event for event in reversed(events) if event["status"] in {"ok", "warning", "critical", "error"}),
        latest,
    )
    metric_columns = st.columns(3)
    metric_columns[0].metric("Latest health result", str(health_event["status"]).upper())
    metric_columns[1].metric("Latest reconstruction MSE", mse_label)
    metric_columns[2].metric("Events received", len(events))

    inference_events = history.dropna(subset=["mse"])
    if not inference_events.empty:
        st.subheader("Reconstruction error")
        if inference_events["mse"].nunique() > 1:
            st.line_chart(inference_events.set_index("received_at")[["mse"]], y="mse")
        else:
            st.info(f"The reported MSE is steady at {mse_label}.")

    st.subheader("Raw UART events")
    st.dataframe(
        history[["received_at", "status", "mse", "message"]]
        .tail(100)
        .sort_values("received_at", ascending=False),
        use_container_width=True,
        hide_index=True,
    )


@st.fragment(run_every=0.5)
def telemetry_view(mode: str, endpoint: str, baud_rate: int) -> None:
    if backend_state["error"]:
        st.warning(f"Simulator: {backend_state['error']}")
    else:
        st.caption(f"Simulator: {backend_state['message']}")
    if st.session_state.uart is None and st.session_state.auto_connect_enabled:
        connect_uart(endpoint, baud_rate)
    if st.session_state.connection_error:
        st.warning(st.session_state.connection_error)
    read_uart_events()
    events: list[TelemetryEvent] = st.session_state.events
    latest = events[-1] if events else None
    if mode == "Normal":
        render_normal(events, latest)
    else:
        render_advanced(events, latest)


telemetry_view(view_mode, endpoint, int(baud_rate))
