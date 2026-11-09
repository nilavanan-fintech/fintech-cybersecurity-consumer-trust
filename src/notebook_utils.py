"""Thin loaders so notebooks stay short and always read the pipeline's real artefacts."""
from __future__ import annotations

import json

import joblib
import pandas as pd

from src.common import ROOT, load_settings

CFG = load_settings()
P = ROOT / "data" / "processed"


def _need(path):
    if not path.exists():
        raise FileNotFoundError(f"{path} missing - run the pipeline first: `make pipeline` (or `docker compose up --build`).")
    return path


def load_raw() -> pd.DataFrame:
    return pd.read_csv(_need(ROOT / "data" / "raw" / "transactions_raw.csv"))


def load_clean() -> pd.DataFrame:
    return pd.read_parquet(_need(ROOT / "data" / "interim" / "transactions_clean.parquet"))


def load_features() -> pd.DataFrame:
    return pd.read_parquet(_need(P / "transactions_features.parquet"))


def load_events() -> pd.DataFrame:
    return pd.read_parquet(_need(P / "security_events_scored.parquet"))


def load_survey() -> pd.DataFrame:
    return pd.read_csv(_need(ROOT / "survey" / "survey_data.csv"))


def load_trust() -> pd.DataFrame:
    return pd.read_parquet(_need(P / "trust_scores.parquet"))


def load_summary() -> dict:
    return json.loads(_need(ROOT / "models" / "model_metadata" / "last_run_summary.json").read_text())


def load_model(name: str):
    return joblib.load(_need(ROOT / "models" / "trained" / f"{name}.joblib"))


def split_xy(df: pd.DataFrame):
    from src.feature_engineering.features import feature_names
    cols = feature_names()
    out = {}
    for s in ("train", "validation", "test"):
        d = df[df["split"] == s]
        out[s] = (d[cols], d["is_fraud"].to_numpy(), d)
    return out
