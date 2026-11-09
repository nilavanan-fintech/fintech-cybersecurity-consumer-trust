"""Risk classification: map fraud probability to an operational action tier."""
from __future__ import annotations

import numpy as np
import pandas as pd

TIERS = ["low", "medium", "high", "critical"]
ACTIONS = {"low": "allow", "medium": "step-up authentication", "high": "hold for manual review", "critical": "block + alert"}


def classify_risk(prob, tiers: dict) -> np.ndarray:
    prob = np.asarray(prob)
    out = np.full(prob.shape, "critical", dtype=object)
    out[prob < tiers["high"]] = "high"
    out[prob < tiers["medium"]] = "medium"
    out[prob < tiers["low"]] = "low"
    return out


def tier_summary(prob, y_true, amount, tiers: dict) -> pd.DataFrame:
    df = pd.DataFrame({"tier": classify_risk(prob, tiers), "fraud": np.asarray(y_true), "amount": np.asarray(amount)})
    g = df.groupby("tier").agg(transactions=("fraud", "size"), frauds=("fraud", "sum"), amount=("amount", "sum"))
    g = g.reindex(TIERS).fillna(0)
    g["observed_fraud_rate"] = g["frauds"] / g["transactions"].replace(0, np.nan)
    g["action"] = [ACTIONS[t] for t in g.index]
    return g.reset_index()
