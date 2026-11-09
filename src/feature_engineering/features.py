"""Leakage-safe feature engineering for transactions and security events."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.schema import AUTH_METHODS, CHANNELS, DEVICE_TYPES, MERCHANT_CATEGORIES

NUMERIC_FEATURES = [
    "log_amount", "hour", "day_of_week", "is_night", "is_weekend", "is_new_device", "is_foreign",
    "ip_risk_score", "velocity_1h", "log_account_age", "is_new_account", "cust_txn_count_prior",
    "amount_to_cust_avg_ratio", "log_secs_since_last", "new_device_x_foreign", "night_x_high_ratio",
    "high_risk_ip",
]
CATEGORICAL = {"channel": CHANNELS, "merchant_category": MERCHANT_CATEGORIES,
               "auth_method": AUTH_METHODS, "device_type": DEVICE_TYPES}


def feature_names() -> list[str]:
    return NUMERIC_FEATURES + [f"{c}__{v}" for c, vals in CATEGORICAL.items() for v in vals]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return a numeric feature frame aligned with df's index.

    Customer-history features use ONLY earlier transactions (cumulative sums minus
    the current row), so the model never sees information from the future.
    Input must be sorted by timestamp.
    """
    ts = pd.to_datetime(df["timestamp"])
    f = pd.DataFrame(index=df.index)
    f["log_amount"] = np.log1p(df["amount"])
    f["hour"] = ts.dt.hour
    f["day_of_week"] = ts.dt.day_of_week
    f["is_night"] = ts.dt.hour.between(0, 5).astype(int)
    f["is_weekend"] = (ts.dt.day_of_week >= 5).astype(int)
    f["is_new_device"] = df["is_new_device"].astype(int)
    f["is_foreign"] = (df["country"] != df["home_country"]).astype(int)
    f["ip_risk_score"] = df["ip_risk_score"]
    f["velocity_1h"] = df["velocity_1h"]
    f["log_account_age"] = np.log1p(df["account_age_days"])
    f["is_new_account"] = (df["account_age_days"] < 60).astype(int)

    g = df.groupby("customer_id", sort=False)
    prior_n = g.cumcount()
    prior_sum = g["amount"].cumsum() - df["amount"]
    # fallback for a customer's first transaction: mean of all PRIOR transactions (never future rows);
    # for the very first row of the dataset the transaction's own amount is used (ratio = 1)
    n_all = np.arange(len(df))
    global_prior = ((df["amount"].cumsum() - df["amount"]) / np.where(n_all == 0, np.nan, n_all)).fillna(df["amount"])
    prior_avg = (prior_sum / prior_n.replace(0, np.nan)).fillna(global_prior)
    f["cust_txn_count_prior"] = prior_n
    f["amount_to_cust_avg_ratio"] = (df["amount"] / prior_avg).clip(upper=50)
    last = ts.groupby(df["customer_id"], sort=False).shift(1)
    secs = (ts - last).dt.total_seconds().fillna(30 * 86400).clip(lower=0)
    f["log_secs_since_last"] = np.log1p(secs)

    f["new_device_x_foreign"] = f["is_new_device"] * f["is_foreign"]
    f["night_x_high_ratio"] = f["is_night"] * (f["amount_to_cust_avg_ratio"] > 3).astype(int)
    f["high_risk_ip"] = (f["ip_risk_score"] > 0.5).astype(int)

    for col, values in CATEGORICAL.items():
        for v in values:
            f[f"{col}__{v}"] = (df[col] == v).astype(int)
    return f[feature_names()]


def chronological_split(n: int, train: float, val: float) -> tuple[slice, slice, slice]:
    a, b = int(n * train), int(n * (train + val))
    return slice(0, a), slice(a, b), slice(b, n)


def build_security_features(ev: pd.DataFrame) -> pd.DataFrame:
    ts = pd.to_datetime(ev["timestamp"])
    sev = ev["severity"].map({"low": 1, "medium": 2, "high": 3, "critical": 4}).fillna(1)
    f = pd.DataFrame({
        "failed_attempts": ev["failed_attempts"],
        "log_bytes_out": np.log1p(ev["bytes_out"]),
        "response_time_s": ev["response_time_s"],
        "severity_num": sev,
        "hour": ts.dt.hour,
        "risky_source": ev["source_country"].isin(["RU", "CN", "NG", "BR"]).astype(int),
        "blocked": ev["blocked"].astype(int),
    }, index=ev.index)
    return f
