import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM


class NormalOnlyDetector:
    name = "normal_only"

    def __init__(self, method="iforest", fp_quantile=0.99, seed=42):
        self.method = method
        self.fp_quantile = fp_quantile
        self.seed = seed
        self.scaler = StandardScaler()
        self.model = None
        self.threshold = None

    def _build(self):
        if self.method == "ocsvm":
            return OneClassSVM(kernel="rbf", gamma="scale", nu=0.05)
        return IsolationForest(n_estimators=200, random_state=self.seed, n_jobs=-1)

    def fit(self, X, y=None):
        X = np.asarray(X, dtype=float)
        if y is not None:
            X = X[np.asarray(y).astype(int) == 0]
        Xs = self.scaler.fit_transform(X)
        self.model = self._build().fit(Xs)
        train_scores = -self.model.score_samples(Xs)
        self.threshold = float(np.quantile(train_scores, self.fp_quantile))
        return self

    def score(self, X):
        Xs = self.scaler.transform(np.asarray(X, dtype=float))
        return -self.model.score_samples(Xs)

    def predict(self, X):
        return (self.score(X) > self.threshold).astype(int)
