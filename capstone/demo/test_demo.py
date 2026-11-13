"""
Comprehensive Unit & Integration Test Suite for Smart Cane Demo.
Verifies all essential subsystems:
  1. Configuration integrity and explicit assumptions
  2. Dataset cataloging & coverage (32 subjects, 5,075 files)
  3. 59-feature extraction architecture (50 IMU + 9 Grip)
  4. Protocol trial generation & bounding box labeling
  5. 5-step signal processing pipeline data
  6. Real K-Fall stream loading with ground truth
  7. Three concurrent detectors & coincidence logic
  8. Personal baseline calibration (mu + 3*sigma)
  9. Research Questions (RQ1-RQ4) benchmark integrity
  10. Full Flask API endpoints verification
"""
import os
import sys
import unittest
import numpy as np

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from detector_engine import (
    load_config, get_available_subjects, build_dataset_catalog, get_curated_playlist,
    apply_butterworth_filter, compute_kinematic_jerk, compute_dynamic_grip_rise,
    extract_59_features, load_recording_stream, run_three_detectors,
    calibrate_subject_baseline, generate_protocol_trial, get_pipeline_step_data
)
from server import app

class TestSmartCaneDemo(unittest.TestCase):

    def setUp(self):
        self.config = load_config()
        self.client = app.test_client()

    def test_01_config_and_assumptions(self):
        self.assertEqual(self.config.get("seed"), 42)
        self.assertIn("units", self.config)
        self.assertAlmostEqual(self.config["units"]["accel_unit_multiplier"], 9.80665)
        self.assertAlmostEqual(self.config["units"]["grip_adc_to_newton"], 45.0 / 4095.0, places=4)
        self.assertEqual(self.config["window"]["length_sec"], 1.0)
        self.assertEqual(self.config["window"]["stride_sec"], 0.25)
        self.assertAlmostEqual(self.config["thresholds"]["jerk_threshold"], 55.0)
        self.assertAlmostEqual(self.config["thresholds"]["grip_rise_threshold"], 12.0)
        self.assertAlmostEqual(self.config["thresholds"]["coincidence_window_sec"], 0.35)

    def test_02_dataset_catalog(self):
        cat = build_dataset_catalog(force_rebuild=False)
        self.assertGreaterEqual(cat["total_subjects"], 30)
        self.assertGreater(cat["total_files"], 4000)
        self.assertEqual(cat["skipped_count"], 0)
        self.assertIn("Walking & Stepping", cat["activity_counts"])
        self.assertIn("Near-Miss: Trip", cat["activity_counts"])

    def test_03_feature_extraction_59(self):
        # 100 samples (1.0 second at 100 Hz)
        acc = np.random.normal(0, 1.0, (100, 3)); acc[:, 2] += 9.81
        gyro = np.random.normal(0, 5.0, (100, 3))
        grip = np.full(100, 5.0)
        grip[40:70] += 25.0 # Grip clench
        feats = extract_59_features(acc, gyro, grip)
        self.assertEqual(len(feats), 59, f"Expected 59 features, got {len(feats)}")
        self.assertIn("grip_delta_rise", feats)
        self.assertIn("temporal_coupling_gap", feats)
        self.assertIn("jerk_max", feats)
        self.assertIn("acc_mag_p2p", feats)

    def test_04_protocol_trial_generator(self):
        trial = generate_protocol_trial(activity="nearmiss", subject="S01", trial_num=1)
        self.assertEqual(trial["activity"], "nearmiss")
        self.assertEqual(trial["subject"], "S01")
        self.assertIsNotNone(trial["event_box"])
        self.assertTrue(trial["event_box"]["is_event"])
        self.assertAlmostEqual(trial["event_box"]["end_s"] - trial["event_box"]["start_s"], 0.8, places=2)

    def test_05_pipeline_steps(self):
        for s in [1, 2, 3, 4, 5]:
            step_data = get_pipeline_step_data(step=s, subject="SA06", task=30, trial=1)
            self.assertEqual(step_data["step"], s)
            if s == 5:
                self.assertEqual(step_data["total_feature_count"], 59)

    def test_06_real_kfall_loader(self):
        stream = load_recording_stream(subject="SA06", task=30, trial=1)
        self.assertEqual(stream["data_source"], "REAL")
        self.assertTrue(stream["is_fall"])
        self.assertIn("acc_mag", stream)
        self.assertIn("gyro_mag", stream)
        self.assertIn("jerk_mag", stream)
        self.assertIn("grip_n", stream)

    def test_07_three_detectors(self):
        stream = load_recording_stream(subject="SA06", task=30, trial=1)
        det = run_three_detectors(stream, jerk_th=55.0, grip_th=12.0, window_sec=0.35)
        self.assertIn("imu", det)
        self.assertIn("grip", det)
        self.assertIn("fused", det)
        self.assertGreaterEqual(det["fused"]["true_positives"], 1)

    def test_08_personal_calibration(self):
        calib = calibrate_subject_baseline(subject="SA06", k_sigma=3.0)
        self.assertIn("calibrated_jerk_th", calib)
        self.assertIn("calibrated_grip_th", calib)
        self.assertGreaterEqual(calib["calibrated_jerk_th"], 35.0)
        self.assertGreaterEqual(calib["calibrated_grip_th"], 8.0)

    def test_09_rq_results_cache(self):
        resp = self.client.get("/api/rq_results")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("rq1", data)
        self.assertIn("rq2", data)
        self.assertIn("rq3", data)
        self.assertIn("rq4", data)
        self.assertAlmostEqual(data["rq1"]["metrics"][1]["sensitivity"], 0.848, places=3)
        self.assertAlmostEqual(data["rq2"]["metrics"][1]["sensitivity"], 1.0, places=1)
        self.assertAlmostEqual(data["rq4"]["headline"][0]["sensitivity"], 0.879, places=3)

    def test_10_api_endpoints(self):
        routes = [
            "/api/dataset_coverage",
            "/api/catalog_cases?subject=SA06&category=ALL",
            "/api/curated_playlist",
            "/api/load_recording?subject=SA06&task=30&trial=1",
            "/api/record_trial?activity=nearmiss&subject=S01&trial=1",
            "/api/pipeline_step?step=1&subject=SA06&task=30&trial=1",
            "/api/pipeline_step?step=5&subject=SA06&task=30&trial=1",
            "/api/rq_results",
            "/api/evaluation",
            "/api/event_log",
            "/api/fallback_simulation?activity=near_miss_trip"
        ]
        for route in routes:
            resp = self.client.get(route)
            self.assertEqual(resp.status_code, 200, f"Route {route} failed with status {resp.status_code}")

if __name__ == "__main__":
    unittest.main()
