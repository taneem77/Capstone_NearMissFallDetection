"""
Feature Extraction for Smart Cane Kinematics & Grip Dynamics.
Extracts jerk derivatives (m/s^3), grip force metrics (N), temporal coupling latency,
and sliding window statistics for baseline vs ML comparison.
"""
import numpy as np
import pandas as pd
from scipy.stats import skew, kurtosis

def compute_kinematics(df, fs=100.0, apply_filter=True):
    """
    Computes acceleration magnitude, angular velocity magnitude, and jerk vectors.
    Strict physical units:
      - Acceleration: m/s^2
      - Jerk: m/s^3
      - Angular velocity: deg/s or rad/s
    """
    res = df.copy()
    
    # Ensure standard column names
    col_map = {
        'timestamp': 'timestamp_ms',
        'acc_x': 'ax', 'acc_y': 'ay', 'acc_z': 'az',
        'gyro_x': 'gx', 'gyro_y': 'gy', 'gyro_z': 'gz',
        'grip': 'grip_adc'
    }
    for old, new in col_map.items():
        if old in res.columns and new not in res.columns:
            res[new] = res[old]
            
    # Time coordinates in seconds
    if 'timestamp_ms' in res.columns:
        t_sec = res['timestamp_ms'].values.astype(float) / 1000.0
        # If timestamps are identical or degenerate, fall back to uniform spacing
        if len(t_sec) > 1 and np.all(np.diff(t_sec) > 0):
            time_coord = t_sec
        else:
            time_coord = 1.0 / fs
    else:
        time_coord = 1.0 / fs
        
    # Acceleration magnitude
    ax = res['ax'].values if 'ax' in res.columns else np.zeros(len(res))
    ay = res['ay'].values if 'ay' in res.columns else np.zeros(len(res))
    az = res['az'].values if 'az' in res.columns else np.zeros(len(res))
    
    res['a_mag'] = np.sqrt(ax**2 + ay**2 + az**2)
    res['a_dyn'] = np.abs(res['a_mag'] - 9.80665)
    
    # Jerk components (da/dt in m/s^3)
    jx = np.gradient(ax, time_coord)
    jy = np.gradient(ay, time_coord)
    jz = np.gradient(az, time_coord)
    
    res['jx'] = jx
    res['jy'] = jy
    res['jz'] = jz
    res['jerk_mag'] = np.sqrt(jx**2 + jy**2 + jz**2)
    
    # Angular velocity magnitude
    if all(k in res.columns for k in ['gx', 'gy', 'gz']):
        res['omega_mag'] = np.sqrt(res['gx']**2 + res['gy']**2 + res['gz']**2)
    else:
        res['omega_mag'] = np.zeros(len(res))
        
    # Grip force derivative (dF/dt or dADC/dt)
    grip_col = 'grip_n' if 'grip_n' in res.columns else ('grip_adc' if 'grip_adc' in res.columns else None)
    if grip_col:
        res['grip_derivative'] = np.gradient(res[grip_col].values, time_coord)
    else:
        res['grip_derivative'] = np.zeros(len(res))
        
    return res

def extract_event_features(window_df, fs=100.0):
    """
    Extracts summary physical features from a candidate event window.
    
    Returns:
        dict: Feature dictionary containing peak jerk, peak grip, rise time,
              decay time, and temporal coupling latency gap (ms).
    """
    df = compute_kinematics(window_df, fs=fs)
    
    peak_jerk = float(np.max(df['jerk_mag'])) if 'jerk_mag' in df else 0.0
    jerk_idx = int(np.argmax(df['jerk_mag'])) if 'jerk_mag' in df else 0
    
    grip_col = 'grip_n' if 'grip_n' in df else ('grip_adc' if 'grip_adc' in df else None)
    if grip_col:
        grip_vals = df[grip_col].values
        baseline_grip = float(np.percentile(grip_vals[:max(5, len(grip_vals)//5)], 20))
        peak_grip = float(np.max(grip_vals))
        grip_rise = max(0.0, peak_grip - baseline_grip)
        grip_idx = int(np.argmax(grip_vals))
        
        # Temporal gap between jerk peak and grip peak in milliseconds
        if 'timestamp_ms' in df.columns:
            t_jerk = df['timestamp_ms'].iloc[jerk_idx]
            t_grip = df['timestamp_ms'].iloc[grip_idx]
            temporal_gap_ms = float(t_grip - t_jerk)
        else:
            temporal_gap_ms = float((grip_idx - jerk_idx) * (1000.0 / fs))
    else:
        peak_grip = 0.0
        grip_rise = 0.0
        temporal_gap_ms = 9999.0
        
    return {
        'peak_jerk_m_s3': round(peak_jerk, 2),
        'peak_grip': round(peak_grip, 2),
        'grip_rise': round(grip_rise, 2),
        'temporal_gap_ms': round(temporal_gap_ms, 1),
        'peak_accel_m_s2': round(float(np.max(df['a_mag'])), 2) if 'a_mag' in df else 0.0,
        'peak_omega_deg_s': round(float(np.max(df['omega_mag'])), 2) if 'omega_mag' in df else 0.0
    }

def extract_windowed_feature_matrix(df, window_size_samples=50, step_samples=25, fs=100.0):
    """
    Slices continuous signal into overlapping sliding windows and extracts comprehensive
    feature vectors suitable for ML classification (e.g. Random Forest baseline).
    """
    processed = compute_kinematics(df, fs=fs)
    rows = []
    
    n_samples = len(processed)
    for start in range(0, n_samples - window_size_samples + 1, step_samples):
        end = start + window_size_samples
        w = processed.iloc[start:end]
        
        jerk = w['jerk_mag'].values
        a_mag = w['a_mag'].values
        grip = w['grip_n'].values if 'grip_n' in w else (w['grip_adc'].values if 'grip_adc' in w else np.zeros(len(w)))
        
        row = {
            'window_start_idx': start,
            'window_end_idx': end,
            'jerk_mean': float(np.mean(jerk)),
            'jerk_std': float(np.std(jerk)),
            'jerk_max': float(np.max(jerk)),
            'jerk_rms': float(np.sqrt(np.mean(jerk**2))),
            'jerk_p90': float(np.percentile(jerk, 90)),
            'a_mag_mean': float(np.mean(a_mag)),
            'a_mag_max': float(np.max(a_mag)),
            'a_mag_std': float(np.std(a_mag)),
            'grip_mean': float(np.mean(grip)),
            'grip_max': float(np.max(grip)),
            'grip_std': float(np.std(grip)),
            'grip_rise': float(np.max(grip) - np.min(grip)),
            'temporal_gap_ms': float((np.argmax(grip) - np.argmax(jerk)) * (1000.0 / fs))
        }
        
        # Inherit label if present
        if 'label' in w.columns:
            # Mode label in window
            labels = w['label'].mode()
            row['label'] = labels.iloc[0] if len(labels) > 0 else 'normal'
            
        if 'subject_id' in w.columns:
            row['subject_id'] = w['subject_id'].iloc[0]
            
        rows.append(row)
        
    return pd.DataFrame(rows)
