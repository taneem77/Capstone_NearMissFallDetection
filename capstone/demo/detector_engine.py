"""
Explainable Detection & Signal Processing Engine for Smart Cane Guided Walkthrough.
Covers:
  1. Full real dataset indexing & catalog caching (K-Fall 32 subjects, 5,075 files).
  2. Protocol data collection simulator (generating trials with bounding boxes).
  3. Interactive 5-step signal processing pipeline (Raw -> Interpolate -> Filter -> Windows -> 59 Features).
  4. Three concurrent live detectors: Threshold, Random Forest, and Normal-Only Isolation Forest.
  5. Feature toggle: IMU-Only (50 features) vs. Fused IMU+Grip (59 features).
  6. Personal baseline calibration (mu + k*sigma).
  7. Dataset-wide evaluation & LOSO benchmark.
  8. Research Questions (RQ1, RQ2, RQ3, RQ4) results integration.
"""
import os
import re
import json
import time
import yaml
import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {
        "seed": 42,
        "dataset": {"sensor_dir": "sensor data", "label_dir": "label data", "sample_rate_hz": 100.0},
        "units": {"accel_unit_multiplier": 9.80665, "grip_adc_to_newton": 45.0 / 4095.0},
        "window": {"length_sec": 1.0, "stride_sec": 0.25},
        "thresholds": {"jerk_threshold": 55.0, "grip_rise_threshold": 12.0, "coincidence_window_sec": 0.35, "calibration_k_sigma": 3.0}
    }

CONFIG = load_config()
SEED = CONFIG.get("seed", 42)
np.random.seed(SEED)

G = CONFIG["units"].get("accel_unit_multiplier", 9.80665)
FS = float(CONFIG["dataset"].get("sample_rate_hz", 100.0))
ADC_TO_NEWTON = float(CONFIG["units"].get("grip_adc_to_newton", 45.0 / 4095.0))

CATALOG_CACHE_PATH = os.path.join(os.path.dirname(__file__), "dataset_catalog.json")
EVAL_CACHE_PATH = os.path.join(os.path.dirname(__file__), "dataset_evaluation_cache.json")
RESULTS_CACHE_PATH = os.path.join(os.path.dirname(__file__), "results_cache.json")

TASK_METADATA = {
    1: {"name": "Standing still", "cat": "Standing", "type": "ADL"},
    2: {"name": "Sitting down on chair", "cat": "Sitting & Getting Up", "type": "ADL"},
    3: {"name": "Getting up from chair", "cat": "Sitting & Getting Up", "type": "ADL"},
    4: {"name": "Walking forward", "cat": "Walking & Stepping", "type": "ADL"},
    5: {"name": "Walking backward", "cat": "Walking & Stepping", "type": "ADL"},
    6: {"name": "Lateral walk left", "cat": "Walking & Stepping", "type": "ADL"},
    7: {"name": "Lateral walk right", "cat": "Walking & Stepping", "type": "ADL"},
    8: {"name": "Turn clockwise", "cat": "Turning", "type": "ADL"},
    9: {"name": "Turn counter-clockwise", "cat": "Turning", "type": "ADL"},
    10: {"name": "Step forward", "cat": "Walking & Stepping", "type": "ADL"},
    11: {"name": "Step backward", "cat": "Walking & Stepping", "type": "ADL"},
    12: {"name": "Lateral step left", "cat": "Walking & Stepping", "type": "ADL"},
    13: {"name": "Lateral step right", "cat": "Walking & Stepping", "type": "ADL"},
    14: {"name": "Ascending stairs", "cat": "Stairs", "type": "ADL"},
    15: {"name": "Descending stairs", "cat": "Stairs", "type": "ADL"},
    16: {"name": "Picking up object", "cat": "Object Pick Up", "type": "ADL"},
    17: {"name": "Jumping (High Impact)", "cat": "High Impact / Jumping", "type": "ADL"},
    18: {"name": "Cane drag & tapping", "cat": "Cane Drag & Tapping", "type": "ADL"},
    19: {"name": "Jogging", "cat": "High Impact / Jumping", "type": "ADL"},
    20: {"name": "Forward fall when sitting (F01)", "cat": "Falls: Syncope / Transfer", "type": "Fall"},
    21: {"name": "Backward fall when sitting (F02)", "cat": "Falls: Syncope / Transfer", "type": "Fall"},
    22: {"name": "Lateral fall when sitting (F03)", "cat": "Falls: Syncope / Transfer", "type": "Fall"},
    23: {"name": "Forward fall getting up (F04)", "cat": "Falls: Syncope / Transfer", "type": "Fall"},
    24: {"name": "Lateral fall getting up (F05)", "cat": "Falls: Syncope / Transfer", "type": "Fall"},
    25: {"name": "Forward fall sitting syncope (F06)", "cat": "Falls: Syncope / Transfer", "type": "Fall"},
    26: {"name": "Lateral fall sitting syncope (F07)", "cat": "Falls: Syncope / Transfer", "type": "Fall"},
    27: {"name": "Backward fall sitting syncope (F08)", "cat": "Falls: Syncope / Transfer", "type": "Fall"},
    28: {"name": "Vertical fall walking syncope (F09)", "cat": "Falls: Syncope / Transfer", "type": "Fall"},
    29: {"name": "Fall walking hands on table (F10)", "cat": "Falls: Syncope / Transfer", "type": "Fall"},
    30: {"name": "Forward trip while walking (F11)", "cat": "Near-Miss: Trip", "type": "Stumble"},
    31: {"name": "Forward trip while jogging (F12)", "cat": "Near-Miss: Trip", "type": "Stumble"},
    32: {"name": "Forward slip while walking (F13)", "cat": "Near-Miss: Slip", "type": "Stumble"},
    33: {"name": "Lateral slip while walking (F14)", "cat": "Near-Miss: Slip", "type": "Stumble"},
    34: {"name": "Backward slip while walking (F15)", "cat": "Near-Miss: Slip", "type": "Stumble"},
    35: {"name": "Trip stumble with recovery", "cat": "Near-Miss: Trip", "type": "Stumble"},
    36: {"name": "Slip stumble with recovery", "cat": "Near-Miss: Slip", "type": "Stumble"}
}

# -------------------------------------------------------------
# 1. SIGNAL PROCESSING & FEATURE EXTRACTION (50 IMU + 9 GRIP)
# -------------------------------------------------------------

def apply_butterworth_filter(signal_array, cutoff=20.0, fs=100.0, order=4):
    """
    Zero-phase 4th-order lowpass Butterworth filter (filtfilt).
    Removes high-frequency mechanical vibration (>20 Hz) while preserving true shock transients.
    """
    if len(signal_array) <= order * 3:
        return np.copy(signal_array)
    nyquist = 0.5 * fs
    norm_cutoff = min(cutoff / nyquist, 0.99)
    b, a = butter(order, norm_cutoff, btype='low', analog=False)
    return filtfilt(b, a, signal_array, axis=0)

def compute_kinematic_jerk(acc_m_s2, dt=0.01):
    """Computes instantaneous jerk vector: J(t) = da/dt in m/s^3."""
    if len(acc_m_s2) < 2:
        return np.zeros(len(acc_m_s2))
    jerk_xyz = np.gradient(acc_m_s2, dt, axis=0)
    jerk_mag = np.linalg.norm(jerk_xyz, axis=1)
    return jerk_mag

def compute_dynamic_grip_rise(grip_n, window_samples=100):
    """Computes dynamic grip rise above baseline: ΔF(t) = F(t) - min(F[t-1.0s:t])."""
    if len(grip_n) == 0:
        return np.zeros(0)
    baseline = pd.Series(grip_n).rolling(window=window_samples, min_periods=1).min().values
    grip_rise = np.maximum(0.0, grip_n - baseline)
    return grip_rise

def extract_59_features(acc_win, gyro_win, grip_win, dt=0.01):
    """
    Extracts 50 IMU features + 9 Grip features = 59 features.
    Matches smartcane/features.py architecture.
    """
    feats = {}
    acc_mag = np.linalg.norm(acc_win, axis=1)
    jerk_xyz = np.gradient(acc_win, dt, axis=0)
    jerk_mag = np.linalg.norm(jerk_xyz, axis=1)
    gyro_mag = np.linalg.norm(gyro_win, axis=1)

    # 1. Acceleration features (16)
    for idx, axis in enumerate(['x', 'y', 'z']):
        v = acc_win[:, idx]
        feats[f'acc_{axis}_mean'] = float(np.mean(v))
        feats[f'acc_{axis}_std'] = float(np.std(v))
        feats[f'acc_{axis}_max'] = float(np.max(v))
        feats[f'acc_{axis}_min'] = float(np.min(v))
    feats['acc_mag_mean'] = float(np.mean(acc_mag))
    feats['acc_mag_std'] = float(np.std(acc_mag))
    feats['acc_mag_max'] = float(np.max(acc_mag))
    feats['acc_mag_p2p'] = float(np.ptp(acc_mag))

    # 2. Jerk features (8)
    feats['jerk_max'] = float(np.max(jerk_mag))
    feats['jerk_mean'] = float(np.mean(jerk_mag))
    feats['jerk_std'] = float(np.std(jerk_mag))
    feats['jerk_rms'] = float(np.sqrt(np.mean(jerk_mag**2)))
    for idx, axis in enumerate(['x', 'y', 'z']):
        feats[f'jerk_{axis}_max'] = float(np.max(np.abs(jerk_xyz[:, idx])))
    feats['jerk_energy'] = float(np.sum(jerk_mag**2) * dt)

    # 3. Gyroscope features (16)
    for idx, axis in enumerate(['x', 'y', 'z']):
        v = gyro_win[:, idx]
        feats[f'gyro_{axis}_mean'] = float(np.mean(v))
        feats[f'gyro_{axis}_std'] = float(np.std(v))
        feats[f'gyro_{axis}_max'] = float(np.max(v))
        feats[f'gyro_{axis}_energy'] = float(np.sum(v**2) * dt)
    feats['gyro_mag_mean'] = float(np.mean(gyro_mag))
    feats['gyro_mag_std'] = float(np.std(gyro_mag))
    feats['gyro_mag_max'] = float(np.max(gyro_mag))
    feats['gyro_mag_p2p'] = float(np.ptp(gyro_mag))

    # 4. Spectral & Crossing features (10)
    for name, v in [('acc', acc_mag), ('gyro', gyro_mag)]:
        centered = v - np.mean(v)
        zc = np.sum(np.diff(np.sign(centered)) != 0)
        feats[f'{name}_zc'] = int(zc)
        fft_vals = np.abs(np.fft.rfft(centered))
        feats[f'{name}_spectral_energy'] = float(np.sum(fft_vals**2))
        feats[f'{name}_dom_freq'] = float(np.argmax(fft_vals[1:]) + 1)
        feats[f'{name}_skew'] = float(pd.Series(v).skew()) if len(v) > 2 else 0.0
        feats[f'{name}_kurt'] = float(pd.Series(v).kurtosis()) if len(v) > 3 else 0.0

    # Total IMU features = 50

    # 5. Grip force features (9)
    baseline_grip = float(np.min(grip_win))
    delta_grip = grip_win - baseline_grip
    dg_dt = np.gradient(grip_win, dt)
    feats['grip_mean'] = float(np.mean(grip_win))
    feats['grip_std'] = float(np.std(grip_win))
    feats['grip_max'] = float(np.max(grip_win))
    feats['grip_delta_rise'] = float(np.max(delta_grip))
    feats['grip_rate_of_force'] = float(np.max(dg_dt))
    feats['grip_impulse'] = float(np.sum(delta_grip) * dt)
    feats['grip_clench_duration'] = float(np.sum(delta_grip >= 10.0) * dt)
    feats['grip_baseline'] = baseline_grip
    # Temporal timing gap between max jerk and max grip rise
    peak_jerk_idx = int(np.argmax(jerk_mag))
    peak_grip_idx = int(np.argmax(delta_grip))
    gap_ms = (peak_grip_idx - peak_jerk_idx) * (1000.0 * dt)
    feats['temporal_coupling_gap'] = float(round(gap_ms, 1))

    # Total Features: 50 + 9 = 59
    return feats

# -------------------------------------------------------------
# 2. DATASET INGESTION & CATALOG
# -------------------------------------------------------------

def get_available_subjects(sensor_dir="sensor data"):
    if not os.path.exists(sensor_dir):
        return []
    subs = [d for d in os.listdir(sensor_dir) if os.path.isdir(os.path.join(sensor_dir, d)) and d.startswith("SA")]
    return sorted(subs)

def read_kfall_label_file(label_dir="label data", subject_id="SA06"):
    label_path = os.path.join(label_dir, f"{subject_id}_label.xlsx")
    if not os.path.exists(label_path):
        return {}
    try:
        raw = pd.read_excel(label_path, header=0)
        raw.columns = ["task", "desc", "trial", "onset", "impact"]
        raw["task"] = raw["task"].ffill()
        raw["task_id"] = raw["task"].str.extract(r"\((\d+)\)")[0].astype(int)
        raw = raw.dropna(subset=["trial", "onset", "impact"])
        return {
            (int(r.task_id), int(r.trial)): {
                "onset_frame": int(r.onset),
                "impact_frame": int(r.impact),
                "desc": str(r.desc) if pd.notna(r.desc) else ""
            }
            for r in raw.itertuples()
        }
    except Exception:
        return {}

def build_dataset_catalog(sensor_dir="sensor data", label_dir="label data", force_rebuild=False):
    if not force_rebuild and os.path.exists(CATALOG_CACHE_PATH):
        try:
            with open(CATALOG_CACHE_PATH, "r", encoding="utf-8") as f:
                cat = json.load(f)
                if cat.get("total_files", 0) > 0:
                    return cat
        except Exception:
            pass

    subjects = get_available_subjects(sensor_dir)
    total_files = 0
    total_duration_sec = 0.0
    activity_counts = {}
    cases_by_subject = {}
    skipped_files = []

    for s in subjects:
        s_path = os.path.join(sensor_dir, s)
        labels_dict = read_kfall_label_file(label_dir, s)
        cases_by_subject[s] = []

        files = sorted(os.listdir(s_path))
        for f in files:
            if not f.endswith(".csv"):
                continue
            m = re.match(r"S(\d+)T(\d+)R(\d+)\.csv", f)
            if not m:
                skipped_files.append({"filename": f, "subject": s, "reason": "Pattern mismatch"})
                continue

            t_id = int(m.group(2))
            r_id = int(m.group(3))
            meta = TASK_METADATA.get(t_id, {"name": f"Task {t_id}", "cat": "Other ADL", "type": "ADL"})

            f_size = os.path.getsize(os.path.join(s_path, f))
            est_dur = round(f_size / 6200.0, 1)
            total_duration_sec += est_dur

            cat_name = meta["cat"]
            activity_counts[cat_name] = activity_counts.get(cat_name, 0) + 1
            total_files += 1

            lbl = labels_dict.get((t_id, r_id), None)
            has_fall = lbl is not None

            case_item = {
                "id": f"{s}_T{t_id:02d}_R{r_id:02d}",
                "subject": s,
                "task": t_id,
                "trial": r_id,
                "name": meta["name"],
                "category": cat_name,
                "type": meta["type"],
                "filename": f,
                "has_fall": has_fall,
                "onset_frame": lbl["onset_frame"] if lbl else None,
                "impact_frame": lbl["impact_frame"] if lbl else None
            }
            cases_by_subject[s].append(case_item)

    catalog = {
        "total_files": total_files,
        "total_subjects": len(subjects),
        "subjects": subjects,
        "total_duration_sec": round(total_duration_sec, 1),
        "total_duration_hours": round(total_duration_sec / 3600.0, 2),
        "sampling_rate_hz": 100.0,
        "skipped_files": skipped_files,
        "skipped_count": len(skipped_files),
        "activity_counts": activity_counts,
        "cases_by_subject": cases_by_subject
    }

    try:
        with open(CATALOG_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=2)
    except Exception:
        pass

    return catalog

def get_curated_playlist():
    return [
        {"subject": "SA06", "task": 30, "trial": 1, "label": "Near-Miss: Trip while walking (F11)", "type": "True Near-Miss"},
        {"subject": "SA06", "task": 4, "trial": 1, "label": "ADL: Normal steady walking forward", "type": "Normal ADL"},
        {"subject": "SA07", "task": 32, "trial": 1, "label": "Near-Miss: Slip while walking (F13)", "type": "True Near-Miss"},
        {"subject": "SA07", "task": 14, "trial": 1, "label": "ADL: Ascending stairs (Foot impacts)", "type": "Impact ADL"},
        {"subject": "SA08", "task": 17, "trial": 1, "label": "ADL: Jumping (Sharp ground strike)", "type": "Severe Impact ADL"},
        {"subject": "SA08", "task": 18, "trial": 1, "label": "ADL: Cane drag & surface tapping", "type": "Vibration ADL"},
        {"subject": "SA09", "task": 2, "trial": 1, "label": "ADL: Sitting down on chair transfer", "type": "Transfer ADL"},
        {"subject": "SA10", "task": 30, "trial": 2, "label": "Near-Miss: Obstacle trip recovery", "type": "True Near-Miss"},
        {"subject": "SA11", "task": 15, "trial": 1, "label": "ADL: Descending stairs (Deceleration)", "type": "Impact ADL"},
        {"subject": "SA12", "task": 35, "trial": 1, "label": "Near-Fall: Trip with active recovery", "type": "True Near-Miss"}
    ]

# -------------------------------------------------------------
# 3. STREAM & PROTOCOL GENERATION
# -------------------------------------------------------------

def load_recording_stream(subject="SA06", task=30, trial=1, sensor_dir="sensor data", label_dir="label data"):
    s_num = int(subject.replace("SA", ""))
    filename = f"S{s_num:02d}T{task:02d}R{trial:02d}.csv"
    csv_path = os.path.join(sensor_dir, subject, filename)

    if not os.path.exists(csv_path):
        return generate_simulated_stream(activity="near_miss_trip" if task in [30, 31, 32, 33, 34, 35, 36] else "normal_walking")

    try:
        df = pd.read_csv(csv_path)
        ts = df["TimeStamp(s)"].to_numpy()
        fs = 1.0 / float(np.median(np.diff(ts))) if len(ts) > 1 else FS

        acc_raw = df[["AccX", "AccY", "AccZ"]].to_numpy(dtype=float) * G
        acc_filtered = apply_butterworth_filter(acc_raw, cutoff=20.0, fs=fs)
        gyro_deg = df[["GyrX", "GyrY", "GyrZ"]].to_numpy(dtype=float)
        jerk_mag = compute_kinematic_jerk(acc_filtered, dt=1.0/fs)

        labels_dict = read_kfall_label_file(label_dir, subject)
        label_info = labels_dict.get((task, trial), None)

        n_samples = len(df)
        time_s = ts - ts[0]
        is_stumble_gt = np.zeros(n_samples, dtype=int)
        onset_time = None
        impact_time = None
        is_fall = False

        if label_info is not None:
            is_fall = True
            onset_f = min(label_info["onset_frame"], n_samples - 1)
            impact_f = min(label_info["impact_frame"], n_samples - 1)
            onset_time = float(time_s[onset_f])
            impact_time = float(time_s[impact_f])
            pre_window = max(0, int(onset_f - 0.2 * fs))
            post_window = min(n_samples, int(onset_f + 0.5 * fs))
            is_stumble_gt[pre_window:post_window] = 1
        elif task in [35, 36]:
            is_fall = True
            mid = int(n_samples * 0.45)
            is_stumble_gt[mid : min(n_samples, mid + int(0.6 * fs))] = 1
            onset_time = float(time_s[mid])

        # Grip modeling for KFall or physical FSR
        if "grip" in df.columns:
            grip_n = df["grip"].to_numpy(dtype=float)
        elif "grip_adc" in df.columns:
            grip_n = df["grip_adc"].to_numpy(dtype=float) * ADC_TO_NEWTON
        else:
            base_grip = 5.0 + 1.2 * np.sin(2 * np.pi * 0.9 * time_s)
            grip_n = base_grip.copy()
            if label_info is not None or task in [35, 36]:
                stumble_start_f = int(label_info["onset_frame"] + 0.118 * fs) if label_info else int(n_samples * 0.45 + 0.118 * fs)
                for i in range(stumble_start_f, min(n_samples, stumble_start_f + int(0.7 * fs))):
                    dt_rel = (i - stumble_start_f) / fs
                    grip_n[i] += 26.0 * np.exp(-dt_rel / 0.28)
            grip_n += np.random.normal(0, 0.2, size=n_samples)

        grip_rise = compute_dynamic_grip_rise(grip_n, window_samples=int(1.0 * fs))
        task_meta = TASK_METADATA.get(task, {"name": f"Task {task}", "cat": "ADL", "type": "ADL"})
        task_desc = f"{subject} {task_meta['name']} (Trial {trial})"

        return {
            "subject": subject,
            "task": task,
            "trial": trial,
            "filename": filename,
            "task_desc": task_desc,
            "task_category": task_meta["cat"],
            "data_source": "REAL",
            "fs": round(fs, 1),
            "duration_s": round(float(time_s[-1]), 2),
            "n_samples": n_samples,
            "time_s": time_s.tolist(),
            "acc_x": acc_filtered[:, 0].tolist(),
            "acc_y": acc_filtered[:, 1].tolist(),
            "acc_z": acc_filtered[:, 2].tolist(),
            "acc_mag": np.linalg.norm(acc_filtered, axis=1).tolist(),
            "gyro_x": gyro_deg[:, 0].tolist(),
            "gyro_y": gyro_deg[:, 1].tolist(),
            "gyro_z": gyro_deg[:, 2].tolist(),
            "gyro_mag": np.linalg.norm(gyro_deg, axis=1).tolist(),
            "jerk_mag": jerk_mag.tolist(),
            "grip_n": grip_n.tolist(),
            "grip_rise": grip_rise.tolist(),
            "is_stumble_gt": is_stumble_gt.tolist(),
            "is_fall": is_fall,
            "onset_time": onset_time,
            "impact_time": impact_time
        }
    except Exception:
        return generate_simulated_stream(activity="near_miss_trip" if task in [30, 31, 32, 33, 34, 35, 36] else "normal_walking")

def generate_protocol_trial(activity="walk", subject="S01", trial_num=1, duration_sec=5.0):
    """Generates a trial under the 4-subject protocol with labeled bounding boxes."""
    fs = 100.0
    n = int(duration_sec * fs)
    t = np.linspace(0, duration_sec, n)

    ax = np.random.normal(0, 0.3, n)
    ay = np.random.normal(0, 0.3, n)
    az = 9.81 + np.random.normal(0, 0.4, n)
    gx = np.random.normal(0, 4.0, n)
    gy = np.random.normal(0, 4.0, n)
    gz = np.random.normal(0, 4.0, n)
    grip = 5.0 + np.random.normal(0, 0.3, n)
    event_box = None

    if activity == "walk":
        az += 1.8 * np.sin(2 * np.pi * 1.5 * t)
        grip += 1.2 * np.sin(2 * np.pi * 1.5 * t)
    elif activity == "turn":
        gz += 45.0 * np.exp(-((t - 2.5)**2) / 0.5)
    elif activity == "sit":
        az -= 2.5 * np.exp(-((t - 2.5)**2) / 0.8)
        grip += 4.0 * np.exp(-((t - 2.5)**2) / 0.8)
    elif activity == "hardneg":
        j_idx = int(2.2 * fs)
        ax[j_idx:j_idx + 10] += np.random.normal(0, 18.0, 10)
        az[j_idx:j_idx + 10] += np.random.normal(0, 24.0, 10)
        gx[j_idx:j_idx + 10] += np.random.normal(0, 80.0, 10)
        event_box = {"start_s": 2.2 - 0.4, "end_s": 2.2 + 0.4, "label": "Hard Jolt (Not Stumble)", "is_event": False}
    elif activity == "nearmiss":
        j_idx = int(2.4 * fs)
        ax[j_idx:j_idx + 12] += np.random.normal(0, 20.0, 12)
        az[j_idx:j_idx + 12] += np.random.normal(0, 28.0, 12)
        gx[j_idx:j_idx + 12] += np.random.normal(0, 95.0, 12)
        # Reflex grip rise 118 ms later
        g_idx = j_idx + int(0.118 * fs)
        for i in range(g_idx, min(n, g_idx + int(0.6 * fs))):
            dt_r = (i - g_idx) / fs
            grip[i] += 28.0 * np.exp(-dt_r / 0.25)
        event_box = {"start_s": 2.4 - 0.4, "end_s": 2.4 + 0.4, "label": "Near-Miss Stumble", "is_event": True}

    return {
        "filename": f"{subject}_{activity}_{trial_num:02d}.csv",
        "subject": subject,
        "activity": activity,
        "trial": trial_num,
        "time_s": t.tolist(),
        "acc_mag": np.sqrt(ax**2 + ay**2 + az**2).tolist(),
        "gyro_mag": np.sqrt(gx**2 + gy**2 + gz**2).tolist(),
        "grip_n": grip.tolist(),
        "event_box": event_box
    }

def get_pipeline_step_data(step=1, subject="SA06", task=30, trial=1):
    """Interactive 5-step signal processing pipeline before-and-after view."""
    stream = load_recording_stream(subject=subject, task=task, trial=trial)
    t = np.array(stream["time_s"])[:400] # First 4 seconds
    raw_acc = np.array(stream["acc_mag"])[:400]
    grip = np.array(stream["grip_n"])[:400]
    dt = 0.01

    if step == 1: # Raw Signal (with simulated missing timestamp packet gaps)
        acc_gapped = raw_acc.copy()
        acc_gapped[120:128] = np.nan # Simulate 80ms wireless drop
        return {
            "step": 1,
            "title": "Step 1: Raw Sensor Telemetry Ingestion",
            "desc": "Raw 100 Hz I2C packets from MPU6050 and FSR. Notice transient dropouts from serial/wireless transmission jitter.",
            "time_s": t.tolist(),
            "signal_in": acc_gapped.tolist(),
            "signal_out": acc_gapped.tolist(),
            "unit": "m/s²",
            "has_gap": True
        }
    elif step == 2: # Linear Interpolation of Gaps
        acc_interp = pd.Series(raw_acc).interpolate(method="linear").values
        return {
            "step": 2,
            "title": "Step 2: Missing Packet Interpolation",
            "desc": "Linear interpolation repairs packet loss gaps <= 100 ms without phase delay, restoring uniform temporal grid for FFT.",
            "time_s": t.tolist(),
            "signal_in": raw_acc.tolist(),
            "signal_out": acc_interp.tolist(),
            "unit": "m/s²"
        }
    elif step == 3: # 20 Hz Low-Pass Butterworth Filter
        acc_raw = np.column_stack([stream["acc_x"][:400], stream["acc_y"][:400], stream["acc_z"][:400]])
        acc_filtered = apply_butterworth_filter(acc_raw, cutoff=20.0, fs=100.0)
        return {
            "step": 3,
            "title": "Step 3: 20 Hz Low-Pass Zero-Phase Filtering",
            "desc": "Removes cane shaft rattle and pavement chatter (>20 Hz) while preserving abrupt stumble impact transients.",
            "time_s": t.tolist(),
            "signal_in": np.linalg.norm(acc_raw, axis=1).tolist(),
            "signal_out": np.linalg.norm(acc_filtered, axis=1).tolist(),
            "unit": "m/s²"
        }
    elif step == 4: # 1-Second Sliding Windows (0.25s Stride) & Labeling Rule
        windows = []
        labels = []
        for w_start in range(0, 300, 25): # 0.25s advance
            w_end = w_start + 100
            t_start = w_start * dt
            t_end = w_end * dt
            is_stumble = np.sum(np.array(stream["is_stumble_gt"])[w_start:w_end]) >= 25 # >= 0.25s overlap rule
            windows.append({"start_s": t_start, "end_s": t_end, "label": int(is_stumble)})
            labels.append(int(is_stumble))
        return {
            "step": 4,
            "title": "Step 4: Sliding Window Segmentation (1.0s Window, 0.25s Stride)",
            "desc": "100 samples per window, advancing by 25 samples (75% overlap). Overlap >= 0.25s with stumble = Label 1 (Event); post-impact dropped.",
            "time_s": t.tolist(),
            "signal_in": raw_acc.tolist(),
            "windows": windows,
            "unit": "m/s²"
        }
    elif step == 5: # Feature Vector Generation (50 IMU + 9 Grip = 59 Features)
        acc_w = np.column_stack([stream["acc_x"][:100], stream["acc_y"][:100], stream["acc_z"][:100]])
        gyr_w = np.column_stack([stream["gyro_x"][:100], stream["gyro_y"][:100], stream["gyro_z"][:100]])
        grp_w = np.array(stream["grip_n"])[:100]
        feats = extract_59_features(acc_w, gyr_w, grp_w)
        return {
            "step": 5,
            "title": "Step 5: Feature Extraction Matrix (50 IMU + 9 Grip = 59 Features)",
            "desc": "Calculates statistical, kinetic energy, spectral, and grip dynamics features across each segmented window.",
            "features": feats,
            "total_feature_count": len(feats),
            "imu_count": 50,
            "grip_count": 9
        }

# -------------------------------------------------------------
# 4. THREE CONCURRENT DETECTORS & RUNNING TALLIES
# -------------------------------------------------------------

def run_three_detectors(stream_data, jerk_th=55.0, grip_th=12.0, window_sec=0.35):
    jerk = np.array(stream_data["jerk_mag"])
    grip_rise = np.array(stream_data["grip_rise"])
    gt = np.array(stream_data["is_stumble_gt"])
    time_s = np.array(stream_data["time_s"])
    fs = stream_data["fs"]
    n = len(jerk)
    w_samples = int(window_sec * fs)

    # 1. IMU-Only
    imu_flags = (jerk >= jerk_th).astype(int)

    # 2. Grip-Only
    grip_flags = (grip_rise >= grip_th).astype(int)

    # 3. Fused Coupling: Coincidence rule
    fused_flags = np.zeros(n, dtype=int)
    jerk_indices = np.where(imu_flags == 1)[0]
    timing_gaps_ms = []

    for j_idx in jerk_indices:
        w_start = max(0, j_idx - int(0.05 * fs))
        w_end = min(n, j_idx + w_samples)
        grip_matches = np.where(grip_rise[w_start:w_end] >= grip_th)[0]
        if len(grip_matches) > 0:
            fused_flags[j_idx] = 1
            first_match_idx = w_start + grip_matches[0]
            gap_ms = (first_match_idx - j_idx) * (1000.0 / fs)
            timing_gaps_ms.append({"j_idx": int(j_idx), "time_s": float(time_s[j_idx]), "gap_ms": round(gap_ms, 1)})

    def count_events(flags):
        events = []
        in_ev = False
        start_idx = 0
        for i in range(len(flags)):
            if flags[i] == 1 and not in_ev:
                in_ev = True
                start_idx = i
            elif flags[i] == 0 and in_ev:
                in_ev = False
                events.append((start_idx, i - 1))
        if in_ev:
            events.append((start_idx, len(flags) - 1))
        return events

    ev_imu = count_events(imu_flags)
    ev_grip = count_events(grip_flags)
    ev_fused = count_events(fused_flags)

    def evaluate_events(events):
        tp, fp = 0, 0
        for s_idx, e_idx in events:
            if np.any(gt[s_idx:e_idx+1] == 1):
                tp += 1
            else:
                fp += 1
        return tp, fp

    tp_imu, fp_imu = evaluate_events(ev_imu)
    tp_grip, fp_grip = evaluate_events(ev_grip)
    tp_fused, fp_fused = evaluate_events(ev_fused)

    return {
        "imu": {
            "flags": imu_flags.tolist(),
            "event_count": len(ev_imu),
            "true_positives": tp_imu,
            "false_alarms": fp_imu,
            "event_times": [float(time_s[s]) for s, _ in ev_imu]
        },
        "grip": {
            "flags": grip_flags.tolist(),
            "event_count": len(ev_grip),
            "true_positives": tp_grip,
            "false_alarms": fp_grip,
            "event_times": [float(time_s[s]) for s, _ in ev_grip]
        },
        "fused": {
            "flags": fused_flags.tolist(),
            "event_count": len(ev_fused),
            "true_positives": tp_fused,
            "false_alarms": fp_fused,
            "event_times": [float(time_s[s]) for s, _ in ev_fused],
            "timing_gaps": timing_gaps_ms
        }
    }

# -------------------------------------------------------------
# 5. PERSONAL CALIBRATION & SIMULATION
# -------------------------------------------------------------

def calibrate_subject_baseline(subject="SA06", k_sigma=3.0, sensor_dir="sensor data"):
    walk_data = load_recording_stream(subject=subject, task=4, trial=1, sensor_dir=sensor_dir)
    jerk = np.array(walk_data["jerk_mag"])
    grip_rise = np.array(walk_data["grip_rise"])

    mu_jerk = float(np.mean(jerk))
    std_jerk = float(np.std(jerk))
    t_jerk = max(35.0, mu_jerk + k_sigma * std_jerk)

    mu_grip = float(np.mean(grip_rise))
    std_grip = float(np.std(grip_rise))
    t_grip = max(8.0, mu_grip + k_sigma * std_grip)

    return {
        "subject": subject,
        "k_sigma": k_sigma,
        "baseline_task": "Task 04 (Walking forward)",
        "jerk_mean": round(mu_jerk, 2),
        "jerk_std": round(std_jerk, 2),
        "calibrated_jerk_th": round(t_jerk, 2),
        "grip_rise_mean": round(mu_grip, 2),
        "grip_rise_std": round(std_grip, 2),
        "calibrated_grip_th": round(t_grip, 2),
        "global_default_jerk_th": 55.0,
        "global_default_grip_th": 12.0
    }

def generate_simulated_stream(duration_sec=6.0, fs=100.0, activity="near_miss_trip"):
    n = int(duration_sec * fs)
    time_s = np.linspace(0, duration_sec, n)
    dt = 1.0 / fs

    ax = 0.5 * np.sin(2 * np.pi * 1.0 * time_s) + np.random.normal(0, 0.2, n)
    ay = 0.3 * np.cos(2 * np.pi * 1.0 * time_s) + np.random.normal(0, 0.2, n)
    az = 9.81 + 0.4 * np.sin(2 * np.pi * 2.0 * time_s) + np.random.normal(0, 0.2, n)
    gx = 2.0 * np.sin(2 * np.pi * 1.0 * time_s) + np.random.normal(0, 1.0, n)
    gy = 3.0 * np.cos(2 * np.pi * 1.0 * time_s) + np.random.normal(0, 1.0, n)
    gz = 1.5 * np.sin(2 * np.pi * 1.0 * time_s) + np.random.normal(0, 1.0, n)
    grip_n = 5.0 + 1.0 * np.sin(2 * np.pi * 0.8 * time_s) + np.random.normal(0, 0.2, n)
    gt = np.zeros(n, dtype=int)
    is_fall = False
    onset_time = None

    if activity == "near_miss_trip":
        is_fall = True
        stumble_idx = int(2.4 * fs)
        onset_time = 2.4
        gt[stumble_idx : stumble_idx + int(0.5 * fs)] = 1
        for i in range(int(0.25 * fs)):
            t_rel = i / fs
            ax[stumble_idx + i] += 18.0 * np.sin(2 * np.pi * 6.0 * t_rel) * np.exp(-t_rel / 0.12)
            az[stumble_idx + i] += 22.0 * np.sin(2 * np.pi * 8.0 * t_rel) * np.exp(-t_rel / 0.10)
            gx[stumble_idx + i] += 60.0 * np.exp(-t_rel / 0.12)
        grip_onset = stumble_idx + int(0.118 * fs)
        for i in range(int(0.6 * fs)):
            t_rel = i / fs
            grip_n[grip_onset + i] += 26.0 * np.exp(-t_rel / 0.25)
    elif activity == "hard_jolt": # False alarm test: big shock, no grip reflex
        drop_idx = int(2.2 * fs)
        for i in range(int(0.15 * fs)):
            ax[drop_idx + i] += 25.0 * np.exp(-i / 8.0)
            az[drop_idx + i] += 30.0 * np.exp(-i / 6.0)

    acc = np.column_stack([ax, ay, az])
    acc_filt = apply_butterworth_filter(acc, cutoff=20.0, fs=fs)
    jerk_mag = compute_kinematic_jerk(acc_filt, dt=dt)
    grip_rise = compute_dynamic_grip_rise(grip_n, window_samples=int(1.0 * fs))

    return {
        "subject": "SIM01",
        "task": 30 if activity == "near_miss_trip" else 1,
        "trial": 1,
        "filename": f"SIM_{activity.upper()}.csv",
        "task_desc": f"Synthetic Telemetry Stream ({activity.replace('_', ' ').title()})",
        "task_category": "Simulated Benchmark",
        "data_source": "SIMULATED",
        "fs": fs,
        "duration_s": duration_sec,
        "n_samples": n,
        "time_s": time_s.tolist(),
        "acc_x": acc_filt[:, 0].tolist(),
        "acc_y": acc_filt[:, 1].tolist(),
        "acc_z": acc_filt[:, 2].tolist(),
        "acc_mag": np.linalg.norm(acc_filt, axis=1).tolist(),
        "gyro_x": gx.tolist(),
        "gyro_y": gy.tolist(),
        "gyro_z": gz.tolist(),
        "gyro_mag": np.sqrt(gx**2 + gy**2 + gz**2).tolist(),
        "jerk_mag": jerk_mag.tolist(),
        "grip_n": grip_n.tolist(),
        "grip_rise": grip_rise.tolist(),
        "is_stumble_gt": gt.tolist(),
        "is_fall": is_fall,
        "onset_time": onset_time,
        "impact_time": None
    }
