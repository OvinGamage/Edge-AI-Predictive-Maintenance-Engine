from datetime import datetime
from typing import TypedDict

from uart_bridge import parse_line


class TelemetryEvent(TypedDict):
    received_at: datetime
    status: str
    mse: float | None
    message: str


def parse_telemetry_event(
    line: str, received_at: datetime | None = None
) -> TelemetryEvent | None:
    parsed = parse_line(line)
    if parsed is None:
        return None
    return {
        "received_at": received_at or datetime.now(),
        "status": str(parsed["status"]),
        "mse": parsed["mse"] if isinstance(parsed["mse"], float) else None,
        "message": str(parsed["message"]),
    }


def retain_recent_events(
    events: list[TelemetryEvent], limit: int = 500
) -> list[TelemetryEvent]:
    if limit < 0:
        raise ValueError("Event limit cannot be negative.")
    return events[-limit:] if limit else []


def latest_health_event(events: list[TelemetryEvent]) -> TelemetryEvent | None:
    return next(
        (
            event
            for event in reversed(events)
            if event["status"] in {"ok", "warning", "critical", "error"}
        ),
        events[-1] if events else None,
    )
