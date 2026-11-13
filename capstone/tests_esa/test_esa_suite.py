"""
Dedicated Unit Test Suite for ESA Deliverables (capstone/tests_esa/).
Tests new data loaders, simulated benchmark generators, dynamic calibration,
and LOSO cross-validation without altering existing repository tests.
"""
import os
import pytest
import numpy as np
import pandas as pd

from capstone.data_esa.loader import load_cane_dataset
from capstone.data_esa.simulated_generator import generate_simulated_trial, generate_all_esa_simulated_corpora
from capstone.hardware_esa.serial_logger_esa import parse_csv_telemetry_line, ESASerialLogger
from capstone.src.detector import FusedCouplingDetector, IMUOnlyDetector
from capstone.src.calibration import calibrate_thresholds_from_baseline
from capstone.esa.extended_analysis import run_loso_cross_validation

def test_loader_simulated_metadata():
    bench_dir = "capstone/data_esa"
    bench_file = os.path.join(bench_dir, "simulated_loso_benchmark.csv")
    if not os.path.exists(bench_file):
        generate_all_esa_simulated_corpora(bench_dir)
        
    df, meta = load_cane_dataset(bench_file)
    assert meta['dataset_type'] == "SIMULATED"
    assert len(df) > 0
    assert 'time_ms' in df.columns

def test_loader_schema_and_columns():
    bench_file = "capstone/data_esa/simulated_loso_benchmark.csv"
    df, _ = load_cane_dataset(bench_file)
    expected_cols = ['time_ms', 'ax', 'ay', 'az', 'gx', 'gy', 'gz', 'grip_adc']
    for col in expected_cols:
        assert col in df.columns

def test_loader_monotonic_timestamps():
    bench_file = "capstone/data_esa/simulated_loso_benchmark.csv"
    df, meta = load_cane_dataset(bench_file)
    # Check monotonicity within first trial
    t_first_trial = df['time_ms'].iloc[:800].values
    assert np.all(np.diff(t_first_trial) > 0)

def test_simulated_generator_seed_reproducibility():
    df1 = generate_simulated_trial(activity="near_miss_trip", seed=42)
    df2 = generate_simulated_trial(activity="near_miss_trip", seed=42)
    pd.testing.assert_frame_equal(df1, df2)

def test_simulated_trip_kinematics():
    df = generate_simulated_trial(activity="near_miss_trip", duration_sec=8.0, fs=100.0)
    # Stumble at mid-trial (index 400)
    stumble_window = df[df['label'] == 'near_miss_trip']
    assert len(stumble_window) > 0
    # Peak acceleration magnitude should spike during trip
    a_mag = np.sqrt(stumble_window['ax']**2 + stumble_window['ay']**2 + stumble_window['az']**2)
    assert np.max(a_mag) > 15.0
    # Reflex grip clench should spike above resting baseline (>1200 counts)
    assert np.max(stumble_window['grip_adc']) > 1500

def test_cane_bump_tap_properties():
    df = generate_simulated_trial(activity="cane_tap_bump", duration_sec=8.0, fs=100.0)
    bump_window = df[df['label'] == 'cane_bump']
    assert len(bump_window) > 0
    # Sharp impact shock
    a_mag = np.sqrt(bump_window['ax']**2 + bump_window['ay']**2 + bump_window['az']**2)
    assert np.max(a_mag) > 16.0
    # Crucial property: grip does NOT experience reflex clench
    assert np.max(bump_window['grip_adc']) < 1000

def test_fused_coupling_rejection_of_cane_bump():
    bump_df = generate_simulated_trial(activity="cane_tap_bump", duration_sec=8.0, fs=100.0)
    # IMU-only flags false alarm
    imu_det = IMUOnlyDetector(jerk_threshold=45.0)
    y_imu = imu_det.predict(bump_df)
    assert np.sum(y_imu) > 0, "IMU-only should false alarm on sharp cane tap"

    # Fused detector rejects it
    fused_det = FusedCouplingDetector(jerk_threshold=45.0, grip_rise_threshold=300.0, window_sec=0.35, fs=100.0)
    y_fused = fused_det.predict(bump_df)
    assert np.sum(y_fused) == 0, "Fused coupling must REJECT cane bump (zero false alarms)"

def test_csv_line_parser():
    valid_csv = "12450,0.12,1.45,9.78,0.2,-0.1,0.5,1420"
    parsed = parse_csv_telemetry_line(valid_csv)
    assert parsed is not None
    assert parsed['time_ms'] == 12450
    assert parsed['az'] == 9.78
    assert parsed['grip_adc'] == 1420

    # Header or malformed line should safely return None
    assert parse_csv_telemetry_line("time_ms,ax,ay,az,gx,gy,gz,grip_adc") is None
    assert parse_csv_telemetry_line("malformed,line") is None

def test_esa_serial_logger_recording(tmp_path):
    logger = ESASerialLogger(output_dir=str(tmp_path))
    logger.start_recording(volunteer_id="VOL_TEST", floor="Carpet", footwear="Slippers", is_simulated=True)
    for i in range(10):
        logger.add_sample({
            'time_ms': 1000 + i*10,
            'ax': 0.1, 'ay': 1.2, 'az': 9.8,
            'gx': 0.0, 'gy': 0.0, 'gz': 0.0,
            'grip_adc': 500
        })
    saved_path = logger.save_to_csv()
    assert os.path.exists(saved_path)
    
    # Read back through loader
    loaded_df, meta = load_cane_dataset(saved_path)
    assert len(loaded_df) == 10
    assert meta['floor_type'] == "Carpet"

def test_loso_cross_validation_execution():
    # Mini corpus across 2 subjects to test LOSO pipeline integrity
    s1 = generate_simulated_trial("normal_walking", duration_sec=4.0, subject_id="S01")
    s2 = generate_simulated_trial("near_miss_trip", duration_sec=4.0, subject_id="S02")
    corpus = pd.concat([s1, s2], ignore_index=True)
    
    loso_df = run_loso_cross_validation(corpus, fs=100.0)
    assert len(loso_df) == 2
    assert 'fused_fa_per_hr' in loso_df.columns
    assert not loso_df['calibrated_jerk_th'].isna().any()
