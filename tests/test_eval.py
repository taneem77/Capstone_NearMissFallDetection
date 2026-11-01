import numpy as np

from smartcane.demo_data import make_demo_data
from smartcane.detectors.normal_only import NormalOnlyDetector
from smartcane.eval import compute_metrics, count_alarm_events, loso_evaluate


def test_metrics_basic():
    y_true = np.array([0, 0, 0, 1, 1, 0])
    y_pred = np.array([0, 1, 0, 1, 0, 0])
    m = compute_metrics(y_true, y_pred, stride_sec=1.0)
    assert (m["tp"], m["fp"], m["tn"], m["fn"]) == (1, 1, 3, 1)
    assert m["sensitivity"] == 0.5
    assert abs(m["normal_hours"] - 4 / 3600) < 1e-12


def test_alarm_events_merge_consecutive_windows():
    y_true = np.zeros(8, dtype=int)
    y_pred = np.array([0, 1, 1, 1, 0, 0, 1, 0])
    assert count_alarm_events(y_true, y_pred) == 2


def test_normal_only_ignores_near_miss_labels_in_training():
    X, y, _ = make_demo_data(n_subjects=3, windows_per_subject=200)
    det = NormalOnlyDetector().fit(X, y)
    assert det.scaler.n_samples_seen_ == int((y == 0).sum())


def test_loso_runs_one_fold_per_subject():
    X, y, g = make_demo_data(n_subjects=5, windows_per_subject=150)
    res = loso_evaluate(lambda: NormalOnlyDetector(), X, y, g, stride_sec=1.0)
    assert len(res["per_subject"]) == 5
    assert res["pooled"]["normal_hours"] > 0
