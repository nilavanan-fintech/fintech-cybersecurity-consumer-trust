"""Unsupervised anomaly detection (no labels used for fitting).

* Isolation Forest (Liu et al., 2008) - random partitioning; anomalies isolate in few splits.
* Local Outlier Factor, novelty mode (Breunig et al., 2000) - density-based; fitted on a
  subsample because it is O(n^2).
Labels (`is_fraud` / `is_attack`) are used ONLY afterwards, to measure how well the
unsupervised scores recover known bad behaviour.
"""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.model_evaluation.evaluate import evaluate_binary


def fit_isolation_forest(X_train, contamination: float, seed: int):
    m = Pipeline([("scale", StandardScaler()),
                  ("iso", IsolationForest(n_estimators=200, contamination=contamination, random_state=seed, n_jobs=2))])
    m.fit(X_train)
    return m


def iso_scores(model, X) -> np.ndarray:
    """Higher = more anomalous."""
    return -model.score_samples(X)


def fit_lof(X_train, n_sample: int, n_neighbors: int, contamination: float, seed: int):
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(X_train), min(n_sample, len(X_train)), replace=False)
    m = Pipeline([("scale", StandardScaler()),
                  ("lof", LocalOutlierFactor(n_neighbors=n_neighbors, novelty=True, contamination=contamination, n_jobs=2))])
    m.fit(X_train.iloc[idx] if hasattr(X_train, "iloc") else X_train[idx])
    return m


def lof_scores(model, X) -> np.ndarray:
    return -model.score_samples(X)


def evaluate_unsupervised(model_scores_train, scores_test, y_test, contamination: float) -> dict:
    thr = float(np.quantile(model_scores_train, 1 - contamination))
    return evaluate_binary(y_test, scores_test, thr)
