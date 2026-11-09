"""Privacy-conscious survey handling: pseudonymisation, generalisation, k-anonymity."""
from __future__ import annotations

import hashlib
import os

import pandas as pd

QUASI_IDENTIFIERS = ["age_band", "education", "usage_frequency"]
FREE_TEXT_HINTS = ("name", "email", "phone", "address", "comment", "ip")


def pseudonymise_ids(ids, salt: str | None = None) -> list[str]:
    salt = salt if salt is not None else os.environ.get("SURVEY_SALT", "dev-only-salt")
    return [hashlib.sha256(f"{salt}:{i}".encode()).hexdigest()[:12] for i in ids]


def drop_direct_identifiers(df: pd.DataFrame) -> pd.DataFrame:
    drop = [c for c in df.columns if any(h in c.lower() for h in FREE_TEXT_HINTS) and c != "respondent_id"]
    return df.drop(columns=drop)


def k_anonymity(df: pd.DataFrame, k: int = 5, quasi: list[str] | None = None) -> dict:
    quasi = [q for q in (quasi or QUASI_IDENTIFIERS) if q in df.columns]
    sizes = df.groupby(quasi, observed=True).size()
    return {"k_required": k, "min_group_size": int(sizes.min()), "groups_below_k": int((sizes < k).sum()),
            "satisfied": bool(sizes.min() >= k), "quasi_identifiers": quasi}


def enforce_k_anonymity(df: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    """Suppress (drop) respondents belonging to quasi-identifier groups smaller than k."""
    sizes = df.groupby(QUASI_IDENTIFIERS, observed=True)["respondent_id"].transform("size")
    return df[sizes >= k].reset_index(drop=True)
