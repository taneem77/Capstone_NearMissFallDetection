"""Tests for smartcane.io live sensor CSV parsing, writing, and validation."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from smartcane.io import (
    LIVE_SENSOR_COLUMNS,
    Recording,
    read_live_sensor_csv,
    validate_live_sensor_df,
    write_live_sensor_csv,
)
from smartcane.windows import clean, make_windows


def _make_sample_live_df(n_samples: int = 100, fs: float = 100.0) -> pd.DataFrame:
    t = np.arange(n_samples, dtype=np.float64) / fs
    data = {
        "timestamp": t,
        "acc_x": np.sin(t * 2 * np.pi) * 2.0,
        "acc_y": np.cos(t * 2 * np.pi) * 9.8,
        "acc_z": np.zeros(n_samples),
        "gyro_x": np.ones(n_samples) * 10.0,
        "gyro_y": np.ones(n_samples) * 20.0,
        "gyro_z": np.ones(n_samples) * 30.0,
        "grip": np.linspace(100.0, 800.0, n_samples),
    }
    return pd.DataFrame(data, columns=list(LIVE_SENSOR_COLUMNS))


def test_validate_live_sensor_df_valid():
    df = _make_sample_live_df()
    validate_live_sensor_df(df)  # Should not raise


def test_validate_live_sensor_df_missing_columns():
    df = _make_sample_live_df().drop(columns=["grip"])
    with pytest.raises(ValueError, match="Missing required sensor columns"):
        validate_live_sensor_df(df)


def test_validate_live_sensor_df_empty():
    df = pd.DataFrame(columns=list(LIVE_SENSOR_COLUMNS))
    with pytest.raises(ValueError, match="empty"):
        validate_live_sensor_df(df)


def test_validate_live_sensor_df_nan_values():
    df = _make_sample_live_df()
    df.loc[5, "acc_x"] = np.nan
    with pytest.raises(ValueError, match="contain missing/NaN values"):
        validate_live_sensor_df(df)


def test_validate_live_sensor_df_non_monotonic_timestamp():
    df = _make_sample_live_df()
    df.loc[10, "timestamp"] = df.loc[9, "timestamp"]  # duplicate / non-monotonic
    with pytest.raises(ValueError, match="monotonically increasing"):
        validate_live_sensor_df(df)


def test_validate_live_sensor_df_non_numeric():
    df = _make_sample_live_df()
    df["gyro_x"] = "invalid_string"
    with pytest.raises(ValueError, match="non-numeric"):
        validate_live_sensor_df(df)


def test_write_and_read_live_sensor_csv_roundtrip(tmp_path):
    csv_file = tmp_path / "test_cane_stream.csv"
    acc = np.random.randn(200, 3).astype(np.float32)
    gyro = np.random.randn(200, 3).astype(np.float32)
    grip = np.random.uniform(50, 600, 200).astype(np.float32)

    rec_orig = Recording(
        subject="test_user",
        task=99,
        trial=1,
        fs=100.0,
        acc=acc,
        gyro=gyro,
        grip=grip,
    )

    written_path = write_live_sensor_csv(csv_file, rec_orig)
    assert written_path.exists()

    rec_loaded = read_live_sensor_csv(csv_file, subject="test_user", task=99, trial=1)
    assert rec_loaded.subject == "test_user"
    assert rec_loaded.task == 99
    assert rec_loaded.trial == 1
    assert rec_loaded.fs == 100.0
    assert rec_loaded.n == 200
    np.testing.assert_allclose(rec_loaded.acc, acc, rtol=1e-5, atol=1e-5)
    np.testing.assert_allclose(rec_loaded.gyro, gyro, rtol=1e-5, atol=1e-5)
    np.testing.assert_allclose(rec_loaded.grip, grip, rtol=1e-5, atol=1e-5)


def test_live_recording_integration_with_windows(tmp_path):
    csv_file = tmp_path / "stream_windows.csv"
    df = _make_sample_live_df(n_samples=250, fs=100.0)
    df.to_csv(csv_file, index=False)

    rec = read_live_sensor_csv(csv_file, subject="user_01", task=1, trial=1)
    cleaned_rec = clean(rec, cutoff=20.0)
    assert cleaned_rec.grip is not None
    assert len(cleaned_rec.grip) == rec.n

    wins = make_windows(cleaned_rec, win_s=1.0, stride_s=0.25)
    assert len(wins) > 0
    for w in wins:
        assert w.has_grip
        assert w.grip is not None
        assert len(w.grip) == len(w.acc)
