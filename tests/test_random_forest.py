"""Tests for smartcane.detectors.random_forest."""
from __future__ import annotations

import numpy as np
import pytest

from smartcane.detectors.random_forest import RandomForestDetector, featurize
from smartcane.windows import Window


def _create_mock_dataset(n_samples: int = 40, has_grip: bool = True):
    wins = []
    y = []
    rng = np.random.default_rng(42)
    for i in range(n_samples):
        label = 1 if i % 2 == 0 else 0
        acc_scale = 18.0 if label == 1 else 9.8
        acc = rng.normal(acc_scale, 2.0, (100, 3)).astype(np.float64)
        gyro = rng.normal(0.0, 50.0 if label == 1 else 5.0, (100, 3)).astype(np.float64)
        grip = (rng.normal(250.0 if label == 1 else 40.0, 10.0, 100)).astype(np.float64) if has_grip else None

        w = Window(
            acc=acc,
            gyro=gyro,
            fs=100.0,
            subject=f"subj_{i % 4}",
            task=20 if label == 1 else 1,
            trial=i,
            start=i * 100,
            label=label,
            grip=grip,
        )
        wins.append(w)
        y.append(label)
    return wins, np.array(y)


def test_featurize_caching():
    wins, _ = _create_mock_dataset(n_samples=5, has_grip=True)
    # Cache IMU
    X_imu1 = featurize(wins, use_grip=False)
    assert hasattr(wins[0], "_feat_imu")
    X_imu2 = featurize(wins, use_grip=False)
    assert np.array_equal(X_imu1, X_imu2)

    # Cache Fused
    X_fused1 = featurize(wins, use_grip=True)
    assert hasattr(wins[0], "_feat_fused")
    assert X_fused1.shape[1] == 59
    assert X_imu1.shape[1] == 50


def test_random_forest_imu_mode():
    wins, y = _create_mock_dataset(n_samples=30, has_grip=False)
    clf = RandomForestDetector(n_estimators=20, seed=42, use_grip=False)
    assert clf.name == "random_forest_imu"

    clf.fit(wins, y)
    scores = clf.score(wins)
    preds = clf.predict(wins)

    assert len(scores) == len(wins)
    assert len(preds) == len(wins)
    assert np.all((scores >= 0.0) & (scores <= 1.0))
    assert np.all((preds == 0) | (preds == 1))

    top_feats = clf.top_features(top_n=5)
    assert len(top_feats) == 5
    assert all(isinstance(name, str) and isinstance(imp, float) for name, imp in top_feats)


def test_random_forest_fused_mode():
    wins, y = _create_mock_dataset(n_samples=30, has_grip=True)
    clf = RandomForestDetector(n_estimators=20, seed=42, use_grip=True)
    assert clf.name == "random_forest_fused"

    clf.fit(wins, y)
    scores = clf.score(wins)
    preds = clf.predict(wins)

    assert len(scores) == len(wins)
    assert len(preds) == len(wins)
    assert np.all((scores >= 0.0) & (scores <= 1.0))


def test_random_forest_fused_error_on_missing_grip():
    wins, y = _create_mock_dataset(n_samples=10, has_grip=False)
    clf = RandomForestDetector(n_estimators=10, use_grip=True)
    with pytest.raises(ValueError, match="use_grip=True requires Window.grip data"):
        clf.fit(wins, y)
