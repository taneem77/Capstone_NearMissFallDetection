"""Detector contract. Everyone's detector (threshold, RF, personalized, normal-only) follows this."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

import numpy as np

from ..windows import Window


class Detector(ABC):
    name = "detector"

    @abstractmethod
    def fit(self, wins: Sequence[Window], y: np.ndarray) -> "Detector":
        """Train on windows (y: 1 event / 0 normal). Normal-only detectors just ignore y==1."""

    @abstractmethod
    def score(self, wins: Sequence[Window]) -> np.ndarray:
        """Higher = more event-like. Shape (len(wins),). Used for ROC / FA-per-hour sweeps."""

    def predict(self, wins: Sequence[Window]) -> np.ndarray:
        return (self.score(wins) >= self.cutoff).astype(int)

    cutoff: float = 0.5   # decision cutoff on score(); subclasses set it in fit()
