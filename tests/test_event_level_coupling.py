
import sys
import unittest
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.live.event_level_coupling import analyse_event


class TestEventLevelCoupling(unittest.TestCase):

    def setUp(self):
        fs = 100
        time = np.arange(0, 10, 1 / fs)

        motion = np.exp(-((time - 4.0) / 0.15) ** 2)
        grip = 0.5 * np.exp(-((time - 4.2) / 0.15) ** 2)

        rng = np.random.default_rng(42)

        self.recording = pd.DataFrame({
            "timestamp": time,
            "acc_x": motion + rng.normal(0, 0.02, len(time)),
            "acc_y": rng.normal(0, 0.02, len(time)),
            "acc_z": 9.80665 + rng.normal(0, 0.02, len(time)),
            "gyro_x": motion * 10 + rng.normal(0, 0.1, len(time)),
            "gyro_y": rng.normal(0, 0.1, len(time)),
            "gyro_z": rng.normal(0, 0.1, len(time)),
            "grip": 1.0 + grip + rng.normal(0, 0.01, len(time))
        })

        self.annotation = pd.Series({
            "recording_id": "demo_001",
            "event_id": 1,
            "event_type": "controlled_recovery_like",
            "event_start_s": 4.0,
            "event_end_s": 4.5
        })

    def test_event_duration(self):
        result = analyse_event(
            self.recording,
            self.annotation
        )

        self.assertAlmostEqual(
            result["event_duration_s"],
            0.5
        )

    def test_grip_peak_follows_motion_peak(self):
        result = analyse_event(
            self.recording,
            self.annotation
        )

        self.assertGreater(
            result["grip_minus_acceleration_peak_s"],
            0
        )

    def test_grip_onset_lag_is_finite(self):
        result = analyse_event(
            self.recording,
            self.annotation
        )

        self.assertTrue(
            np.isfinite(
                result["grip_minus_acceleration_onset_s"]
            )
        )

    def test_event_metadata_is_preserved(self):
        result = analyse_event(
            self.recording,
            self.annotation
        )

        self.assertEqual(result["recording_id"], "demo_001")
        self.assertEqual(result["event_id"], 1)
        self.assertEqual(
            result["event_type"],
            "controlled_recovery_like"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
