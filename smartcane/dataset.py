import numpy as np
import pandas as pd

from smartcane.demo_data import make_demo_data


def load_features_csv(path):
    df = pd.read_csv(path)
    needed = {"subject", "label"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(f"features csv is missing columns: {sorted(missing)}")
    feature_cols = [c for c in df.columns if c not in ("subject", "label", "t_start", "t_end", "task", "trial")]
    X = df[feature_cols].to_numpy(dtype=float)
    y = df["label"].to_numpy(dtype=int)
    groups = df["subject"].astype(str).to_numpy()
    return X, y, groups, feature_cols


def build_dataset(cfg):
    source = cfg["data"]["source"]
    if source == "demo":
        X, y, g = make_demo_data(seed=cfg.get("seed", 42))
        return X, y, g, [f"f{i}" for i in range(X.shape[1])]
    if source == "features_csv":
        return load_features_csv(cfg["data"]["features_csv"])
    raise ValueError(f"unknown data source: {source}")
