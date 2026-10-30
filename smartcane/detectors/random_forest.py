"""Random Forest detector on window features.

Supports both IMU-only classification (RQ1 baseline) and Fused IMU + Grip classification
for live smart cane near-miss fall detection.
Features are extracted via smartcane.features.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from ..features import extract, feature_names
from ..windows import Window
from .base import Detector


def featurize(wins: Sequence[Window], use_grip: bool = False) -> np.ndarray:
    """Compute and cache features on the window object.

    Caches separately for IMU-only ('_feat_imu') and fused ('_feat_fused')
    so that shared window instances can be evaluated across multiple detector configurations.
    """
    cache_attr = "_feat_fused" if use_grip else "_feat_imu"
    out: List[np.ndarray] = []
    for w in wins:
        f = getattr(w, cache_attr, None)
        if f is None:
            f = extract(w, use_grip=use_grip)
            setattr(w, cache_attr, f)
        out.append(f)
    if not out:
        dim = len(feature_names(use_grip=use_grip))
        return np.empty((0, dim), dtype=np.float64)
    return np.vstack(out)


class RandomForestDetector(Detector):
    """Random Forest fall & near-miss detector.

    Parameters:
    -----------
    n_estimators: Number of trees in the forest.
    seed: Random state seed.
    use_grip: Whether to fuse IMU kinematics with grip (FSR) dynamics.
    max_depth: Maximum tree depth (None for unlimited).
    min_samples_leaf: Minimum samples per leaf node.
    cutoff: Classification probability threshold (default 0.5).
    """

    def __init__(
        self,
        n_estimators: int = 200,
        seed: int = 0,
        use_grip: bool = False,
        max_depth: Optional[int] = None,
        min_samples_leaf: int = 2,
        cutoff: float = 0.5,
    ):
        self.use_grip = use_grip
        self.name = "random_forest_fused" if use_grip else "random_forest_imu"
        self.cutoff = cutoff
        self.seed = seed
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf

        self.clf = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            class_weight="balanced_subsample",
            min_samples_leaf=min_samples_leaf,
            n_jobs=-1,
            random_state=seed,
        )
        self.feature_names_: List[str] = feature_names(use_grip=use_grip)
        self.feature_importances_: Optional[np.ndarray] = None

    def fit(self, wins: Sequence[Window], y: Sequence[int] | np.ndarray) -> "RandomForestDetector":
        y_arr = np.asarray(y, dtype=int)
        if self.use_grip and not all(w.has_grip for w in wins):
            raise ValueError("use_grip=True requires Window.grip data for all training windows.")

        X = featurize(wins, use_grip=self.use_grip)
        self.clf.fit(X, y_arr)
        self.feature_importances_ = self.clf.feature_importances_
        return self

    def score(self, wins: Sequence[Window]) -> np.ndarray:
        """Return event probability score for each window (shape: len(wins),)."""
        if len(wins) == 0:
            return np.array([], dtype=np.float64)
        if self.use_grip and not all(w.has_grip for w in wins):
            raise ValueError("use_grip=True requires Window.grip data for all evaluation windows.")

        X = featurize(wins, use_grip=self.use_grip)
        # If classifier only saw 1 class during fit (e.g., negative-only fold), handle gracefully
        if len(self.clf.classes_) == 1:
            cls = self.clf.classes_[0]
            prob = 1.0 if cls == 1 else 0.0
            return np.full(len(wins), prob, dtype=np.float64)

        return self.clf.predict_proba(X)[:, 1]

    def predict(self, wins: Sequence[Window]) -> np.ndarray:
        """Classify windows as 1 (event) or 0 (normal) using self.cutoff."""
        return (self.score(wins) >= self.cutoff).astype(int)

    def top_features(self, top_n: int = 10) -> List[tuple[str, float]]:
        """Return the top N most important features and their Gini importances."""
        if self.feature_importances_ is None:
            raise RuntimeError("Detector must be fitted before querying feature importances.")
        indices = np.argsort(self.feature_importances_)[::-1][:top_n]
        return [(self.feature_names_[i], float(self.feature_importances_[i])) for i in indices]
