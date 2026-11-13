"""Raw readers + the Recording container. KFall-specific parsing lives here.

Recording is the single hand-off object for the whole pipeline:
sources/ makes them, windows.py consumes them.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

import numpy as np
import pandas as pd

G = 9.80665
FNAME = re.compile(r"S(\d+)T(\d+)R(\d+)\.csv$")

LIVE_SENSOR_COLUMNS = (
    "timestamp",
    "acc_x",
    "acc_y",
    "acc_z",
    "gyro_x",
    "gyro_y",
    "gyro_z",
    "grip",
)


@dataclass
class Recording:
    subject: str                  # 'SA06' or cane session id
    task: int                     # KFall task id (1..36) or custom code
    trial: int
    fs: float                     # Hz
    acc: np.ndarray               # (N,3) m/s^2
    gyro: np.ndarray              # (N,3) deg/s
    grip: Optional[np.ndarray] = None   # (N,) raw FSR reading (or calibrated N)
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


def validate_live_sensor_df(df: pd.DataFrame) -> None:
    """Validate DataFrame conforms to live sensor CSV format.

    Required columns in exact names:
    timestamp (seconds), acc_x, acc_y, acc_z (m/s^2),
    gyro_x, gyro_y, gyro_z (deg/s), grip (raw FSR).
    """
    if df.empty:
        raise ValueError("Sensor data is empty (0 rows).")

    missing = [c for c in LIVE_SENSOR_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required sensor columns: {missing}. Expected: {list(LIVE_SENSOR_COLUMNS)}")

    # Check for NaN / null values
    nan_cols = [c for c in LIVE_SENSOR_COLUMNS if df[c].isna().any()]
    if nan_cols:
        raise ValueError(f"Sensor columns contain missing/NaN values: {nan_cols}")

    # Validate numeric convertibility
    for c in LIVE_SENSOR_COLUMNS:
        if not np.issubdtype(df[c].dtype, np.number):
            try:
                pd.to_numeric(df[c])
            except Exception as e:
                raise ValueError(f"Column '{c}' contains non-numeric data: {e}")

    # Validate timestamps
    ts = pd.to_numeric(df["timestamp"]).to_numpy(dtype=np.float64)
    if len(ts) > 1:
        diffs = np.diff(ts)
        if np.any(diffs <= 0):
            bad_idx = int(np.where(diffs <= 0)[0][0])
            raise ValueError(
                f"Timestamps must be strictly monotonically increasing. "
                f"Non-monotonic at row {bad_idx + 1}: t0={ts[bad_idx]}, t1={ts[bad_idx + 1]}"
            )
        median_dt = float(np.median(diffs))
        if median_dt <= 0:
            raise ValueError(f"Invalid timestamp interval: median dt = {median_dt}")


def read_live_sensor_csv(
    path: Path | str,
    subject: str = "cane_user",
    task: int = 0,
    trial: int = 1,
    fall_onset: Optional[int] = None,
    fall_impact: Optional[int] = None,
) -> Recording:
    """Read a live cane sensor CSV into a Recording container.

    Expected CSV columns:
    timestamp,acc_x,acc_y,acc_z,gyro_x,gyro_y,gyro_z,grip

    - timestamp: Seconds
    - acc_x, acc_y, acc_z: m/s^2
    - gyro_x, gyro_y, gyro_z: deg/s
    - grip: raw FSR reading (preserved as raw sensor values)
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Sensor CSV file does not exist: {path}")

    df = pd.read_csv(path)
    validate_live_sensor_df(df)

    ts = pd.to_numeric(df["timestamp"]).to_numpy(dtype=np.float64)
    fs = 1.0 / float(np.median(np.diff(ts))) if len(ts) > 1 else 100.0

    acc = df[["acc_x", "acc_y", "acc_z"]].to_numpy(dtype=np.float32)
    gyro = df[["gyro_x", "gyro_y", "gyro_z"]].to_numpy(dtype=np.float32)
    grip = df["grip"].to_numpy(dtype=np.float32)

    return Recording(
        subject=subject,
        task=task,
        trial=trial,
        fs=float(round(fs, 2)),
        acc=acc,
        gyro=gyro,
        grip=grip,
        fall_onset=fall_onset,
        fall_impact=fall_impact,
    )


def write_live_sensor_csv(
    path: Path | str,
    rec: Recording,
    timestamps: Optional[Sequence[float] | np.ndarray] = None,
) -> Path:
    """Export a Recording to the standard live sensor CSV format."""
    path = Path(path)
    n = rec.n
    if timestamps is None:
        fs = rec.fs if rec.fs > 0 else 100.0
        ts = np.arange(n, dtype=np.float64) / fs
    else:
        ts = np.asarray(timestamps, dtype=np.float64)
        if len(ts) != n:
            raise ValueError(f"Timestamps length ({len(ts)}) does not match recording length ({n})")

    grip = rec.grip if rec.grip is not None else np.zeros(n, dtype=np.float32)

    df = pd.DataFrame(
        {
            "timestamp": ts,
            "acc_x": rec.acc[:, 0],
            "acc_y": rec.acc[:, 1],
            "acc_z": rec.acc[:, 2],
            "gyro_x": rec.gyro[:, 0],
            "gyro_y": rec.gyro[:, 1],
            "gyro_z": rec.gyro[:, 2],
            "grip": grip,
        },
        columns=list(LIVE_SENSOR_COLUMNS),
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path
