"""RQ1 baseline B: random forest on window features (IMU-only by default).

Features come from features.py (Satvik): `extract(window) -> 1-D np.ndarray`.
Until that lands, a small built-in set is used so the baseline runs today.
"""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from ..windows import Window
from .base import Detector
from .threshold import peak_jerk

try:
    from ..features import extract as _extract      # Satvik's module
except ImportError:
    _extract = None


def _fallback_features(w: Window) -> np.ndarray:
    a = w.acc_mag
    gm = np.linalg.norm(w.gyro, axis=1)
    f = [a.max(), a.min(), a.std(), np.ptp(a), gm.max(), gm.std(), peak_jerk(w),
         float(np.argmax(a)) / len(a)]
    return np.array(f, dtype=np.float64)


def featurize(wins) -> np.ndarray:
    """Features are computed once per window and cached on the window object."""
    fn = _extract or _fallback_features
    out = []
    for w in wins:
        f = getattr(w, "_feat", None)
        if f is None:
            f = fn(w)
            w._feat = f
        out.append(f)
    return np.vstack(out)


class RandomForestDetector(Detector):
    def __init__(self, n_estimators: int = 200, seed: int = 0):
        self.name = "random_forest_imu"
        self.clf = RandomForestClassifier(n_estimators=n_estimators, class_weight="balanced_subsample",
                                          min_samples_leaf=2, n_jobs=-1, random_state=seed)
        self.cutoff = 0.5

    def fit(self, wins, y):
        self.clf.fit(featurize(wins), np.asarray(y))
        return self

    def score(self, wins):
        return self.clf.predict_proba(featurize(wins))[:, 1]