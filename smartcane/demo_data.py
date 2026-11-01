import numpy as np


def make_demo_data(n_subjects=12, windows_per_subject=600, n_features=8, seed=42):
    rng = np.random.default_rng(seed)
    X_all, y_all, g_all = [], [], []
    for s in range(n_subjects):
        offset = rng.normal(0, 0.4, size=n_features)
        scale = rng.uniform(0.8, 1.3)
        X = rng.normal(0, 1, size=(windows_per_subject, n_features)) * scale + offset
        y = np.zeros(windows_per_subject, dtype=int)
        n_events = rng.integers(8, 14)
        starts = rng.choice(np.arange(5, windows_per_subject - 5), size=n_events, replace=False)
        for st in starts:
            length = rng.integers(1, 3)
            shift = rng.normal(2.2, 0.5, size=n_features)
            X[st:st + length] += shift
            y[st:st + length] = 1
        X_all.append(X)
        y_all.append(y)
        g_all.append(np.full(windows_per_subject, f"S{s + 1:02d}"))
    return np.vstack(X_all), np.concatenate(y_all), np.concatenate(g_all)
