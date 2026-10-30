"""Raw readers + the Recording container. KFall-specific parsing lives here.

Recording is the single hand-off object for the whole pipeline:
sources/ makes them, windows.py consumes them.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

G = 9.80665
FNAME = re.compile(r"S(\d+)T(\d+)R(\d+)\.csv$")


@dataclass
class Recording:
    subject: str                  # 'SA06'
    task: int                     # KFall task id (1..36)
    trial: int
    fs: float                     # Hz
    acc: np.ndarray               # (N,3) m/s^2
    gyro: np.ndarray              # (N,3) deg/s
    grip: Optional[np.ndarray] = None   # (N,) N (newtons) -- None until cane data exists
    fall_onset: Optional[int] = None    # frame index, None for ADL trials
    fall_impact: Optional[int] = None

    @property
    def n(self) -> int:
        return len(self.acc)

    @property
    def is_fall(self) -> bool:
        return self.fall_onset is not None

    @property
    def uid(self) -> str:
        return f"{self.subject}_T{self.task:02d}_R{self.trial:02d}"


def parse_name(path: Path) -> tuple[int, int, int]:
    m = FNAME.search(path.name)
    if not m:
        raise ValueError(f"not a KFall sensor file: {path}")
    s, t, r = map(int, m.groups())
    return s, t, r


def read_sensor_csv(path: Path) -> dict:
    """KFall csv: TimeStamp(s),FrameCounter,AccX..Z (g),GyrX..Z (deg/s),Euler*. 100 Hz."""
    df = pd.read_csv(path)
    ts = df["TimeStamp(s)"].to_numpy()
    fs = 1.0 / float(np.median(np.diff(ts))) if len(ts) > 1 else 100.0
    return dict(
        fs=round(fs),
        acc=df[["AccX", "AccY", "AccZ"]].to_numpy(dtype=np.float32) * G,
        gyro=df[["GyrX", "GyrY", "GyrZ"]].to_numpy(dtype=np.float32),
        frame=df["FrameCounter"].to_numpy(),
    )


def read_labels(xlsx: Path) -> dict[tuple[int, int], tuple[int, int]]:
    """{(task_id, trial_id): (onset_frame, impact_frame)} from a SAxx_label.xlsx.

    The sheet only writes the task code on the first row of each block
    ('F01 (20)'), so forward-fill it. Frames are FrameCounter values (1-based).
    """
    raw = pd.read_excel(xlsx, header=0)
    raw.columns = ["task", "desc", "trial", "onset", "impact"]
    raw["task"] = raw["task"].ffill()
    raw["task_id"] = raw["task"].str.extract(r"\((\d+)\)")[0].astype(int)
    raw = raw.dropna(subset=["trial", "onset", "impact"])
    return {
        (int(r.task_id), int(r.trial)): (int(r.onset), int(r.impact))
        for r in raw.itertuples()
    }
