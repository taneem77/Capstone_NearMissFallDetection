
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.live.event_detector import CandidateEventDetector


class TestCandidateEventDetector(unittest.TestCase):

    def setUp(self):
        self.detector = CandidateEventDetector(
            acceleration_threshold=3.0,
            gyroscope_threshold=100.0,
            consecutive_samples=5
        )

    def make_message(self, timestamp, acc_z=9.80665, gyro_z=0.0):
        return {
            "timestamp": timestamp,
            "acc_x": 0.0,
            "acc_y": 0.0,
            "acc_z": acc_z,
            "gyro_x": 0.0,
            "gyro_y": 0.0,
            "gyro_z": gyro_z,
            "grip": 120.0
        }

    def test_normal_motion_does_not_trigger(self):
        for i in range(10):
            result = self.detector.process(
                self.make_message(i * 0.01)
            )

            self.assertIsNone(result)

    def test_high_motion_triggers_candidate_event(self):
        result = None

        for i in range(5):
            result = self.detector.process(
                self.make_message(
                    i * 0.01,
                    acc_z=15.0
                )
            )

        self.assertIsNotNone(result)
        self.assertEqual(
            result["event_type"],
            "candidate_high_motion"
        )

    def test_event_is_not_repeated_during_same_motion(self):
        events = []

        for i in range(10):
            result = self.detector.process(
                self.make_message(
                    i * 0.01,
                    acc_z=15.0
                )
            )

            if result is not None:
                events.append(result)

        self.assertEqual(len(events), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)

