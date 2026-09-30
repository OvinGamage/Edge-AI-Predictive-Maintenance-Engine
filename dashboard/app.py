from datetime import datetime
from typing import TypedDict

import pandas as pd
import serial
import streamlit as st

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

st.session_state.setdefault("uart", None)
st.session_state.setdefault("events", [])
st.session_state.setdefault("connection_error", "")

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

    if connect:
        current_uart = st.session_state.uart
        if current_uart is not None:
            current_uart.close()
        try:
            st.session_state.uart = serial.serial_for_url(
                endpoint,
                baudrate=int(baud_rate),
                timeout=0.05,
            )
            st.session_state.connection_error = ""
        except serial.SerialException as error:
            st.session_state.uart = None
            st.session_state.connection_error = str(error)

    if disconnect:
        current_uart = st.session_state.uart
        if current_uart is not None:
            current_uart.close()
        st.session_state.uart = None

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
def telemetry_view(mode: str) -> None:
    read_uart_events()
    events: list[TelemetryEvent] = st.session_state.events
    latest = events[-1] if events else None
    if mode == "Normal":
        render_normal(events, latest)
    else:
        render_advanced(events, latest)


telemetry_view(view_mode)
