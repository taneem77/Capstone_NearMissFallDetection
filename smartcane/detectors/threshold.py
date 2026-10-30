"""RQ1 baseline A: single global threshold on peak jerk (IMU-only).

use_grip=True is the fused slot: also requires a grip rise in the window.
It needs Window.grip, so it only works once cane data exists (KFall has no grip).
"""
from __future__ import annotations

import numpy as np

from ..windows import Window
from .base import Detector


def peak_jerk(w: Window) -> float:
    """Peak |d(acc)/dt| over the window, m/s^3 (vector norm)."""
    return float(np.linalg.norm(np.diff(w.acc, axis=0), axis=1).max() * w.fs)


def grip_rise(w: Window) -> float:
    """Max grip force above the window's median, N."""
    return float(np.max(w.grip) - np.median(w.grip))


def _best_threshold(x: np.ndarray, y: np.ndarray) -> float:
    cands = np.unique(np.quantile(x, np.linspace(0.01, 0.99, 197)))
    pos, neg = y == 1, y == 0
    j = [(x[pos] >= t).mean() + (x[neg] < t).mean() - 1 for t in cands]   # Youden's J
    return float(cands[int(np.argmax(j))])


class ThresholdDetector(Detector):
    def __init__(self, use_grip: bool = False):
        self.use_grip = use_grip
        self.name = "threshold_fused" if use_grip else "threshold_imu"
        self.jerk_thr = np.inf
        self.grip_thr = 0.0

    def fit(self, wins, y):
        y = np.asarray(y)
        jerk = np.array([peak_jerk(w) for w in wins])
        self.jerk_thr = _best_threshold(jerk, y)
        if self.use_grip:
            if not all(w.has_grip for w in wins):
                raise ValueError("use_grip=True needs Window.grip (no grip in KFall)")
            g = np.array([grip_rise(w) for w in wins])
            hit = jerk >= self.jerk_thr          # tune grip gate only among jerk hits
            self.grip_thr = _best_threshold(g[hit], y[hit]) if hit.any() and len(set(y[hit])) == 2 else 0.0
        self.cutoff = 0.5
        return self

    def score(self, wins):
        jerk = np.array([peak_jerk(w) for w in wins])
        s = jerk / self.jerk_thr                  # >=1 means over threshold
        if self.use_grip:
            g = np.array([grip_rise(w) for w in wins])
            s = np.where(g >= self.grip_thr, s, 0.0)
        return s

    def predict(self, wins):
        return (self.score(wins) >= 1.0).astype(int)
