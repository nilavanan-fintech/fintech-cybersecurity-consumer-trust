"""Data validation: returns structured check results (also exported as metrics)."""
from __future__ import annotations

import pandas as pd

from src.schema import AUTH_METHODS, CHANNELS, MERCHANT_CATEGORIES, TRANSACTION_COLUMNS


def _check(name: str, failed: int, total: int, detail: str = "") -> dict:
    return {"check": name, "passed": failed == 0, "failed_count": int(failed), "total": int(total), "detail": detail}


def validate_transactions(df: pd.DataFrame, cfg: dict | None = None) -> list[dict]:
    cfg = (cfg or {}).get("validation", {"max_missing_ratio": 0.02, "max_duplicate_ratio": 0.01, "min_rows": 1000})
    n = len(df)
    out = []
    missing_cols = [c for c in TRANSACTION_COLUMNS if c not in df.columns]
    out.append(_check("schema_columns_present", len(missing_cols), len(TRANSACTION_COLUMNS), ",".join(missing_cols)))
    if missing_cols:
        return out
    out.append(_check("min_rows", int(n < cfg["min_rows"]), 1, f"rows={n}"))
    miss = df[["amount", "timestamp", "customer_id", "channel"]].isna().any(axis=1).sum()
    out.append(_check("missing_ratio_within_limit", int(miss / n > cfg["max_missing_ratio"]), 1, f"{miss / n:.4%}"))
    out.append(_check("no_missing_amount", int(df["amount"].isna().sum()), n))
    dups = int(df.duplicated("transaction_id").sum())
    out.append(_check("duplicate_ratio_within_limit", int(dups / n > cfg["max_duplicate_ratio"]), 1, f"{dups / n:.4%}"))
    out.append(_check("no_duplicate_transaction_id", dups, n))
    out.append(_check("amount_positive", int((df["amount"].dropna() <= 0).sum()), n))
    out.append(_check("timestamp_parsable", int(pd.to_datetime(df["timestamp"], errors="coerce").isna().sum()), n))
    out.append(_check("ip_risk_in_unit_interval", int(((df["ip_risk_score"] < 0) | (df["ip_risk_score"] > 1)).sum()), n))
    out.append(_check("label_is_binary", int((~df["is_fraud"].isin([0, 1])).sum()), n))
    out.append(_check("channel_domain", int((~df["channel"].isin(CHANNELS)).sum()), n))
    out.append(_check("merchant_domain", int((~df["merchant_category"].isin(MERCHANT_CATEGORIES)).sum()), n))
    out.append(_check("auth_method_domain", int((~df["auth_method"].isin(AUTH_METHODS)).sum()), n))
    return out


def validation_pass_rate(checks: list[dict]) -> float:
    return sum(c["passed"] for c in checks) / max(len(checks), 1)
