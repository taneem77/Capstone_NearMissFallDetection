"""
Python Serial Logger for Smart Cane Sensor Data

Reads newline-delimited JSON messages from an ESP32 over USB serial,
validates the sensor fields, and appends valid readings to a CSV file.

Expected JSON format:
{
    "timestamp": 1.25,
    "acc_x": 0.1,
    "acc_y": 0.2,
    "acc_z": 9.7,
    "gyro_x": 1.0,
    "gyro_y": 2.0,
    "gyro_z": 3.0,
    "grip": 120.0
}
"""

import argparse
import csv
import json
from pathlib import Path

import serial

try:
    from .wifi_logger import COLUMNS, validate_message
except ImportError:
    from wifi_logger import COLUMNS, validate_message


def process_serial_stream(
    serial_connection,
    output_path,
    max_lines=None
):
    """
    Read sensor messages from an already-open serial connection.

    Args:
        serial_connection: Open serial connection with a readline() method.
        output_path: CSV file where valid readings will be stored.
        max_lines: Optional maximum number of lines to read.

    Returns:
        Dictionary containing processed, saved, and rejected counts.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    processed = 0
    saved = 0
    rejected = 0

    file_exists = output_path.exists() and output_path.stat().st_size > 0

    with output_path.open("a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=COLUMNS)

        if not file_exists:
            writer.writeheader()

        while max_lines is None or processed < max_lines:
            raw_line = serial_connection.readline()

            # A blank line can occur when the serial read times out.
            if not raw_line:
                if max_lines is not None:
                    processed += 1
                continue

            processed += 1

            try:
                # PySerial normally returns bytes.
                if isinstance(raw_line, bytes):
                    raw_line = raw_line.decode("utf-8").strip()
                else:
                    raw_line = str(raw_line).strip()

                if not raw_line:
                    rejected += 1
                    continue

                message = json.loads(raw_line)
                validated_message = validate_message(message)

                writer.writerow(validated_message)
                csv_file.flush()
                saved += 1

            except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError):
                rejected += 1

    return {
        "processed": processed,
        "saved": saved,
        "rejected": rejected
    }


def main():
    parser = argparse.ArgumentParser(
        description="Read Smart Cane sensor data from an ESP32 serial port."
    )

    parser.add_argument(
        "--port",
        required=True,
        help="Serial port, for example COM3 or COM4"
    )

    parser.add_argument(
        "--baudrate",
        type=int,
        default=115200,
        help="Serial baud rate (default: 115200)"
    )

    parser.add_argument(
        "--output",
        default="logs/serial_sensor_data.csv",
        help="Output CSV file"
    )

    parser.add_argument(
        "--max-lines",
        type=int,
        default=None,
        help="Optional maximum number of lines to read"
    )

    args = parser.parse_args()

    try:
        print(f"Connecting to {args.port} at {args.baudrate} baud...")

        with serial.Serial(
            port=args.port,
            baudrate=args.baudrate,
            timeout=1
        ) as serial_connection:

            print("Serial connection established.")
            print("Logging sensor readings. Press Ctrl+C to stop.")

            results = process_serial_stream(
                serial_connection=serial_connection,
                output_path=args.output,
                max_lines=args.max_lines
            )

            print("\nSerial logging summary:")
            print(f"Lines processed: {results['processed']}")
            print(f"Readings saved:  {results['saved']}")
            print(f"Lines rejected:  {results['rejected']}")
            print(f"Output file:     {args.output}")

    except serial.SerialException as error:
        print(f"Serial connection error: {error}")
        print("Check that the ESP32 is connected and the correct COM port is selected.")

    except KeyboardInterrupt:
        print("\nSerial logging stopped by user.")


if __name__ == "__main__":
    main()