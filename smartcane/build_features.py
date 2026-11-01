"""KFall recordings -> window features -> data/features.csv (the input to RQ4).

    python -m smartcane.build_features --config config.yaml

Output columns: subject, task, trial, t_start, label, <feature columns...>
Rows are in time order within each subject, as eval.py expects.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from .features import extract, feature_names
from .windows import Window


def windows_to_frame(wins: list[Window], use_grip: bool = False) -> pd.DataFrame:
    cols = feature_names(use_grip=use_grip)
    if not wins:
        return pd.DataFrame(columns=["subject", "task", "trial", "t_start", "label", *cols])
    X = np.nan_to_num(np.vstack([extract(w, use_grip=use_grip) for w in wins]),
                      nan=0.0, posinf=0.0, neginf=0.0)
    meta = pd.DataFrame({
        "subject": [w.subject for w in wins],
        "task": [w.task for w in wins],
        "trial": [w.trial for w in wins],
        "t_start": [w.start / w.fs for w in wins],
        "label": [w.label for w in wins],
    })
    df = pd.concat([meta, pd.DataFrame(X, columns=cols)], axis=1)
    # subject-major, then recording order, then time
    return df.sort_values(["subject", "task", "trial", "t_start"], kind="stable").reset_index(drop=True)


def main():
    import yaml
    from .sources import KFallSource
    from .windows import build_dataset

    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--subjects", nargs="*", help="limit to e.g. SA06 SA07 for a quick test")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    cfg = yaml.safe_load(open(a.config))
    k, w = cfg["data"]["kfall"], cfg["window"]
    out = Path(a.out or cfg["data"]["features_csv"])

    src = KFallSource(k["sensors"], k["labels"], subjects=a.subjects, cache_dir=k.get("cache"))
    wins = build_dataset(src.recordings(), win_s=w["length_sec"], stride_s=w["stride_sec"])
    df = windows_to_frame(wins)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    if df.empty or df.label.sum() == 0:
        print("WARNING: no event windows found. Check that the label .xlsx files are in "
              f"{k['labels']} and named SAxx_label.xlsx; RQ4 needs positives.")
    print(f"{len(df)} windows | {int(df.label.sum())} event | {df.subject.nunique()} subjects -> {out}")


if __name__ == "__main__":
    main()
