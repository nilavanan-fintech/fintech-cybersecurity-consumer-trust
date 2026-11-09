import numpy as np
import pytest

from src.anomaly_detection.detectors import fit_isolation_forest, iso_scores
from src.feature_engineering.features import build_features, chronological_split
from src.fraud_detection.risk import classify_risk, tier_summary
from src.fraud_detection.train import evaluate_models, train_and_select
from src.model_evaluation.evaluate import best_f1_threshold, evaluate_binary
from src.preprocessing.cleaning import clean_transactions


def test_evaluate_binary_known_values():
    y = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    s = np.array([.1, .2, .6, .3, .9, .8, .4, .7])
    m = evaluate_binary(y, s, 0.5)
    assert (m["tp"], m["fp"], m["fn"], m["tn"]) == (3, 1, 1, 3)
    assert m["precision"] == pytest.approx(0.75) and m["recall"] == pytest.approx(0.75)
    assert m["false_positive_rate"] == pytest.approx(0.25)
    assert m["accuracy"] == pytest.approx(0.75)
    assert m["roc_auc"] == pytest.approx(15 / 16)      # 15 of 16 positive/negative pairs ranked correctly


def test_threshold_selection_beats_default_on_imbalance():
    rng = np.random.default_rng(0)
    y = (rng.random(5000) < 0.02).astype(int)
    s = np.clip(0.15 + 0.5 * y + rng.normal(0, 0.1, 5000), 0, 1)
    t = best_f1_threshold(y, s)
    assert evaluate_binary(y, s, t)["f1"] >= evaluate_binary(y, s, 0.5)["f1"]


def test_risk_tiers():
    tiers = {"low": 0.05, "medium": 0.3, "high": 0.7}
    out = classify_risk([0.01, 0.1, 0.5, 0.9], tiers)
    assert list(out) == ["low", "medium", "high", "critical"]
    df = tier_summary(np.array([0.01, 0.9, 0.9]), np.array([0, 1, 1]), np.array([10, 20, 30]), tiers)
    assert df.set_index("tier").loc["critical", "frauds"] == 2


@pytest.fixture(scope="module")
def split(tx):
    clean, _ = clean_transactions(tx)
    X, y = build_features(clean), clean["is_fraud"].to_numpy()
    tr, va, te = chronological_split(len(clean), 0.7, 0.15)
    return X.iloc[tr], y[tr], X.iloc[va], y[va], X.iloc[te], y[te]


def test_models_learn_better_than_chance_and_unsupervised_is_above_random(split, cfg):
    X_tr, y_tr, X_va, y_va, X_te, y_te = split
    c = dict(cfg); c["tuning"] = {**cfg["tuning"], "n_iter": 2, "cv_folds": 2, "n_jobs": 1}
    trained = train_and_select(X_tr, y_tr, X_va, y_va, c)
    assert set(trained) == {"logistic_regression", "random_forest", "xgboost"}
    results, _ = evaluate_models(trained, X_te, y_te)
    base_rate = y_te.mean()
    for name, r in results.items():
        assert r["roc_auc"] > 0.8, name
        assert r["pr_auc"] > 3 * base_rate, name
    iso = fit_isolation_forest(X_tr, 0.03, seed=1)
    from sklearn.metrics import roc_auc_score
    assert roc_auc_score(y_te, iso_scores(iso, X_te)) > 0.6
