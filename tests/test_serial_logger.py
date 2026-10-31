import csv
import tempfile
import unittest
from pathlib import Path

from src.live.serial_logger import process_serial_stream


class FakeSerial:
    """Simulates an ESP32 serial connection."""

    def __init__(self, messages):
        self.messages = iter(messages)

    def readline(self):
        return next(self.messages, b"")


class TestSerialLogger(unittest.TestCase):

    def test_valid_messages_are_saved(self):
        messages = [
            b'{"timestamp":1.0,"acc_x":0.1,"acc_y":0.2,"acc_z":9.7,"gyro_x":1,"gyro_y":2,"gyro_z":3,"grip":120}\n',
            b'{"timestamp":2.0,"acc_x":0.2,"acc_y":0.3,"acc_z":9.6,"gyro_x":2,"gyro_y":3,"gyro_z":4,"grip":125}\n'
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "serial_data.csv"

            fake_serial = FakeSerial(messages)

            result = process_serial_stream(
                fake_serial,
                output,
                max_lines=2
            )

            self.assertEqual(result["saved"], 2)
            self.assertEqual(result["rejected"], 0)

            with output.open(newline="") as file:
                rows = list(csv.DictReader(file))

            self.assertEqual(len(rows), 2)

    def test_invalid_message_is_rejected(self):
        messages = [
            b'not valid json\n',
            b'{"timestamp":1.0}\n'
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "serial_data.csv"

            fake_serial = FakeSerial(messages)

            result = process_serial_stream(
                fake_serial,
                output,
                max_lines=2
            )

            self.assertEqual(result["saved"], 0)
            self.assertEqual(result["rejected"], 2)

    def test_mixed_messages(self):
        messages = [
            b'{"timestamp":1.0,"acc_x":0.1,"acc_y":0.2,"acc_z":9.7,"gyro_x":1,"gyro_y":2,"gyro_z":3,"grip":120}\n',
            b'invalid message\n'
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "serial_data.csv"

            fake_serial = FakeSerial(messages)

            result = process_serial_stream(
                fake_serial,
                output,
                max_lines=2
            )

            self.assertEqual(result["saved"], 1)
            self.assertEqual(result["rejected"], 1)


if __name__ == "__main__":
    unittest.main()