import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dashboard"))
from uart_bridge import parse_line


class UartParsingTests(unittest.TestCase):
    def test_parses_firmware_status_and_mse(self):
        cases = {
            "[OK] MSE: 0.00123 | Status: Normal": ("ok", 0.00123),
            "[WARNING] MSE: .25 | Action: Inspection Required": ("warning", 0.25),
            "[CRITICAL ANOMALY] MSE: 1 | Action: Emergency Shutdown Recommended": (
                "critical",
                1.0,
            ),
            "[ERR] Inference execution failed!": ("error", None),
            "[SYS] Model Runner initialized successfully.": ("system", None),
        }
        for line, expected in cases.items():
            with self.subTest(line=line):
                event = parse_line(line)
                self.assertEqual((event["status"], event["mse"]), expected)
                self.assertEqual(event["message"], line)

    def test_ignores_blank_lines_and_preserves_signed_decimal(self):
        self.assertIsNone(parse_line(" \r\n"))
        self.assertEqual(parse_line("[OK] MSE: -0.5")["mse"], -0.5)


if __name__ == "__main__":
    unittest.main()
