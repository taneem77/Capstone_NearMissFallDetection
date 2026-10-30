"""Feature extraction for Window objects.

Consumes Window (from windows.py) and produces 1-D feature vectors.
Supports both IMU-only extraction (for KFall baseline) and Fused IMU + Grip extraction
(for live smart cane near-miss detection).
"""
from __future__ import annotations

from typing import List, Optional

import numpy as np
from scipy import stats

from .windows import Window


def _safe_skew(x: np.ndarray) -> float:
    if len(x) < 3 or np.all(x == x[0]):
        return 0.0
    s = float(stats.skew(x, bias=False))
    return 0.0 if not np.isfinite(s) else s


def _safe_kurt(x: np.ndarray) -> float:
    if len(x) < 4 or np.all(x == x[0]):
        return 0.0
    k = float(stats.kurtosis(x, bias=False))
    return 0.0 if not np.isfinite(k) else k


def peak_jerk(w: Window) -> float:
    """Peak |d(acc)/dt| over the window, m/s^3 (vector norm)."""
    if len(w.acc) < 2:
        return 0.0
    diff = np.diff(w.acc, axis=0)
    return float(np.linalg.norm(diff, axis=1).max() * w.fs)


def jerk_series(w: Window) -> np.ndarray:
    """Vector norm of jerk across consecutive frames, m/s^3."""
    if len(w.acc) < 2:
        return np.array([0.0], dtype=np.float64)
    return np.linalg.norm(np.diff(w.acc, axis=0), axis=1) * w.fs


def imu_feature_names() -> List[str]:
    names = [
        # Accel magnitude features
        "acc_mag_mean",
        "acc_mag_std",
        "acc_mag_min",
        "acc_mag_max",
        "acc_mag_ptp",
        "acc_mag_rms",
        "acc_mag_energy",
        "acc_mag_skew",
        "acc_mag_kurt",
        "acc_mag_q25",
        "acc_mag_q75",
        "acc_mag_iqr",
        "acc_mag_peak_ratio",
        # Jerk features
        "jerk_max",
        "jerk_mean",
        "jerk_std",
    ]
    # Per-axis Accel features
    for ax in ("x", "y", "z"):
        names.extend([
            f"acc_{ax}_mean",
            f"acc_{ax}_std",
            f"acc_{ax}_min",
            f"acc_{ax}_max",
            f"acc_{ax}_ptp",
        ])
    # Gyro magnitude features
    names.extend([
        "gyro_mag_mean",
        "gyro_mag_std",
        "gyro_mag_min",
        "gyro_mag_max",
        "gyro_mag_ptp",
        "gyro_mag_rms",
        "gyro_mag_energy",
    ])
    # Per-axis Gyro features
    for ax in ("x", "y", "z"):
        names.extend([
            f"gyro_{ax}_mean",
            f"gyro_{ax}_std",
            f"gyro_{ax}_min",
            f"gyro_{ax}_max",
        ])
    return names


def grip_feature_names() -> List[str]:
    return [
        "grip_mean",
        "grip_std",
        "grip_min",
        "grip_max",
        "grip_ptp",
        "grip_rise",
        "grip_rate_max",
        "grip_rate_mean",
        "grip_jerk_gap_ms",
    ]


def feature_names(use_grip: bool = False) -> List[str]:
    names = imu_feature_names()
    if use_grip:
        names.extend(grip_feature_names())
    return names


def extract_imu(w: Window) -> np.ndarray:
    """Extract IMU kinematics and statistical features from a Window."""
    a = w.acc_mag
    n = len(a)
    if n == 0:
        return np.zeros(len(imu_feature_names()), dtype=np.float64)

    # Accel magnitude stats
    a_mean = float(np.mean(a))
    a_std = float(np.std(a))
    a_min = float(np.min(a))
    a_max = float(np.max(a))
    a_ptp = float(a_max - a_min)
    a_rms = float(np.sqrt(np.mean(a ** 2)))
    a_energy = float(np.sum(a ** 2) / n)
    a_skew = _safe_skew(a)
    a_kurt = _safe_kurt(a)
    q25, q75 = float(np.percentile(a, 25)), float(np.percentile(a, 75))
    a_iqr = q75 - q25
    a_peak_ratio = float(np.argmax(a)) / float(n) if n > 0 else 0.0

    # Jerk features
    j = jerk_series(w)
    j_max = float(np.max(j))
    j_mean = float(np.mean(j))
    j_std = float(np.std(j))

    feats = [
        a_mean, a_std, a_min, a_max, a_ptp,
        a_rms, a_energy, a_skew, a_kurt,
        q25, q75, a_iqr, a_peak_ratio,
        j_max, j_mean, j_std,
    ]

    # Per-axis Accel
    for ax in range(3):
        col = w.acc[:, ax]
        c_min, c_max = float(np.min(col)), float(np.max(col))
        feats.extend([
            float(np.mean(col)),
            float(np.std(col)),
            c_min,
            c_max,
            c_max - c_min,
        ])

    # Gyro magnitude
    gm = np.linalg.norm(w.gyro, axis=1)
    gm_min, gm_max = float(np.min(gm)), float(np.max(gm))
    feats.extend([
        float(np.mean(gm)),
        float(np.std(gm)),
        gm_min,
        gm_max,
        gm_max - gm_min,
        float(np.sqrt(np.mean(gm ** 2))),
        float(np.sum(gm ** 2) / n),
    ])

    # Per-axis Gyro
    for ax in range(3):
        col = w.gyro[:, ax]
        feats.extend([
            float(np.mean(col)),
            float(np.std(col)),
            float(np.min(col)),
            float(np.max(col)),
        ])

    return np.array(feats, dtype=np.float64)


def extract_grip(w: Window, zero_fill_if_none: bool = False) -> np.ndarray:
    """Extract grip (raw FSR) dynamics and cross-modal timing features."""
    num_grip_feats = len(grip_feature_names())
    if w.grip is None:
        if zero_fill_if_none:
            return np.zeros(num_grip_feats, dtype=np.float64)
        raise ValueError("Cannot extract grip features: Window.grip is None.")

    g = np.asarray(w.grip, dtype=np.float64)
    n = len(g)
    if n == 0:
        return np.zeros(num_grip_feats, dtype=np.float64)

    g_mean = float(np.mean(g))
    g_std = float(np.std(g))
    g_min = float(np.min(g))
    g_max = float(np.max(g))
    g_ptp = g_max - g_min
    g_median = float(np.median(g))
    grip_rise = float(g_max - g_median)

    # Rate of grip change
    if n > 1:
        g_diff = np.abs(np.diff(g)) * w.fs
        rate_max = float(np.max(g_diff))
        rate_mean = float(np.mean(g_diff))
    else:
        rate_max = 0.0
        rate_mean = 0.0

    # Cross-modal timing: gap in ms from peak jerk to maximum grip rise
    if n > 1 and len(w.acc) > 1:
        j = jerk_series(w)
        pj = int(np.argmax(j))
        # Search grip from peak jerk to 400 ms window
        lookahead = max(1, int(round(0.4 * w.fs)))
        seg = g[pj: min(n, pj + lookahead)]
        if len(seg) > 0:
            pg = pj + int(np.argmax(seg))
            gap_ms = float((pg - pj) * 1000.0 / w.fs)
        else:
            gap_ms = 0.0
    else:
        gap_ms = 0.0

    return np.array([
        g_mean,
        g_std,
        g_min,
        g_max,
        g_ptp,
        grip_rise,
        rate_max,
        rate_mean,
        gap_ms,
    ], dtype=np.float64)


def extract_fused(w: Window, zero_fill_if_none: bool = False) -> np.ndarray:
    """Extract both IMU kinematics and grip dynamics into a fused feature vector."""
    imu_f = extract_imu(w)
    grip_f = extract_grip(w, zero_fill_if_none=zero_fill_if_none)
    return np.concatenate([imu_f, grip_f])


def extract(w: Window, use_grip: Optional[bool] = None) -> np.ndarray:
    """Primary feature extraction entry point.

    If use_grip is None: automatically extract fused features if w.has_grip else IMU features.
    If use_grip is False: extracts IMU features only.
    If use_grip is True: extracts fused features (zero-filling grip if w.grip is None).
    """
    if use_grip is None:
        use_grip = w.has_grip

    if use_grip:
        return extract_fused(w, zero_fill_if_none=True)
    return extract_imu(w)
