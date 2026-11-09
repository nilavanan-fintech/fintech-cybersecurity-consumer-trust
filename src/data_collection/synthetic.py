"""Isolated synthetic data generators (transactions, security events, survey).

All data is generated locally from a seeded RNG - no real customer data and no
live systems are touched. Fraud / attack patterns are *stylised* versions of
those described in the fraud-detection literature; signatures are expressed
only 75 % of the time so classes overlap and the task is not trivially separable.
"""
from __future__ import annotations

import hashlib
import os

import numpy as np
import pandas as pd

from src.schema import (
    AUTH_METHODS, COUNTRIES, EVENT_TYPES_ATTACK, EVENT_TYPES_BENIGN, FRAUD_PATTERNS,
    HOME_COUNTRIES, MERCHANT_CATEGORIES, SERVICES, SURVEY_ITEMS,
)


def _end_date(end_date) -> pd.Timestamp:
    if end_date in (None, "auto"):
        return pd.Timestamp.now("UTC").tz_localize(None).normalize()
    return pd.Timestamp(end_date)


def generate_transactions(n: int = 60000, n_customers: int = 5000, fraud_rate: float = 0.02,
                          days: int = 90, seed: int = 42, end_date="auto",
                          dirty_fraction: float = 0.004) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    end = _end_date(end_date)
    start = end - pd.Timedelta(days=days)

    cust = pd.DataFrame({
        "customer_id": [f"C{i:05d}" for i in range(n_customers)],
        "home_country": rng.choice(HOME_COUNTRIES, n_customers, p=[.70, .08, .07, .05, .05, .05]),
        "account_age_days": np.clip(rng.gamma(2.0, 400, n_customers), 5, 5000).round().astype(int),
        "mu": rng.normal(np.log(45), 0.6, n_customers),
    })
    c = cust.iloc[rng.integers(0, n_customers, n)].reset_index(drop=True)

    h = np.arange(24)
    w = 0.3 + np.exp(-((h - 13) ** 2) / (2 * 4.5 ** 2)) + 0.6 * np.exp(-((h - 19) ** 2) / (2 * 2.5 ** 2))
    day = rng.integers(0, days, n)
    hour = rng.choice(24, n, p=w / w.sum())
    sec = rng.integers(0, 3600, n)

    channel = rng.choice(["mobile_app", "web", "pos", "atm"], n, p=[.45, .25, .25, .05]).astype(object)
    device = np.where(channel == "mobile_app", rng.choice(["android", "ios"], n, p=[.65, .35]),
             np.where(channel == "web", rng.choice(["desktop", "android", "ios"], n, p=[.7, .2, .1]),
             np.where(channel == "pos", "pos_terminal", "atm_terminal"))).astype(object)
    cats = [m for m in MERCHANT_CATEGORIES if m != "cash_withdrawal"]
    cat_p = np.array([.22, .14, .06, .07, .08, .1, .09, .08, .05, .11])
    merchant = rng.choice(cats, n, p=cat_p / cat_p.sum()).astype(object)
    merchant[channel == "atm"] = "cash_withdrawal"

    amount = np.exp(c["mu"].to_numpy() + 0.7 * rng.standard_normal(n))
    country = c["home_country"].to_numpy().astype(object).copy()
    foreign = rng.random(n) < 0.03
    country[foreign] = rng.choice(COUNTRIES, foreign.sum())
    new_device = (rng.random(n) < 0.05).astype(int)
    ip_risk = rng.beta(2, 10, n)
    velocity = rng.poisson(0.4, n)
    age = c["account_age_days"].to_numpy().copy()
    auth = rng.choice(AUTH_METHODS, n, p=[.35, .30, .30, .05]).astype(object)

    # --- fraud labels -------------------------------------------------------
    mult = 1.0 + 1.0 * (age < 90) + 0.5 * np.isin(channel, ["web", "mobile_app"])
    p = fraud_rate * mult / mult.mean()
    fraud = rng.random(n) < p
    fi = np.where(fraud)[0]
    pat = rng.choice(FRAUD_PATTERNS, len(fi), p=[.40, .25, .15, .20])
    pattern = np.full(n, "none", dtype=object)
    pattern[fi] = pat
    strong = rng.random(n) < 0.75

    def sub(name):
        return fi[(pat == name) & strong[fi]]

    i = sub("account_takeover")
    new_device[i] = (rng.random(len(i)) < 0.85).astype(int)
    country[i[rng.random(len(i)) < 0.5]] = "NG"
    ip_risk[i] = rng.beta(5, 3, len(i))
    amount[i] *= rng.uniform(2, 6, len(i))
    hour[i[rng.random(len(i)) < 0.5]] = rng.integers(0, 6)
    velocity[i] = rng.poisson(1.5, len(i))

    i = sub("card_testing")
    amount[i] = rng.uniform(0.5, 12, len(i))
    velocity[i] = 3 + rng.poisson(4, len(i))
    channel[i] = "web"; device[i] = "desktop"; merchant[i] = "digital_goods"
    auth[i] = "password"; ip_risk[i] = rng.beta(4, 4, len(i))

    i = sub("synthetic_identity")
    age[i] = rng.integers(1, 45, len(i))
    amount[i] *= rng.uniform(3, 8, len(i))
    auth[i] = "password"; new_device[i] = 1

    i = sub("social_engineering")
    amount[i] *= rng.uniform(3, 8, len(i))
    merchant[i] = "transfers"; auth[i] = "otp"; channel[i] = "mobile_app"
    device[i] = rng.choice(["android", "ios"], len(i))

    ts = start + pd.to_timedelta(day * 86400 + hour * 3600 + sec, unit="s")
    df = pd.DataFrame({
        "customer_id": c["customer_id"], "timestamp": ts, "amount": amount.round(2),
        "merchant_category": merchant, "channel": channel, "device_type": device,
        "country": country, "home_country": c["home_country"], "is_new_device": new_device,
        "ip_risk_score": ip_risk.round(4), "velocity_1h": velocity, "account_age_days": age,
        "auth_method": auth, "is_fraud": fraud.astype(int), "fraud_pattern": pattern,
    }).sort_values("timestamp").reset_index(drop=True)
    df.insert(0, "transaction_id", [f"T{i:07d}" for i in range(len(df))])

    # --- deliberately dirty rows so validation / cleaning have real work -----
    k = max(1, int(dirty_fraction * len(df)))
    df.loc[rng.choice(len(df), k, replace=False), "amount"] = np.nan
    neg = rng.choice(len(df), max(1, k // 3), replace=False)
    df.loc[neg, "amount"] = -df.loc[neg, "amount"].abs()
    dup = df.sample(max(1, k // 2), random_state=seed)
    return pd.concat([df, dup], ignore_index=True)


def generate_security_events(n: int = 25000, days: int = 90, seed: int = 42, end_date="auto") -> pd.DataFrame:
    rng = np.random.default_rng(seed + 1)
    end = _end_date(end_date)
    start = end - pd.Timedelta(days=days)
    total_s = days * 86400
    n_att = int(0.18 * n)

    # attack campaigns: dense bursts of one dominant attack type
    n_camp = 6
    c_start = rng.uniform(0, total_s - 12 * 3600, n_camp)
    c_len = rng.uniform(3, 10, n_camp) * 3600
    c_type = rng.choice(EVENT_TYPES_ATTACK, n_camp)
    in_camp = rng.random(n_att) < 0.6
    cid = rng.integers(0, n_camp, n_att)
    t_att = np.where(in_camp, c_start[cid] + rng.random(n_att) * c_len[cid], rng.uniform(0, total_s, n_att))
    typ_att = np.where(in_camp & (rng.random(n_att) < 0.8), c_type[cid], rng.choice(EVENT_TYPES_ATTACK, n_att))

    n_ben = n - n_att
    h = np.arange(24)
    w = 0.3 + np.exp(-((h - 13) ** 2) / (2 * 4.5 ** 2))
    t_ben = rng.integers(0, days, n_ben) * 86400 + rng.choice(24, n_ben, p=w / w.sum()) * 3600 + rng.integers(0, 3600, n_ben)
    typ_ben = rng.choice(EVENT_TYPES_BENIGN, n_ben, p=[.6, .1, .3])

    t = np.concatenate([t_att, t_ben]); etype = np.concatenate([typ_att, typ_ben]).astype(object)
    is_att = np.concatenate([np.ones(n_att, int), np.zeros(n_ben, int)])
    sev_base = {"brute_force": 2, "credential_stuffing": 3, "phishing_click": 2, "malware_alert": 3,
                "api_abuse": 2, "data_exfiltration": 4, "ddos_probe": 2,
                "login_success": 1, "password_reset": 1, "api_call": 1}
    sev = np.clip(np.array([sev_base[e] for e in etype]) + (rng.random(n) < 0.15) * 1, 1, 4)
    sev_name = np.array(["", "low", "medium", "high", "critical"])[sev]
    block_p = {"brute_force": .95, "credential_stuffing": .85, "phishing_click": .70, "malware_alert": .80,
               "api_abuse": .80, "data_exfiltration": .60, "ddos_probe": .90}
    bp = np.array([block_p.get(e, 0.01) for e in etype])
    failed = np.where(np.isin(etype, ["brute_force"]), 5 + rng.poisson(25, n),
             np.where(np.isin(etype, ["credential_stuffing"]), 3 + rng.poisson(12, n), rng.poisson(0.3, n)))
    bytes_out = np.exp(rng.normal(8, 1, n)) * np.where(etype == "data_exfiltration", 50, 1)
    resp = np.exp(rng.normal(-1.5, 0.5, n)) * np.where(is_att == 1, 1.8, 1)
    risky = ["RU", "CN", "NG", "BR"]
    src = np.where((is_att == 1) & (rng.random(n) < 0.6), rng.choice(risky, n), rng.choice(COUNTRIES[:6], n))

    df = pd.DataFrame({
        "timestamp": start + pd.to_timedelta(t, unit="s"), "event_type": etype, "severity": sev_name,
        "source_country": src, "target_service": rng.choice(SERVICES, n),
        "blocked": rng.random(n) < bp, "response_time_s": resp.round(4), "bytes_out": bytes_out.round(1),
        "failed_attempts": failed, "is_attack": is_att,
    }).sort_values("timestamp").reset_index(drop=True)
    df.insert(0, "event_id", [f"E{i:07d}" for i in range(len(df))])
    return df


def pseudonymise(i: int, salt: str | None = None) -> str:
    salt = salt if salt is not None else os.environ.get("SURVEY_SALT", "dev-only-salt")
    return hashlib.sha256(f"{salt}:{i}".encode()).hexdigest()[:12]


def generate_survey(n: int = 400, seed: int = 42, salt: str | None = None) -> pd.DataFrame:
    """SYNTHETIC respondents drawn from a latent-factor model (for pipeline demonstration).

    Replace with real, consented responses collected via survey/questionnaire.md.
    """
    rng = np.random.default_rng(seed + 2)
    literacy = rng.normal(0, 1, n)
    mfa = (rng.random(n) < 1 / (1 + np.exp(-(0.3 + 0.8 * literacy)))).astype(int)
    fraud_exp = (rng.random(n) < 0.18).astype(int)
    trust_lat = 0.35 * literacy + 0.45 * mfa - 0.7 * fraud_exp + rng.normal(0, 0.8, n)
    rows = {"respondent_id": [pseudonymise(i, salt) for i in range(n)]}
    for q, (dim, _, rev) in SURVEY_ITEMS.items():
        load = {"perceived_security": 0.9, "privacy_assurance": 0.7, "transparency": 0.6,
                "reliability": 0.5, "behavioural_intent": 0.8}[dim]
        raw = 3.2 + load * trust_lat * (-1 if rev else 1) + rng.normal(0, 0.7, n)
        rows[q] = np.clip(np.rint(raw), 1, 5).astype(int)
    df = pd.DataFrame(rows)
    df["age_band"] = rng.choice(["18-24", "25-34", "35-44", "45-54", "55+"], n, p=[.22, .34, .22, .13, .09])
    df["education"] = rng.choice(["secondary", "undergraduate", "postgraduate"], n, p=[.2, .55, .25])
    df["usage_frequency"] = rng.choice(["daily", "weekly", "monthly"], n, p=[.45, .4, .15])
    df["uses_mfa"] = mfa
    df["experienced_fraud"] = fraud_exp
    df["digital_literacy"] = np.clip(np.rint(3 + literacy * 0.9), 1, 5).astype(int)
    return df
