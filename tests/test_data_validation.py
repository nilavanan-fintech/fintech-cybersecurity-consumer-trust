import numpy as np

from src.preprocessing.validation import validate_transactions, validation_pass_rate


def by_name(checks):
    return {c["check"]: c for c in checks}


def test_dirty_synthetic_data_is_detected(tx, cfg):
    checks = by_name(validate_transactions(tx, cfg))
    assert not checks["no_missing_amount"]["passed"]          # NaNs were injected on purpose
    assert not checks["no_duplicate_transaction_id"]["passed"]
    assert not checks["amount_positive"]["passed"]
    assert checks["schema_columns_present"]["passed"]
    assert checks["label_is_binary"]["passed"]


def test_missing_column_short_circuits(tx, cfg):
    checks = validate_transactions(tx.drop(columns=["amount"]), cfg)
    assert checks[0]["check"] == "schema_columns_present" and not checks[0]["passed"]
    assert len(checks) == 1


def test_pass_rate_bounds(tx, cfg):
    r = validation_pass_rate(validate_transactions(tx, cfg))
    assert 0.0 < r < 1.0


def test_domain_violation_flagged(tx, cfg):
    bad = tx.copy()
    bad.loc[bad.index[:5], "channel"] = "carrier_pigeon"
    assert not by_name(validate_transactions(bad, cfg))["channel_domain"]["passed"]
    bad = tx.copy(); bad.loc[bad.index[:3], "ip_risk_score"] = 7.0
    assert by_name(validate_transactions(bad, cfg))["ip_risk_in_unit_interval"]["failed_count"] == 3


def test_synthetic_generation_is_reproducible():
    from src.data_collection.synthetic import generate_transactions
    a = generate_transactions(2000, 300, 0.02, 10, seed=3, end_date="2025-01-31")
    b = generate_transactions(2000, 300, 0.02, 10, seed=3, end_date="2025-01-31")
    assert a.equals(b)
    c = generate_transactions(2000, 300, 0.02, 10, seed=4, end_date="2025-01-31")
    assert not np.allclose(a["amount"].fillna(0).head(100), c["amount"].fillna(0).head(100))
