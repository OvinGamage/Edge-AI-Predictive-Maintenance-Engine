import sys
import unittest
from datetime import datetime
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dashboard"))
from telemetry import (
    latest_health_event,
    parse_telemetry_event,
    retain_recent_events,
)


class DashboardTelemetryTests(unittest.TestCase):
    def test_converts_uart_line_to_dashboard_event(self):
        received_at = datetime(2026, 1, 2, 3, 4, 5)
        event = parse_telemetry_event("[WARNING] MSE: 0.125 | Action: Inspect", received_at)
        self.assertEqual(
            event,
            {
                "received_at": received_at,
                "status": "warning",
                "mse": 0.125,
                "message": "[WARNING] MSE: 0.125 | Action: Inspect",
            },
        )
        self.assertIsNone(parse_telemetry_event(""))

    def test_retains_only_newest_events(self):
        events = [{"status": str(index)} for index in range(4)]
        self.assertEqual(retain_recent_events(events, limit=2), events[-2:])
        self.assertEqual(retain_recent_events(events, limit=0), [])
        with self.assertRaises(ValueError):
            retain_recent_events(events, limit=-1)

    def test_latest_health_skips_system_updates(self):
        system = {"status": "system"}
        warning = {"status": "warning"}
        latest_system = {"status": "system", "message": "still connected"}
        self.assertIs(latest_health_event([system, warning, latest_system]), warning)
        self.assertIs(latest_health_event([system]), system)
        self.assertIsNone(latest_health_event([]))


if __name__ == "__main__":
    unittest.main()
