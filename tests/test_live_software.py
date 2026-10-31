
import csv
import sys
import tempfile
import unittest
from pathlib import Path

# Add the project root to Python's import path.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.live.wifi_logger import validate_message
from src.live.event_log import EventLogger


class TestSensorMessageValidation(unittest.TestCase):

    def setUp(self):
        """Create a valid sample sensor message for testing."""
        self.valid_message = {
            "timestamp": 1.0,
            "acc_x": 0.1,
            "acc_y": 0.2,
            "acc_z": 9.8,
            "gyro_x": 0.3,
            "gyro_y": 0.4,
            "gyro_z": 0.5,
            "grip": 120.0
        }

    def test_valid_message(self):
        """A valid sensor message should be accepted."""
        self.assertTrue(validate_message(self.valid_message))

    def test_missing_field(self):
        """A message with a missing field should raise ValueError."""
        message = self.valid_message.copy()
        del message["grip"]

        with self.assertRaises(ValueError):
            validate_message(message)

    def test_invalid_string_value(self):
        """A non-numeric sensor value should raise ValueError."""
        message = self.valid_message.copy()
        message["acc_x"] = "invalid"

        with self.assertRaises(ValueError):
            validate_message(message)

    def test_negative_timestamp(self):
        """A negative timestamp should raise ValueError."""
        message = self.valid_message.copy()
        message["timestamp"] = -1

        with self.assertRaises(ValueError):
            validate_message(message)

    def test_non_finite_value(self):
        """A NaN sensor value should raise ValueError."""
        message = self.valid_message.copy()
        message["acc_x"] = float("nan")

        with self.assertRaises(ValueError):
            validate_message(message)


class TestEventLogger(unittest.TestCase):

    def test_event_is_saved(self):
        """Check whether an event is correctly written to CSV."""
        with tempfile.TemporaryDirectory() as temp_dir:

            output = Path(temp_dir) / "events.csv"
            logger = EventLogger(output)

            logger.log_event(
                event_id=1,
                timestamp="2026-10-30T10:00:00+00:00",
                event_type="recovery_like_event",
                detection_score=0.87,
                source="test",
                duration_s=1.2
            )

            # Read the generated CSV.
            with output.open(
                "r",
                newline="",
                encoding="utf-8"
            ) as file:

                rows = list(csv.DictReader(file))

            self.assertEqual(len(rows), 1)
            self.assertEqual(
                rows[0]["event_type"],
                "recovery_like_event"
            )
            self.assertEqual(rows[0]["source"], "test")


if __name__ == "__main__":
    unittest.main(verbosity=2)
