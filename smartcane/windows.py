"""Cleaning + windowing. Recording -> list[Window].

Window is what features.py (Satvik) and every detector consumes.
`grip` is the slot for the fused version: None for KFall, filled for cane data.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

import numpy as np
from scipy.signal import butter, sosfiltfilt

from .io import Recording


@dataclass
class Window:
    acc: np.ndarray                  # (T,3) m/s^2
    gyro: np.ndarray                 # (T,3) deg/s
    fs: float
    subject: str
    task: int
    trial: int
    start: int                       # frame index in the recording
    label: int                       # 1 event, 0 normal  (-1 never leaves make_windows unless keep_ignored)
    grip: Optional[np.ndarray] = None  # (T,) N  -- fused detectors read this

    @property
    def acc_mag(self) -> np.ndarray:
        return np.linalg.norm(self.acc, axis=1)

    @property
    def has_grip(self) -> bool:
        return self.grip is not None


def lowpass(x: np.ndarray, fs: float, cutoff: float = 20.0, order: int = 4) -> np.ndarray:
    """Zero-phase Butterworth. Offline only -- the live path needs a causal filter (sosfilt)."""
    sos = butter(order, cutoff / (fs / 2), btype="low", output="sos")
    return sosfiltfilt(sos, x, axis=0)


def clean(rec: Recording, cutoff: float = 20.0) -> Recording:
    """Drop NaNs (interpolate), low-pass. Returns a new Recording."""
    def fix(a):
        a = np.asarray(a, dtype=np.float64).copy()
        if a.ndim == 1:
            a = a[:, None]
        for c in range(a.shape[1]):
            bad = ~np.isfinite(a[:, c])
            if bad.any():
                idx = np.arange(len(a))
                a[bad, c] = np.interp(idx[bad], idx[~bad], a[~bad, c])
        return a

    acc, gyro = fix(rec.acc), fix(rec.gyro)
    grip = fix(rec.grip)[:, 0] if rec.grip is not None else None
    if rec.n > 30:   # filtfilt needs padding room
        acc, gyro = lowpass(acc, rec.fs, cutoff), lowpass(gyro, rec.fs, cutoff)
        if grip is not None:
            grip = lowpass(grip, rec.fs, cutoff)[:]
    return Recording(rec.subject, rec.task, rec.trial, rec.fs, acc, gyro, grip,
                     rec.fall_onset, rec.fall_impact)


def make_windows(rec: Recording, win_s: float = 1.0, stride_s: float = 0.25,
                 min_overlap_s: float = 0.25, keep_ignored: bool = False) -> list[Window]:
    """Slide a window over one (already cleaned) recording and label it.

    Fall trials: label=1 if the window overlaps [fall_onset, fall_impact] by
    >= min_overlap_s; label=-1 (ignored) if it starts after impact (person on floor);
    else 0. ADL trials: always 0.
    Label frames are 1-based FrameCounter values, hence the -1.
    """
    W, S = int(round(win_s * rec.fs)), int(round(stride_s * rec.fs))
    M = int(round(min_overlap_s * rec.fs))
    out = []
    for s in range(0, rec.n - W + 1, S):
        e = s + W
        label = 0
        if rec.is_fall:
            on, im = rec.fall_onset - 1, rec.fall_impact - 1
            overlap = min(e, im) - max(s, on)
            if overlap >= M:
                label = 1
            elif s >= im:
                label = -1
        if label == -1 and not keep_ignored:
            continue
        out.append(Window(rec.acc[s:e], rec.gyro[s:e], rec.fs, rec.subject, rec.task,
                          rec.trial, s, label,
                          rec.grip[s:e] if rec.grip is not None else None))
    return out


def build_dataset(recs: Iterable[Recording], **kw) -> list[Window]:
    cutoff = kw.pop("cutoff", 20.0)
    wins: list[Window] = []
    for r in recs:
        wins.extend(make_windows(clean(r, cutoff), **kw))
    return wins


def labels(wins: list[Window]) -> np.ndarray:
    return np.array([w.label for w in wins], dtype=int)


def subjects(wins: list[Window]) -> np.ndarray:
    return np.array([w.subject for w in wins])
