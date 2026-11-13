"""
Multi-Subject Simulated Telemetry Generator (ESA Scope).
Produces benchmark datasets strictly stamped with `# DATASET_TYPE: SIMULATED` headers.
Simulates realistic cane gait dynamics across multiple virtual subjects (S01 to S05)
for testing and leave-one-subject-out (LOSO) validation before physical hardware trials.
"""
import os
import json
import numpy as np
import pandas as pd

def generate_simulated_trial(
    activity="normal_walking",
    duration_sec=10.0,
    fs=100.0,
    subject_id="S01",
    seed=42
):
    """
    Generates a single trial of simulated cane telemetry with ground truth annotations.
    """
    np.random.seed(seed)
    n = int(duration_sec * fs)
    t_sec = np.linspace(0, duration_sec, n, endpoint=False)
    t_ms = (t_sec * 1000.0).astype(int)

    # Base upright cane gravity (Z along shaft)
    ax = np.zeros(n)
    ay = np.ones(n) * 1.5 # forward tilt
    az = np.ones(n) * 9.6 # gravity component
    gx = np.zeros(n)
    gy = np.zeros(n)
    gz = np.zeros(n)
    grip_adc = np.ones(n) * 750 # baseline relaxed resting grip

    labels = ["normal"] * n

    # Periodic gait (1.0 Hz cadence with subject variability)
    cadence = 1.0 + np.random.uniform(-0.15, 0.15)
    stride_phase = 2 * np.pi * cadence * t_sec
    ax += 0.7 * np.sin(stride_phase)
    ay += 1.4 * np.cos(stride_phase)
    az += 1.1 * np.cos(2 * stride_phase) # heel contact shock
    grip_adc += 120.0 * np.maximum(0, np.sin(stride_phase)) # rhythmic stance palm pressure

    # Add Gaussian sensor noise
    ax += np.random.normal(0, 0.12, n)
    ay += np.random.normal(0, 0.12, n)
    az += np.random.normal(0, 0.18, n)
    gx += np.random.normal(0, 1.2, n)
    gy += np.random.normal(0, 1.2, n)
    gz += np.random.normal(0, 1.2, n)
    grip_adc += np.random.normal(0, 20.0, n)

    # Inject specific activities at mid-trial
    mid_idx = int(duration_sec * 0.5 * fs)

    if activity == "near_miss_trip":
        # Deceleration jerk spike (Y & Z axes)
        pulse_len = int(0.14 * fs) # 140 ms pulse
        window = np.hanning(pulse_len)
        ay[mid_idx:mid_idx + pulse_len] += 13.0 * window
        az[mid_idx:mid_idx + pulse_len] -= 8.5 * window
        gx[mid_idx:mid_idx + pulse_len] += 110.0 * window

        # Biomechanical grasp reflex peaks ~120 ms after jerk onset
        reflex_delay = int(0.12 * fs) # 12 samples = 120 ms
        clench_len = int(0.55 * fs)   # 550 ms duration
        clench_window = np.hanning(clench_len)
        c_start = mid_idx + reflex_delay
        grip_adc[c_start:c_start + clench_len] += 1650.0 * clench_window

        for i in range(mid_idx, min(n, c_start + clench_len)):
            labels[i] = "near_miss_trip"

    elif activity == "near_miss_slip":
        pulse_len = int(0.16 * fs)
        window = np.hanning(pulse_len)
        ax[mid_idx:mid_idx + pulse_len] += 10.0 * window
        ay[mid_idx:mid_idx + pulse_len] -= 11.5 * window
        gy[mid_idx:mid_idx + pulse_len] += 130.0 * window

        # Grasp reflex ~110 ms later
        reflex_delay = int(0.11 * fs)
        clench_len = int(0.50 * fs)
        clench_window = np.hanning(clench_len)
        c_start = mid_idx + reflex_delay
        grip_adc[c_start:c_start + clench_len] += 1400.0 * clench_window

        for i in range(mid_idx, min(n, c_start + clench_len)):
            labels[i] = "near_miss_slip"

    elif activity == "cane_tap_bump":
        # Sharp rigid impact on door/stair
        pulse_len = int(0.08 * fs) # very sharp 80 ms impact
        window = np.hanning(pulse_len)
        ax[mid_idx:mid_idx + pulse_len] += 16.0 * window
        az[mid_idx:mid_idx + pulse_len] += 15.0 * window

        # NO grasp reflex! User was simply tapping cane; grip remains flat
        grip_adc[mid_idx:mid_idx + int(0.2 * fs)] -= 40.0

        for i in range(mid_idx, mid_idx + pulse_len):
            labels[i] = "cane_bump"

    elif activity == "stairs_descent":
        stair_cadence = 1.6
        ay += 3.2 * np.sin(2 * np.pi * stair_cadence * t_sec)
        az += 3.8 * np.maximum(0, np.sin(2 * np.pi * stair_cadence * t_sec))
        grip_adc += 300.0 # higher sustained grip
        labels = ["stairs"] * n

    df = pd.DataFrame({
        'time_ms': t_ms,
        'ax': np.round(ax, 3),
        'ay': np.round(ay, 3),
        'az': np.round(az, 3),
        'gx': np.round(gx, 2),
        'gy': np.round(gy, 2),
        'gz': np.round(gz, 2),
        'grip_adc': np.clip(grip_adc, 100, 4095).astype(int),
        'label': labels,
        'subject_id': subject_id
    })
    return df

def generate_all_esa_simulated_corpora(output_dir="capstone/data_esa"):
    """
    Writes simulated benchmark datasets to disk with explicit metadata headers.
    """
    os.makedirs(output_dir, exist_ok=True)
    generated = []

    # 1. Multi-Subject LOSO Corpus (S01 to S05)
    subjects = ["S01", "S02", "S03", "S04", "S05"]
    activities = ["normal_walking", "near_miss_trip", "near_miss_slip", "cane_tap_bump"]
    
    all_dfs = []
    for s_idx, subj in enumerate(subjects):
        for act in activities:
            df = generate_simulated_trial(activity=act, duration_sec=8.0, fs=100.0, subject_id=subj, seed=100 + s_idx*10 + len(act))
            all_dfs.append(df)
            
    corpus_df = pd.concat(all_dfs, ignore_index=True)
    corpus_path = os.path.join(output_dir, "simulated_loso_benchmark.csv")
    
    meta = {
        "dataset_type": "SIMULATED",
        "description": "Multi-subject synthetic benchmark for LOSO cross-validation",
        "subjects": subjects,
        "activities": activities,
        "fs_hz": 100
    }
    with open(corpus_path, 'w', encoding='utf-8') as f:
        f.write(f"# DATASET_METADATA: {json.dumps(meta)}\n")
        f.write("# DATASET_TYPE: SIMULATED\n")
        corpus_df.to_csv(f, index=False)
        
    generated.append(corpus_path)
    return generated

if __name__ == "__main__":
    files = generate_all_esa_simulated_corpora()
    print("Generated simulated files:")
    for f in files:
        print(" -", f)
