"""Glue test: Recording -> windows -> features -> csv -> RQ4 eval, end to end on synthetic IMU."""
import numpy as np

from smartcane.build_features import windows_to_frame
from smartcane.dataset import load_features_csv
from smartcane.detectors.normal_only import NormalOnlyDetector
from smartcane.eval import loso_evaluate
from smartcane.io import Recording
from smartcane.windows import build_dataset


def _rec(subject, seed, fall):
    rng = np.random.default_rng(seed)
    n, fs = 1000, 100.0
    acc = rng.normal(0, 0.3, (n, 3)); acc[:, 2] += 9.8
    gyro = rng.normal(0, 5, (n, 3))
    on = im = None
    if fall:
        acc[500:540] += rng.normal(0, 12, (40, 3))
        on, im = 501, 541
    return Recording(subject, 20 if fall else 1, 1, fs, acc, gyro, None, on, im)


def test_features_csv_roundtrip_and_loso(tmp_path):
    recs = [_rec(f"SA{s:02d}", s * 10 + f, f) for s in range(1, 5) for f in (0, 1)]
    wins = build_dataset(recs, win_s=1.0, stride_s=0.25)
    df = windows_to_frame(wins)
    assert {"subject", "label", "t_start"} <= set(df.columns)
    assert df.label.isin([0, 1]).all() and df.label.sum() > 0
    p = tmp_path / "features.csv"; df.to_csv(p, index=False)
    X, y, g, names = load_features_csv(p)
    assert X.shape[1] == len(names) and "trial" not in names and "task" not in names
    res = loso_evaluate(lambda: NormalOnlyDetector(), X, y, g, stride_sec=0.25)
    assert len(res["per_subject"]) == 4
