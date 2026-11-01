import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import LeaveOneGroupOut


def confusion(y_true, y_pred):
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    return tp, fp, tn, fn


def count_alarm_events(y_true, y_pred):
    fp_flag = ((np.asarray(y_true) == 0) & (np.asarray(y_pred) == 1)).astype(int)
    if fp_flag.size == 0:
        return 0
    edges = np.diff(np.concatenate([[0], fp_flag]))
    return int((edges == 1).sum())


def safe_div(a, b):
    return float(a) / float(b) if b else float("nan")


def compute_metrics(y_true, y_pred, stride_sec):
    tp, fp, tn, fn = confusion(y_true, y_pred)
    normal_hours = (tn + fp) * stride_sec / 3600.0
    alarm_events = count_alarm_events(y_true, y_pred)
    sens = safe_div(tp, tp + fn)
    prec = safe_div(tp, tp + fp)
    f1 = safe_div(2 * prec * sens, prec + sens) if tp else (0.0 if (tp + fp + fn) else float("nan"))
    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "sensitivity": sens,
        "specificity": safe_div(tn, tn + fp),
        "precision": prec,
        "f1": f1,
        "normal_hours": normal_hours,
        "false_alarms_per_hour": safe_div(alarm_events, normal_hours),
        "false_alarm_windows_per_hour": safe_div(fp, normal_hours),
    }


def loso_evaluate(make_detector, X, y, groups, stride_sec):
    X = np.asarray(X)
    y = np.asarray(y).astype(int)
    groups = np.asarray(groups)
    per_subject = []
    pooled_true, pooled_pred = [], []
    pooled_alarm_events = 0
    for train_idx, test_idx in LeaveOneGroupOut().split(X, y, groups):
        det = make_detector()
        det.fit(X[train_idx], y[train_idx])
        pred = np.asarray(det.predict(X[test_idx])).astype(int)
        m = compute_metrics(y[test_idx], pred, stride_sec)
        m["subject"] = str(groups[test_idx][0])
        per_subject.append(m)
        pooled_true.append(y[test_idx])
        pooled_pred.append(pred)
        pooled_alarm_events += count_alarm_events(y[test_idx], pred)
    yt = np.concatenate(pooled_true)
    yp = np.concatenate(pooled_pred)
    pooled = compute_metrics(yt, yp, stride_sec)
    pooled["false_alarms_per_hour"] = safe_div(pooled_alarm_events, pooled["normal_hours"])
    df = pd.DataFrame(per_subject)
    summary = {}
    for col in ["sensitivity", "specificity", "precision", "f1", "false_alarms_per_hour"]:
        vals = df[col].to_numpy(dtype=float)
        summary[col + "_mean"] = float(np.nanmean(vals)) if np.isfinite(vals).any() else float("nan")
        summary[col + "_std"] = float(np.nanstd(vals)) if np.isfinite(vals).any() else float("nan")
    return {"pooled": pooled, "per_subject": per_subject, "summary": summary}


def write_results(results, out_dir, name):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / f"{name}.json", "w") as f:
        json.dump(results, f, indent=2, default=float)
    if isinstance(results, dict) and "per_subject" in results:
        pd.DataFrame(results["per_subject"]).to_csv(out / f"{name}_per_subject.csv", index=False)
    return out / f"{name}.json"


def results_table(named_results):
    rows = []
    for name, res in named_results.items():
        p = res["pooled"]
        s = res["summary"]
        rows.append({
            "model": name,
            "sensitivity": p["sensitivity"],
            "specificity": p["specificity"],
            "precision": p["precision"],
            "f1": p["f1"],
            "false_alarms_per_hour": p["false_alarms_per_hour"],
            "sens_mean_over_subjects": s["sensitivity_mean"],
            "fa_per_hour_mean_over_subjects": s["false_alarms_per_hour_mean"],
        })
    return pd.DataFrame(rows)
