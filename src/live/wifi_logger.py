
"""
Live sensor data logger for the Smart Cane project.

Accepts JSON sensor messages and stores validated readings in CSV.
The input transport can later be connected to Wi-Fi, MQTT, HTTP or serial.

Expected fields:
timestamp, acc_x, acc_y, acc_z,
gyro_x, gyro_y, gyro_z, grip
"""

import argparse
import csv
import json
import math
from pathlib import Path


COLUMNS = [
    "timestamp",
    "acc_x", "acc_y", "acc_z",
    "gyro_x", "gyro_y", "gyro_z",
    "grip"
]


def validate_message(message):
    """Validate one incoming sensor message."""

    if not isinstance(message, dict):
        raise ValueError("Sensor message must be a JSON object.")

    missing = [key for key in COLUMNS if key not in message]

    if missing:
        raise ValueError(f"Missing fields: {missing}")

    validated = {}

    for key in COLUMNS:
        try:
            value = float(message[key])
        except (TypeError, ValueError):
            raise ValueError(f"Invalid numeric value for {key}")

        if not math.isfinite(value):
            raise ValueError(f"Non-finite value for {key}")

        validated[key] = value

    if validated["timestamp"] < 0:
        raise ValueError("Timestamp cannot be negative.")

    return validated


def save_readings(messages, output_path):
    """Validate and append sensor readings to a CSV file."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    file_exists = output_path.exists() and output_path.stat().st_size > 0
    saved = 0
    rejected = 0

    with output_path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)

        if not file_exists:
            writer.writeheader()

        for message in messages:
            try:
                row = validate_message(message)
                writer.writerow(row)
                saved += 1

            except ValueError as error:
                print(f"Rejected message: {error}")
                rejected += 1

    return saved, rejected


def read_json_lines(input_path):
    """Read JSON messages from a newline-delimited JSON file."""

    with open(input_path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                print(f"Invalid JSON at line {line_number}")


def main():
    parser = argparse.ArgumentParser(
        description="Smart Cane live sensor data logger"
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Input JSON Lines file containing sensor messages"
    )

    parser.add_argument(
        "--output",
        default="logs/live_sensor_data.csv",
        help="Output CSV file"
    )

    args = parser.parse_args()

    saved, rejected = save_readings(
        read_json_lines(args.input),
        args.output
    )

    print("\nSensor Logging Summary")
    print("----------------------")
    print(f"Successfully saved: {saved}")
    print(f"Rejected messages: {rejected}")
    print(f"Output file: {args.output}")


if __name__ == "__main__":
    main()
