"""Supervised fraud-detection models with randomised hyper-parameter search.

Why these models (see documentation/methodology.md):
* Logistic Regression - interpretable, regulator-friendly baseline.
* Random Forest       - robust bagged trees, handles non-linear interactions.
* XGBoost             - gradient-boosted trees, state of the art on tabular fraud data.
Class imbalance is handled with class weights / scale_pos_weight (no synthetic
oversampling, which would distort calibrated probabilities used for risk tiers).
"""
from __future__ import annotations

import time

import numpy as np
from scipy.stats import loguniform, randint, uniform
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from src.common import get_logger
from src.model_evaluation.evaluate import best_f1_threshold, evaluate_binary

log = get_logger(__name__)


def candidate_models(seed: int, pos_weight: float, n_jobs: int = 2) -> dict:
    return {
        "logistic_regression": (
            Pipeline([("scale", StandardScaler()),
                      ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=seed))]),
            {"clf__C": loguniform(1e-3, 1e2)},
        ),
        "random_forest": (
            RandomForestClassifier(n_estimators=150, class_weight="balanced_subsample", n_jobs=n_jobs, random_state=seed),
            {"max_depth": randint(4, 16), "min_samples_leaf": randint(2, 30), "max_features": ["sqrt", 0.3, 0.5]},
        ),
        "xgboost": (
            XGBClassifier(n_estimators=200, tree_method="hist", eval_metric="aucpr", scale_pos_weight=pos_weight,
                          n_jobs=n_jobs, random_state=seed, verbosity=0),
            {"max_depth": randint(3, 8), "learning_rate": loguniform(0.02, 0.3),
             "subsample": uniform(0.6, 0.4), "colsample_bytree": uniform(0.6, 0.4), "min_child_weight": randint(1, 10)},
        ),
    }


def train_and_select(X_tr, y_tr, X_val, y_val, cfg: dict) -> dict:
    """Train every enabled model; tune on the training set (CV), pick threshold on validation."""
    seed = cfg["seed"]; t = cfg["tuning"]
    pos_weight = float((y_tr == 0).sum() / max((y_tr == 1).sum(), 1))
    out = {}
    for name, (est, space) in candidate_models(seed, pos_weight, t["n_jobs"]).items():
        if not cfg["models"].get(name, {}).get("enabled", True):
            continue
        t0 = time.perf_counter()
        if t["enabled"]:
            cv = StratifiedKFold(t["cv_folds"], shuffle=True, random_state=seed)
            search = RandomizedSearchCV(est, space, n_iter=t["n_iter"], scoring=t["scoring"], cv=cv,
                                        random_state=seed, n_jobs=1, refit=True)
            search.fit(X_tr, y_tr)
            model, params, cv_score = search.best_estimator_, search.best_params_, float(search.best_score_)
        else:
            model = est.fit(X_tr, y_tr); params, cv_score = {}, float("nan")
        secs = time.perf_counter() - t0
        thr = best_f1_threshold(y_val, model.predict_proba(X_val)[:, 1])
        out[name] = {"model": model, "params": {k: (v.item() if hasattr(v, "item") else v) for k, v in params.items()},
                     "cv_score": cv_score, "threshold": thr, "train_seconds": secs}
        log.info("trained %s in %.1fs (cv %s=%.4f, thr=%.3f)", name, secs, t["scoring"], cv_score, thr,
                 extra={"stage": "train", "model": name})
    return out


def score(model, X) -> np.ndarray:
    return model.predict_proba(X)[:, 1]


def evaluate_models(trained: dict, X_te, y_te) -> tuple[dict, dict]:
    results, scores = {}, {}
    for name, t in trained.items():
        s = score(t["model"], X_te)
        scores[name] = s
        results[name] = evaluate_binary(y_te, s, t["threshold"])
    return results, scores
