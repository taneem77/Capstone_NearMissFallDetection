"""Data-source interface. KFall replay now, live cane serial later (Samika) -- same shape."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterator

from ..io import Recording


class Source(ABC):
    @abstractmethod
    def recordings(self) -> Iterator[Recording]:
        """Yield complete recordings (offline replay)."""
