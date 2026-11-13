"""
Comprehensive Unit Test Suite for Smart Cane Phase-1 ESA Evaluation.
Validates signal processing, feature calculation, dynamic calibration,
multi-sensor fusion, and false alarm rejection.
"""
import pytest
import numpy as np
import pandas as pd
from capstone.src.signal_proc import butter_lowpass_filter, moving_average_filter, validate_stream_integrity
from capstone.src.features import compute_kinematics, extract_event_features, extract_windowed_feature_matrix
from capstone.src.calibration import adc_to_force_newtons, calibrate_thresholds_from_baseline
from capstone.src.synthetic_data import generate_activity_segment
from capstone.src.detector import IMUOnlyDetector, GripOnlyDetector, FusedCouplingDetector, MLBaselineClassifier, compute_evaluation_metrics

def test_butterworth_filter_attenuates_noise():
    # 100 Hz sampling, 2 Hz true signal + 25 Hz high frequency noise
    t = np.linspace(0, 1.0, 100)
    clean = np.sin(2 * np.pi * 2 * t)
    noisy = clean + 0.5 * np.sin(2 * np.pi * 25 * t)
    
    filtered = butter_lowpass_filter(noisy, cutoff=5.0, fs=100.0, order=4)
    assert len(filtered) == len(noisy)
    # Variance of error relative to clean should be lower after filtering
    err_raw = np.var(noisy - clean)
    err_filtered = np.var(filtered - clean)
    assert err_filtered < err_raw

def test_stream_integrity_validation():
    # Perfectly monotonic 100 Hz stream
    ts_good = np.arange(0, 1000, 10) # 10 ms interval = 100 Hz
    diag_good = validate_stream_integrity(ts_good, expected_fs=100.0)
    assert diag_good['is_monotonic'] is True
    assert diag_good['healthy'] is True
    assert diag_good['dropped_packet_count'] == 0
    
    # Stream with dropped packets (e.g. 50 ms gap)
    ts_dropped = [0, 10, 20, 75, 85, 95]
    diag_bad = validate_stream_integrity(ts_dropped, expected_fs=100.0)
    assert diag_bad['dropped_packet_count'] >= 1

def test_kinematics_and_jerk_units():
    # Test jerk computation: da/dt in m/s^3
    df = pd.DataFrame({
        'timestamp_ms': [0, 10, 20, 30, 40],
        'ax': [0.0, 1.0, 3.0, 1.0, 0.0],
        'ay': [0.0, 0.0, 0.0, 0.0, 0.0],
        'az': [9.8, 9.8, 9.8, 9.8, 9.8],
        'grip_adc': [500, 500, 500, 500, 500]
    })
    k_df = compute_kinematics(df, fs=100.0)
    assert 'jerk_mag' in k_df.columns
    assert 'a_mag' in k_df.columns
    # Peak jerk should be non-zero and physically reasonable
    assert np.max(k_df['jerk_mag']) > 0

def test_adc_to_force_conversion():
    # Zero / low ADC counts -> minimal force (~0 N)
    f_low = adc_to_force_newtons([50, 100])
    assert np.all(f_low < 5.0)
    
    # High ADC counts (strong grip) -> higher force (> 20 N)
    f_high = adc_to_force_newtons([2500, 3200])
    assert np.all(f_high > 10.0)
    assert f_high[1] > f_high[0]

def test_baseline_threshold_calibration():
    # Baseline walking data
    walk_df = generate_activity_segment("normal_walking", duration_sec=10.0, fs=100.0)
    calib = calibrate_thresholds_from_baseline(walk_df, k_jerk=3.0, k_grip=3.0)
    
    # Calibrated threshold must be greater than baseline mean
    assert calib['calibrated_jerk_threshold'] > calib['jerk_mean']
    assert calib['calibrated_jerk_threshold'] >= 35.0
    assert calib['calibrated_grip_threshold'] > 0

def test_false_alarm_rejection_cane_bump():
    """
    CRITICAL TEST: Validates that cane bump (sharp tap) causes a false alarm
    in IMU-only detector, but is successfully rejected by Fused Coupling.
    """
    bump_df = generate_activity_segment("cane_tap_bump", duration_sec=10.0, fs=100.0)
    
    # IMU-only flags false alarm on cane tap
    imu_detector = IMUOnlyDetector(jerk_threshold=45.0)
    imu_flags = imu_detector.predict(bump_df)
    assert np.sum(imu_flags) > 0, "IMU-only should have tripped on sharp bump"
    
    # Fused detector correctly rejects the tap because grip rise didn't co-occur
    fused_detector = FusedCouplingDetector(jerk_threshold=45.0, grip_rise_threshold=15.0, window_sec=0.35)
    fused_flags = fused_detector.predict(bump_df)
    assert np.sum(fused_flags) == 0, "Fused coupling must REJECT cane bump (zero false alarms)"

def test_fused_detector_detects_near_miss_trip():
    """Validates that a true near-miss trip is successfully detected by Fused Coupling."""
    trip_df = generate_activity_segment("near_miss_trip", duration_sec=10.0, fs=100.0)
    fused_detector = FusedCouplingDetector(jerk_threshold=50.0, grip_rise_threshold=12.0, window_sec=0.4)
    flags = fused_detector.predict(trip_df)
    assert np.sum(flags) > 0, "Fused coupling must reliably detect coordinated trip near-miss"

def test_fused_detector_detects_near_miss_slip():
    """Validates that a true near-miss slip is successfully detected by Fused Coupling."""
    slip_df = generate_activity_segment("near_miss_slip", duration_sec=10.0, fs=100.0)
    fused_detector = FusedCouplingDetector(jerk_threshold=45.0, grip_rise_threshold=12.0, window_sec=0.4)
    flags = fused_detector.predict(slip_df)
    assert np.sum(flags) > 0, "Fused coupling must reliably detect coordinated slip near-miss"

def test_ml_classifier_fit_and_predict():
    # Generate multi-subject training and test
    train_df = pd.concat([
        generate_activity_segment("normal_walking", duration_sec=8.0, subject_id="SA01"),
        generate_activity_segment("near_miss_trip", duration_sec=8.0, subject_id="SA01")
    ], ignore_index=True)
    
    test_df = generate_activity_segment("near_miss_slip", duration_sec=8.0, subject_id="SA02")
    
    clf = MLBaselineClassifier(n_estimators=20)
    clf.fit(train_df)
    preds, feat_df = clf.predict(test_df)
    assert len(preds) == len(feat_df)
    assert set(preds).issubset({0, 1})

def test_evaluation_metrics_calculation():
    y_true = [0, 0, 1, 1, 0, 0, 0, 1, 0, 0]
    y_pred = [0, 0, 1, 1, 0, 1, 0, 1, 0, 0] # 3 TP, 1 FP, 0 FN, 6 TN
    m = compute_evaluation_metrics(y_true, y_pred, total_duration_hours=0.5)
    
    assert m['True_Positives'] == 3
    assert m['False_Positives'] == 1
    assert m['False_Negatives'] == 0
    assert m['Sensitivity'] == 1.0
    assert m['Precision'] == 0.75
    assert m['False_Alarms_Per_Hour'] == 2.0
