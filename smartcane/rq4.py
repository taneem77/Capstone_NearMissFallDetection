import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from smartcane.detectors.normal_only import NormalOnlyDetector
from smartcane.eval import loso_evaluate, results_table


class SupervisedRF:
    name = "supervised_rf"

    def __init__(self, seed=42, n_estimators=100):
        self.seed = seed
        self.model = RandomForestClassifier(
            n_estimators=n_estimators, class_weight="balanced", random_state=self.seed, n_jobs=-1
        )

    def fit(self, X, y):
        self.model.fit(X, y)
        return self

    def predict(self, X):
        return self.model.predict(X).astype(int)


class SubsampledFit:
    def __init__(self, make_inner, pos_frac=1.0, neg_frac=1.0, seed=42):
        self.make_inner = make_inner
        self.pos_frac = pos_frac
        self.neg_frac = neg_frac
        self.seed = seed
        self.inner = None

    def fit(self, X, y):
        rng = np.random.default_rng(self.seed)
        y = np.asarray(y).astype(int)
        pos = np.where(y == 1)[0]
        neg = np.where(y == 0)[0]
        n_pos = max(2, int(round(len(pos) * self.pos_frac))) if len(pos) else 0
        n_neg = max(10, int(round(len(neg) * self.neg_frac)))
        keep_pos = rng.choice(pos, size=min(n_pos, len(pos)), replace=False) if n_pos else np.array([], dtype=int)
        keep_neg = rng.choice(neg, size=min(n_neg, len(neg)), replace=False)
        keep = np.sort(np.concatenate([keep_pos, keep_neg]))
        self.inner = self.make_inner()
        self.inner.fit(np.asarray(X)[keep], y[keep])
        return self

    def predict(self, X):
        return self.inner.predict(X)


def run_rq4(X, y, groups, cfg):
    seed = cfg.get("seed", 42)
    stride = cfg["window"]["stride_sec"]
    rq = cfg["rq4"]

    def make_sup():
        return SupervisedRF(seed=seed, n_estimators=rq.get("supervised_trees", 100))

    def make_norm():
        return NormalOnlyDetector(method=rq["normal_only_method"], fp_quantile=rq["fp_quantile"], seed=seed)

    headline = {
        "supervised_rf": loso_evaluate(make_sup, X, y, groups, stride),
        "normal_only": loso_evaluate(make_norm, X, y, groups, stride),
    }

    sup_rows = []
    for frac in rq["pos_fractions"]:
        res = loso_evaluate(
            lambda f=frac: SubsampledFit(make_sup, pos_frac=f, neg_frac=1.0, seed=seed),
            X, y, groups, stride,
        )
        p = res["pooled"]
        sup_rows.append({
            "labeled_near_miss_fraction": frac,
            "sensitivity": p["sensitivity"],
            "false_alarms_per_hour": p["false_alarms_per_hour"],
            "f1": p["f1"],
        })

    norm_rows = []
    for frac in rq["neg_fractions"]:
        res = loso_evaluate(
            lambda f=frac: SubsampledFit(make_norm, pos_frac=1.0, neg_frac=f, seed=seed),
            X, y, groups, stride,
        )
        p = res["pooled"]
        norm_rows.append({
            "normal_data_fraction": frac,
            "sensitivity": p["sensitivity"],
            "false_alarms_per_hour": p["false_alarms_per_hour"],
            "f1": p["f1"],
        })

    return {
        "headline": headline,
        "headline_table": results_table(headline),
        "supervised_label_sweep": pd.DataFrame(sup_rows),
        "normal_only_data_sweep": pd.DataFrame(norm_rows),
    }
