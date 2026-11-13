"""Tests for smartcane.features."""
from __future__ import annotations

import numpy as np
import pytest

from smartcane.features import (
    extract,
    extract_fused,
    extract_grip,
    extract_imu,
    feature_names,
    grip_feature_names,
    imu_feature_names,
    peak_jerk,
)
from smartcane.windows import Window


def _make_dummy_window(has_grip: bool = True, n_samples: int = 100, fs: float = 100.0) -> Window:
    t = np.arange(n_samples, dtype=np.float64) / fs
    acc = np.zeros((n_samples, 3), dtype=np.float64)
    acc[:, 0] = np.sin(2 * np.pi * 2.0 * t) * 3.0
    acc[:, 1] = np.cos(2 * np.pi * 2.0 * t) * 4.0
    acc[:, 2] = 9.80665

    gyro = np.zeros((n_samples, 3), dtype=np.float64)
    gyro[:, 0] = 10.0 * np.sin(2 * np.pi * 1.0 * t)
    gyro[:, 1] = 20.0 * np.cos(2 * np.pi * 1.0 * t)
    gyro[:, 2] = 5.0

    grip = (50.0 + 30.0 * np.sin(2 * np.pi * 0.5 * t)).astype(np.float64) if has_grip else None

    return Window(
        acc=acc,
        gyro=gyro,
        fs=fs,
        subject="test_subj",
        task=20,
        trial=1,
        start=0,
        label=1,
        grip=grip,
    )


def test_feature_names():
    imu_names = imu_feature_names()
    assert len(imu_names) == 50
    assert "acc_mag_mean" in imu_names
    assert "jerk_max" in imu_names
    assert "gyro_mag_rms" in imu_names

    grip_names = grip_feature_names()
    assert len(grip_names) == 9
    assert "grip_rise" in grip_names
    assert "grip_jerk_gap_ms" in grip_names

    fused_names = feature_names(use_grip=True)
    assert len(fused_names) == 50 + 9
    assert fused_names[:50] == imu_names
    assert fused_names[50:] == grip_names


def test_extract_imu():
    w = _make_dummy_window(has_grip=False)
    f = extract_imu(w)
    assert isinstance(f, np.ndarray)
    assert f.shape == (50,)
    assert np.all(np.isfinite(f))


def test_extract_grip_with_and_without_grip():
    w_with = _make_dummy_window(has_grip=True)
    f_grip = extract_grip(w_with)
    assert isinstance(f_grip, np.ndarray)
    assert f_grip.shape == (9,)
    assert np.all(np.isfinite(f_grip))

    w_without = _make_dummy_window(has_grip=False)
    with pytest.raises(ValueError, match="Window.grip is None"):
        extract_grip(w_without, zero_fill_if_none=False)

    f_zero = extract_grip(w_without, zero_fill_if_none=True)
    assert f_zero.shape == (9,)
    assert np.all(f_zero == 0.0)


def test_extract_auto_dispatch():
    w_with = _make_dummy_window(has_grip=True)
    f_with = extract(w_with)
    assert f_with.shape == (59,)

    w_without = _make_dummy_window(has_grip=False)
    f_without = extract(w_without)
    assert f_without.shape == (50,)


def test_extract_constant_signals():
    # Test numerical stability with zero variance / constant input
    acc = np.full((100, 3), 9.8)
    gyro = np.full((100, 3), 0.0)
    grip = np.full(100, 20.0)
    w = Window(acc=acc, gyro=gyro, fs=100.0, subject="c", task=1, trial=1, start=0, label=0, grip=grip)

    f = extract(w, use_grip=True)
    assert f.shape == (59,)
    assert np.all(np.isfinite(f))
    assert not np.any(np.isnan(f))
