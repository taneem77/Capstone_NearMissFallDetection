
import sys
import unittest
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.live.coupling import (
    calculate_signals,
    peak_time_lag,
    cross_correlation_lag
)


class TestCouplingAnalysis(unittest.TestCase):

    def setUp(self):
        self.fs = 100
        self.time = np.arange(0, 10, 1 / self.fs)

        motion = np.zeros(len(self.time))
        grip = np.zeros(len(self.time))

        # Motion peak at 4 seconds.
        motion[(self.time >= 3.9) & (self.time <= 4.1)] = 3.0

        # Grip response at 4.2 seconds.
        grip[(self.time >= 4.1) & (self.time <= 4.3)] = 2.0

        self.df = pd.DataFrame({
            "timestamp": self.time,
            "acc_x": motion,
            "acc_y": np.zeros(len(self.time)),
            "acc_z": np.full(len(self.time), 9.80665),
            "gyro_x": np.zeros(len(self.time)),
            "gyro_y": np.zeros(len(self.time)),
            "gyro_z": np.zeros(len(self.time)),
            "grip": grip
        })

        self.signals = calculate_signals(self.df)

    def test_signal_columns_created(self):
        self.assertIn("acc_magnitude", self.signals.columns)
        self.assertIn("gyro_magnitude", self.signals.columns)
        self.assertIn("acc_dynamic", self.signals.columns)
        self.assertIn("grip_change", self.signals.columns)

    def test_peak_lag_is_positive(self):
        result = peak_time_lag(self.signals)

        self.assertGreater(
            result["grip_minus_motion_lag_s"],
            0
        )

    def test_cross_correlation_returns_valid_result(self):
        result = cross_correlation_lag(self.signals)

        self.assertTrue(np.isfinite(result["correlation"]))
        self.assertTrue(np.isfinite(result["lag_s"]))

    def test_constant_signals_handled(self):
        constant_df = self.df.copy()
        constant_df["acc_x"] = 0.0
        constant_df["acc_y"] = 0.0
        constant_df["acc_z"] = 9.80665
        constant_df["grip"] = 120.0

        signals = calculate_signals(constant_df)
        result = cross_correlation_lag(signals)

        self.assertTrue(np.isnan(result["correlation"]))
        self.assertTrue(np.isnan(result["lag_s"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
