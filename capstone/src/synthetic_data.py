"""
Synthetic Data Generation Engine.
Simulates realistic cane kinematics (MPU6050) and handle grip dynamics (FSR 402).
Generates benchmark datasets for:
  - Normal walking
  - Near-miss trips (jerk + reflex grip rise ~120 ms apart)
  - Near-miss slips (lateral jerk + reflex grip rise)
  - Cane tap/bump (sharp jerk, NO grip rise -> false alarm rejection test)
  - Stair descent
Supports multi-subject generation for Leave-One-Subject-Out (LOSO) validation.
"""
import numpy as np
import pandas as pd
from .calibration import adc_to_force_newtons

def generate_activity_segment(
    activity_type="normal_walking",
    duration_sec=10.0,
    fs=100.0,
    subject_id="SA01",
    random_seed=42
):
    """
    Generates a single synthetic telemetry segment for a specified activity.
    """
    np.random.seed(random_seed)
    n_samples = int(duration_sec * fs)
    t_sec = np.linspace(0, duration_sec, n_samples, endpoint=False)
    t_ms = (t_sec * 1000.0).astype(int)
    
    # Base gravity vector (cane upright slightly tilted)
    # Cane coordinate frame: Z along cane shaft, X lateral, Y forward
    ax_base = np.zeros(n_samples)
    ay_base = np.ones(n_samples) * 1.5
    az_base = np.ones(n_samples) * 9.6
    
    gx = np.zeros(n_samples)
    gy = np.zeros(n_samples)
    gz = np.zeros(n_samples)
    
    grip_n = np.ones(n_samples) * 8.0 # baseline grip 8 Newtons
    labels = ["normal"] * n_samples
    
    # Normal periodic gait (1.0 Hz cadence)
    gait_freq = 1.0 + np.random.uniform(-0.1, 0.1)
    ax_gait = 0.8 * np.sin(2 * np.pi * gait_freq * t_sec)
    ay_gait = 1.8 * np.sin(2 * np.pi * gait_freq * t_sec + np.pi/4)
    az_gait = 1.2 * np.cos(2 * np.pi * 2 * gait_freq * t_sec) # ground contact impacts
    
    # Normal rhythmic grip pulsation during stance
    grip_gait = 2.0 * np.maximum(0, np.sin(2 * np.pi * gait_freq * t_sec))
    
    ax = ax_base + ax_gait + np.random.normal(0, 0.15, n_samples)
    ay = ay_base + ay_gait + np.random.normal(0, 0.15, n_samples)
    az = az_base + az_gait + np.random.normal(0, 0.20, n_samples)
    grip_n = grip_n + grip_gait + np.random.normal(0, 0.3, n_samples)
    
    # Inject specific activity anomalies
    if activity_type == "near_miss_trip":
        # Event occurs at 5.0 seconds
        ev_idx = int(5.0 * fs)
        # Sharp deceleration jerk spike in Y and Z (duration ~ 150 ms)
        pulse_len = int(0.15 * fs)
        pulse = np.hanning(pulse_len)
        ay[ev_idx:ev_idx+pulse_len] += 12.0 * pulse
        az[ev_idx:ev_idx+pulse_len] -= 8.0 * pulse
        gx[ev_idx:ev_idx+pulse_len] += 120.0 * pulse
        
        # Reflexive grip tightening peaks ~ 120 ms (12 samples) after jerk onset
        grip_delay = int(0.12 * fs)
        grip_len = int(0.6 * fs)
        grip_pulse = np.hanning(grip_len)
        g_start = ev_idx + grip_delay
        grip_n[g_start:g_start+grip_len] += 26.0 * grip_pulse
        
        # Mark label
        for i in range(ev_idx, min(n_samples, g_start + grip_len)):
            labels[i] = "near_miss_trip"
            
    elif activity_type == "near_miss_slip":
        # Event at 5.0 seconds
        ev_idx = int(5.0 * fs)
        pulse_len = int(0.18 * fs)
        pulse = np.hanning(pulse_len)
        # Lateral/backward acceleration
        ax[ev_idx:ev_idx+pulse_len] += 9.5 * pulse
        ay[ev_idx:ev_idx+pulse_len] -= 10.0 * pulse
        gy[ev_idx:ev_idx+pulse_len] += 140.0 * pulse
        
        # Reflex grip rise ~ 110 ms later
        grip_delay = int(0.11 * fs)
        grip_len = int(0.55 * fs)
        grip_pulse = np.hanning(grip_len)
        g_start = ev_idx + grip_delay
        grip_n[g_start:g_start+grip_len] += 22.0 * grip_pulse
        
        for i in range(ev_idx, min(n_samples, g_start + grip_len)):
            labels[i] = "near_miss_slip"
            
    elif activity_type == "cane_tap_bump":
        # Critical false alarm test: User knocks cane against a door frame or curb
        ev_idx = int(5.0 * fs)
        pulse_len = int(0.08 * fs) # very sharp impact
        pulse = np.hanning(pulse_len)
        ax[ev_idx:ev_idx+pulse_len] += 15.0 * pulse
        az[ev_idx:ev_idx+pulse_len] += 14.0 * pulse
        
        # KEY NOVELTY: NO reflex grip rise! User was just moving/tapping cane.
        # Grip actually remains steady or slightly drops
        grip_n[ev_idx:ev_idx+int(0.3*fs)] -= 1.0
        
        for i in range(ev_idx, min(n_samples, ev_idx + pulse_len)):
            labels[i] = "cane_bump"
            
    elif activity_type == "stairs_descent":
        # Repetitive heavier impacts (~2 Hz)
        stair_freq = 1.6
        ay += 3.5 * np.sin(2 * np.pi * stair_freq * t_sec)
        az += 4.0 * np.maximum(0, np.sin(2 * np.pi * stair_freq * t_sec))
        grip_n += 4.0 # sustained higher grip on stairs
        labels = ["stairs"] * n_samples

    # Convert grip Newtons back to simulated ESP32 12-bit ADC counts
    # Invert calibration model for realistic ADC counts
    # High force -> Lower resistance -> Higher voltage -> Higher ADC
    grip_adc = np.clip(grip_n * 55.0 + 400.0, 100.0, 4095.0).astype(int)

    df = pd.DataFrame({
        'timestamp_ms': t_ms,
        'ax': np.round(ax, 3),
        'ay': np.round(ay, 3),
        'az': np.round(az, 3),
        'gx': np.round(gx, 2),
        'gy': np.round(gy, 2),
        'gz': np.round(gz, 2),
        'grip_adc': grip_adc,
        'grip_n': np.round(grip_n, 2),
        'label': labels,
        'subject_id': subject_id
    })
    return df

def generate_multi_subject_benchmark(output_dir="capstone/data/sample"):
    """
    Generates a full evaluation corpus across 5 synthetic subjects (SA01-SA05)
    and writes canonical reference CSV files.
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    activities = [
        ("walking_baseline", "normal_walking", 15.0),
        ("near_miss_trip", "near_miss_trip", 10.0),
        ("near_miss_slip", "near_miss_slip", 10.0),
        ("cane_bump_false_alarm", "cane_tap_bump", 10.0),
        ("stairs_descent", "stairs_descent", 12.0)
    ]
    
    generated_files = []
    all_dfs = []
    
    for filename, act, dur in activities:
        df = generate_activity_segment(act, duration_sec=dur, fs=100.0, subject_id="SA01", random_seed=101)
        path = os.path.join(output_dir, f"{filename}.csv")
        df.to_csv(path, index=False)
        generated_files.append(path)
        all_dfs.append(df)
        
    # Multi-subject dataset for Leave-One-Subject-Out (LOSO) ML validation
    multi_dfs = []
    for s_idx, subj in enumerate(["SA01", "SA02", "SA03", "SA04", "SA05"]):
        for act in ["normal_walking", "near_miss_trip", "near_miss_slip", "cane_tap_bump"]:
            sub_df = generate_activity_segment(act, duration_sec=8.0, fs=100.0, subject_id=subj, random_seed=200 + s_idx * 10)
            multi_dfs.append(sub_df)
            
    full_corpus = pd.concat(multi_dfs, ignore_index=True)
    benchmark_path = os.path.join(output_dir, "benchmark_multi_subject.csv")
    full_corpus.to_csv(benchmark_path, index=False)
    generated_files.append(benchmark_path)
    
    # Generate event_log.csv for weekly trends
    log_rows = [
        {"timestamp": "2026-10-14 09:12:44", "event_type": "near_miss_trip", "confidence": 0.94, "peak_jerk": 68.4, "grip_rise": 24.1, "temporal_gap_ms": 118, "status": "Recovered"},
        {"timestamp": "2026-10-16 16:45:10", "event_type": "near_miss_slip", "confidence": 0.91, "peak_jerk": 59.2, "grip_rise": 21.8, "temporal_gap_ms": 125, "status": "Recovered"},
        {"timestamp": "2026-10-21 11:05:32", "event_type": "near_miss_trip", "confidence": 0.88, "peak_jerk": 62.1, "grip_rise": 19.5, "temporal_gap_ms": 132, "status": "Recovered"},
        {"timestamp": "2026-10-28 14:22:19", "event_type": "near_miss_trip", "confidence": 0.96, "peak_jerk": 74.8, "grip_rise": 28.3, "temporal_gap_ms": 112, "status": "Recovered"},
        {"timestamp": "2026-10-29 08:31:05", "event_type": "near_miss_slip", "confidence": 0.89, "peak_jerk": 56.4, "grip_rise": 20.2, "temporal_gap_ms": 120, "status": "Recovered"},
        {"timestamp": "2026-11-04 17:50:41", "event_type": "near_miss_trip", "confidence": 0.95, "peak_jerk": 71.3, "grip_rise": 25.6, "temporal_gap_ms": 115, "status": "Recovered"},
        {"timestamp": "2026-11-08 10:18:22", "event_type": "near_miss_trip", "confidence": 0.92, "peak_jerk": 65.0, "grip_rise": 23.0, "temporal_gap_ms": 122, "status": "Recovered"},
    ]
    log_df = pd.DataFrame(log_rows)
    log_path = os.path.join(output_dir, "event_log.csv")
    log_df.to_csv(log_path, index=False)
    generated_files.append(log_path)
    
    return generated_files
