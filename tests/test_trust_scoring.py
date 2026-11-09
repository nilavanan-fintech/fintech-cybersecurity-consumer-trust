import numpy as np
import pandas as pd
import pytest

from src.model_evaluation import statistics as st
from src.schema import SURVEY_ITEMS
from src.trust_scoring.scoring import (
    consumer_trust_index, cronbach_alpha, platform_security_index, reliability_report, reverse_code, score_respondents,
)


def uniform_survey(value):
    d = {"respondent_id": ["a", "b"]}
    d.update({q: [value, value] for q in SURVEY_ITEMS})
    return pd.DataFrame(d)


def test_score_bounds_and_reverse_coding(cfg):
    best = uniform_survey(5); best["q12"] = 1      # max trust: agree with everything, no worry about hacking
    worst = uniform_survey(1); worst["q12"] = 5
    assert score_respondents(best, cfg)["trust_score"].eq(100).all()
    assert score_respondents(worst, cfg)["trust_score"].eq(0).all()
    assert reverse_code(best)["q12"].eq(5).all()


def test_segments(cfg):
    s = score_respondents(uniform_survey(3), cfg)       # q12=3 reverse -> 3 => 50
    assert s["trust_score"].round(1).eq(50.0).all()
    assert (s["segment"] == "Moderate").all()


def test_weights_sum_to_one(cfg):
    assert sum(cfg["trust"]["weights"].values()) == pytest.approx(1.0)


def test_cronbach_alpha_known():
    rng = np.random.default_rng(0)
    base = rng.normal(size=500)
    items = pd.DataFrame({f"i{k}": base + rng.normal(0, 0.3, 500) for k in range(4)})
    assert cronbach_alpha(items) > 0.9
    noise = pd.DataFrame(rng.normal(size=(500, 4)))
    assert abs(cronbach_alpha(noise)) < 0.2


def test_synthetic_survey_internal_consistency(survey):
    assert reliability_report(survey)["overall"] > 0.7


def test_indices():
    assert platform_security_index(1.0, 0.0, 1.0, 1.0) == pytest.approx(100)
    assert platform_security_index(0.0, 0.2, 0.0, 0.0) == pytest.approx(0)
    assert consumer_trust_index(80, 60, 0.6) == pytest.approx(72)


def test_ols_recovers_coefficients():
    rng = np.random.default_rng(1)
    X = pd.DataFrame(rng.normal(size=(2000, 2)), columns=["a", "b"])
    y = 3 + 2 * X["a"] - 1 * X["b"] + rng.normal(0, 0.1, 2000)
    res = st.ols(X, y)
    assert res.loc["a", "coef"] == pytest.approx(2, abs=0.05)
    assert res.loc["b", "coef"] == pytest.approx(-1, abs=0.05)
    assert res.attrs["r2"] > 0.99


def test_survey_driver_directions(survey, cfg):
    full = survey.merge(score_respondents(survey, cfg)[["respondent_id", "trust_score"]], on="respondent_id")
    corr = st.correlation_with_p(full, "trust_score", ["uses_mfa", "experienced_fraud"]).set_index("variable")
    assert corr.loc["uses_mfa", "r"] > 0 and corr.loc["experienced_fraud", "r"] < 0


def test_hypothesis_helpers():
    a, b = np.arange(100), np.arange(100) + 50
    assert st.mann_whitney(a, b)["p_value"] < 0.001
    y = np.array([1, 1, 0, 0, 1, 0, 1, 0] * 20)
    assert st.mcnemar(y, y, 1 - y)["p_value"] < 0.001
