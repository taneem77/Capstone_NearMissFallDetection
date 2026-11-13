"""
Core Detection Engine for Smart Cane.
Compares four detection paradigms:
  1. IMU-Only (Kinematic Jerk Threshold)
  2. Grip-Only (Kinetic Grip Rise Threshold)
  3. Fused Temporal Coupling Rule (Jerk + Grip within coincidence window ~120 ms)
  4. Lightweight ML Classifier (Random Forest / Decision Tree)
Computes False Alarms per hour, Sensitivity, Precision, and Latency.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score
from .features import compute_kinematics, extract_windowed_feature_matrix

class IMUOnlyDetector:
    """Baseline 1: Flags near-fall when cane jerk exceeds threshold."""
    def __init__(self, jerk_threshold=60.0):
        self.jerk_threshold = jerk_threshold
        
    def predict(self, df):
        processed = compute_kinematics(df)
        flags = (processed['jerk_mag'].values >= self.jerk_threshold).astype(int)
        return flags

class GripOnlyDetector:
    """Baseline 2: Flags near-fall when handle grip rise exceeds threshold."""
    def __init__(self, grip_rise_threshold=12.0):
        self.grip_rise_threshold = grip_rise_threshold
        
    def predict(self, df):
        processed = compute_kinematics(df)
        grip_col = 'grip_n' if 'grip_n' in processed else ('grip_adc' if 'grip_adc' in processed else None)
        if not grip_col:
            return np.zeros(len(df), dtype=int)
            
        grip = processed[grip_col].values
        # Baseline is estimated from sliding minimum or initial window
        baseline = pd.Series(grip).rolling(window=100, min_periods=1).min().values
        grip_rise = grip - baseline
        flags = (grip_rise >= self.grip_rise_threshold).astype(int)
        return flags

class FusedCouplingDetector:
    """
    Proposed Method: Dual-domain Temporal Coupling.
    Flags near-miss only when kinematic jerk spike AND reflex grip rise occur
    within a physiological coincidence window (nominal ~120 ms, window +/- 350 ms).
    Filters out cane taps, door bumps, and intentional handle squeezing.
    """
    def __init__(self, jerk_threshold=60.0, grip_rise_threshold=12.0, window_sec=0.35, fs=100.0):
        self.jerk_threshold = jerk_threshold
        self.grip_rise_threshold = grip_rise_threshold
        self.window_samples = int(window_sec * fs)
        self.fs = fs
        
    def predict(self, df):
        processed = compute_kinematics(df, fs=self.fs)
        n = len(processed)
        flags = np.zeros(n, dtype=int)
        
        jerk = processed['jerk_mag'].values
        grip_col = 'grip_n' if 'grip_n' in processed else ('grip_adc' if 'grip_adc' in processed else None)
        if not grip_col:
            return flags
            
        grip = processed[grip_col].values
        baseline = pd.Series(grip).rolling(window=int(self.fs), min_periods=1).min().values
        grip_rise = grip - baseline
        
        # Find candidate jerk peaks
        jerk_candidates = np.where(jerk >= self.jerk_threshold)[0]
        
        for j_idx in jerk_candidates:
            # Check coincidence window: reflex grip follows jerk (0 to +window_samples)
            w_start = max(0, j_idx - int(0.05 * self.fs)) # slight tolerance
            w_end = min(n, j_idx + self.window_samples)
            
            if np.any(grip_rise[w_start:w_end] >= self.grip_rise_threshold):
                # Co-occurrence verified
                flags[j_idx:min(n, j_idx + int(0.2 * self.fs))] = 1
                
        return flags

class MLBaselineClassifier:
    """Machine Learning benchmark baseline (Random Forest)."""
    def __init__(self, n_estimators=50, max_depth=6, random_state=42):
        self.clf = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=random_state)
        self.feature_cols = [
            'jerk_mean', 'jerk_std', 'jerk_max', 'jerk_rms', 'jerk_p90',
            'a_mag_mean', 'a_mag_max', 'a_mag_std',
            'grip_mean', 'grip_max', 'grip_std', 'grip_rise', 'temporal_gap_ms'
        ]
        
    def fit(self, train_df, fs=100.0):
        feat_df = extract_windowed_feature_matrix(train_df, fs=fs)
        X = feat_df[self.feature_cols].fillna(0.0)
        y = (feat_df['label'].str.contains('near_miss')).astype(int)
        self.clf.fit(X, y)
        return self
        
    def predict(self, test_df, fs=100.0):
        feat_df = extract_windowed_feature_matrix(test_df, fs=fs)
        X = feat_df[self.feature_cols].fillna(0.0)
        preds = self.clf.predict(X)
        return preds, feat_df

def compute_evaluation_metrics(y_true, y_pred, total_duration_hours=1.0):
    """
    Computes standard clinical & engineering metrics:
      - Sensitivity / Recall
      - Precision
      - Specificity
      - False Alarms per hour (Primary Metric)
      - F1 Score
    """
    y_t = np.array(y_true).astype(int)
    y_p = np.array(y_pred).astype(int)
    
    # Binary confusion matrix
    tn, fp, fn, tp = confusion_matrix(y_t, y_p, labels=[0, 1]).ravel()
    
    sens = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 1.0
    prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    f1 = float(2 * prec * sens / (prec + sens)) if (prec + sens) > 0 else 0.0
    
    # False alarms per hour
    fa_per_hour = float(fp / max(0.001, total_duration_hours))
    
    return {
        'True_Positives': int(tp),
        'False_Positives': int(fp),
        'True_Negatives': int(tn),
        'False_Negatives': int(fn),
        'Sensitivity': round(sens, 4),
        'Specificity': round(spec, 4),
        'Precision': round(prec, 4),
        'F1_Score': round(f1, 4),
        'False_Alarms_Per_Hour': round(fa_per_hour, 2)
    }

def benchmark_all_detectors(test_df, fs=100.0, jerk_th=60.0, grip_th=12.0):
    """
    Runs comprehensive benchmark across IMU-Only, Grip-Only, Fused Coupling, and ML.
    """
    duration_hours = len(test_df) / (fs * 3600.0)
    y_true = (test_df['label'].astype(str).str.contains('near_miss')).astype(int).values
    
    # 1. IMU Only
    imu_det = IMUOnlyDetector(jerk_threshold=jerk_th)
    y_imu = imu_det.predict(test_df)
    m_imu = compute_evaluation_metrics(y_true, y_imu, total_duration_hours=duration_hours)
    
    # 2. Grip Only
    grip_det = GripOnlyDetector(grip_rise_threshold=grip_th)
    y_grip = grip_det.predict(test_df)
    m_grip = compute_evaluation_metrics(y_true, y_grip, total_duration_hours=duration_hours)
    
    # 3. Fused Coupling
    fused_det = FusedCouplingDetector(jerk_threshold=jerk_th, grip_rise_threshold=grip_th, fs=fs)
    y_fused = fused_det.predict(test_df)
    m_fused = compute_evaluation_metrics(y_true, y_fused, total_duration_hours=duration_hours)
    
    results = {
        'IMU_Only': m_imu,
        'Grip_Only': m_grip,
        'Fused_Temporal_Coupling': m_fused
    }
    return results
