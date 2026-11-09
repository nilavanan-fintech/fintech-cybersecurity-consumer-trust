"""Cleaning / preprocessing of raw transaction and survey data."""
from __future__ import annotations

import hashlib

import pandas as pd


def clean_transactions(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Return (clean_df, report). The report records every row removed and why."""
    n0 = len(df)
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.drop_duplicates("transaction_id", keep="first")
    n_dup = n0 - len(df)
    bad = df["amount"].isna() | (df["amount"] <= 0) | df["timestamp"].isna()
    n_bad = int(bad.sum())
    df = df[~bad].copy()
    df["ip_risk_score"] = df["ip_risk_score"].clip(0, 1)
    for col in ("channel", "merchant_category", "auth_method", "device_type", "country", "home_country"):
        df[col] = df[col].fillna("unknown")
    df["velocity_1h"] = df["velocity_1h"].fillna(0).astype(int)
    df = df.sort_values("timestamp").reset_index(drop=True)
    report = {"rows_in": n0, "duplicates_removed": n_dup, "invalid_removed": n_bad, "rows_out": len(df)}
    return df, report


def frame_hash(df: pd.DataFrame) -> str:
    """Stable content hash used in model metadata for provenance."""
    h = pd.util.hash_pandas_object(df.reset_index(drop=True), index=False).values
    return hashlib.sha256(h.tobytes()).hexdigest()[:16]
