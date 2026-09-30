import argparse
import json
import re

import serial

MSE_PATTERN = re.compile(r"\bMSE:\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+))")


def parse_line(line: str) -> dict[str, str | float | None] | None:
    message = line.strip()
    if not message:
        return None

    if "[CRITICAL ANOMALY]" in message:
        status = "critical"
    elif "[WARNING]" in message:
        status = "warning"
    elif "[OK]" in message:
        status = "ok"
    elif "[ERR]" in message:
        status = "error"
    else:
        status = "system"

    match = MSE_PATTERN.search(message)
    return {
        "status": status,
        "mse": float(match.group(1)) if match else None,
        "message": message,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Read firmware UART telemetry.")
    parser.add_argument("port", help="Serial port, e.g. COM5 or /dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=115200)
    args = parser.parse_args()

    try:
        with serial.Serial(args.port, args.baud, timeout=1) as uart:
            print(f"Listening on {args.port} at {args.baud} baud")
            while True:
                raw_line = uart.readline()
                if not raw_line:
                    continue

                line = raw_line.decode("utf-8", errors="replace")
                event = parse_line(line)
                if event is not None:
                    print(json.dumps(event))
    except KeyboardInterrupt:
        print("\nUART bridge stopped.")
    except serial.SerialException as error:
        parser.error(f"Could not open/read serial port: {error}")


if __name__ == "__main__":
    main()