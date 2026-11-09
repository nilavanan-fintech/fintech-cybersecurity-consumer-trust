import numpy as np
import pandas as pd

from src.feature_engineering.features import build_features, chronological_split, feature_names
from src.preprocessing.anonymize import enforce_k_anonymity, k_anonymity, pseudonymise_ids
from src.preprocessing.cleaning import clean_transactions


def test_cleaning_removes_invalid_rows(tx):
    clean, rep = clean_transactions(tx)
    assert clean["transaction_id"].is_unique
    assert (clean["amount"] > 0).all() and clean["amount"].notna().all()
    assert rep["rows_in"] == len(tx)
    assert rep["rows_out"] == len(clean) == rep["rows_in"] - rep["duplicates_removed"] - rep["invalid_removed"]
    assert clean["timestamp"].is_monotonic_increasing


def test_features_have_stable_schema_and_no_nans(tx):
    clean, _ = clean_transactions(tx)
    X = build_features(clean)
    assert list(X.columns) == feature_names()
    assert not X.isna().any().any()
    assert np.isfinite(X.to_numpy(dtype=float)).all()


def test_history_features_do_not_leak_future(tx):
    """Changing a LATER transaction must not change an EARLIER row's features."""
    clean, _ = clean_transactions(tx)
    base = build_features(clean)
    mod = clean.copy()
    mod.loc[mod.index[-1], "amount"] = 1e6
    changed = build_features(mod)
    pd.testing.assert_frame_equal(base.iloc[:-1], changed.iloc[:-1])


def test_chronological_split_is_ordered():
    tr, va, te = chronological_split(1000, 0.7, 0.15)
    assert (tr.start, tr.stop, va.start, va.stop, te.start, te.stop) == (0, 700, 700, 850, 850, 1000)


def test_survey_privacy(survey):
    assert survey["respondent_id"].is_unique and survey["respondent_id"].str.len().eq(12).all()
    assert "name" not in " ".join(survey.columns).lower()
    ids_a = pseudonymise_ids(range(5), salt="x"); ids_b = pseudonymise_ids(range(5), salt="y")
    assert ids_a != ids_b                                   # salt matters
    out = enforce_k_anonymity(survey, k=5)
    assert k_anonymity(out, k=5)["satisfied"]
