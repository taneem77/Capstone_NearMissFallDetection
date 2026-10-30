"""RQ1 baselines: IMU-only threshold vs random forest, leave-one-subject-out.

    python -m smartcane.rq1_baselines --sensors smartcane\\data --labels smartcane\\data --cache smartcane\\cache

Swap `loso()` for Pratham's eval.py once it exists -- same inputs (wins, y, subjects).
"""
from __future__ import annotations

import argparse

import numpy as np

from .detectors import RandomForestDetector, ThresholdDetector
from .sources import KFallSource
from .windows import build_dataset, labels, subjects


def metrics(y, pred, n_neg_hours):
    tp = int(((pred == 1) & (y == 1)).sum()); fn = int(((pred == 0) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum()); tn = int(((pred == 0) & (y == 0)).sum())
    return dict(sens=tp / max(tp + fn, 1), spec=tn / max(fp + tn, 1),
                fa_per_hr=fp / n_neg_hours if n_neg_hours else float("nan"),
                tp=tp, fn=fn, fp=fp, tn=tn)


def loso(make_detector, wins, y, subj, stride_s):
    pred = np.zeros(len(y), dtype=int)
    folds = np.unique(subj)
    for i, s in enumerate(folds, 1):
        te = subj == s
        det = make_detector().fit([w for w, t in zip(wins, te) if not t], y[~te])
        pred[te] = det.predict([w for w, t in zip(wins, te) if t])
        print(f"  fold {i}/{len(folds)} ({s}) done", flush=True)
    # windows overlap, so "hours of negative data" = n_neg * stride, not n_neg * window
    hours = (y == 0).sum() * stride_s / 3600
    return metrics(y, pred, hours)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sensors", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--cache", default=None)
    ap.add_argument("--win", type=float, default=1.0)
    ap.add_argument("--stride", type=float, default=0.25)
    ap.add_argument("--subjects", nargs="*")
    a = ap.parse_args()

    src = KFallSource(a.sensors, a.labels, subjects=a.subjects, cache_dir=a.cache)
    wins = build_dataset(src.recordings(), win_s=a.win, stride_s=a.stride)
    y, subj = labels(wins), subjects(wins)
    print(f"{len(wins)} windows | {int(y.sum())} event | {len(np.unique(subj))} subjects")

    for name, mk in [("threshold (peak jerk)", lambda: ThresholdDetector()),
                     ("random forest", lambda: RandomForestDetector(n_estimators=60))]:
        print(name, flush=True)
        m = loso(mk, wins, y, subj, a.stride)
        print(f"{name:24s} sens={m['sens']:.3f} spec={m['spec']:.3f} FA/hr={m['fa_per_hr']:.1f}")


if __name__ == "__main__":
    main()