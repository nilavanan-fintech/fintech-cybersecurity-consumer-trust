"""Consumer Trust Score (CTS) and Platform Security Index (PSI).

CTS (0-100, per respondent): weighted mean of five survey dimensions, each rescaled
from the 1-5 Likert range, with q12 reverse-coded.
PSI (0-100, per platform/run): objective security performance measured by the pipeline
(detection recall, 1-FPR, threat-block rate, data-validation pass rate).
Consumer Trust Index (CTI) = a*mean(CTS) + (1-a)*PSI  - a *proposed* composite, not a
validated psychometric instrument (see documentation/methodology.md, Limitations).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.schema import SURVEY_DIMENSIONS, SURVEY_ITEMS


def reverse_code(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for q, (_, _, rev) in SURVEY_ITEMS.items():
        if rev:
            out[q] = 6 - out[q]
    return out


def cronbach_alpha(items: pd.DataFrame) -> float:
    k = items.shape[1]
    if k < 2:
        return float("nan")
    var_sum = items.var(axis=0, ddof=1).sum()
    total_var = items.sum(axis=1).var(ddof=1)
    return float(k / (k - 1) * (1 - var_sum / total_var))


def dimension_scores(df: pd.DataFrame) -> pd.DataFrame:
    r = reverse_code(df)
    out = pd.DataFrame(index=df.index)
    for dim in SURVEY_DIMENSIONS:
        qs = [q for q, (d, _, _) in SURVEY_ITEMS.items() if d == dim]
        out[dim] = (r[qs].mean(axis=1) - 1) / 4 * 100
    return out


def score_respondents(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    w = cfg["trust"]["weights"]
    dims = dimension_scores(df)
    cts = sum(dims[d] * w[d] for d in SURVEY_DIMENSIONS) / sum(w.values())
    seg = cfg["trust"]["segments"]
    out = pd.concat([df[["respondent_id"]], dims], axis=1)
    out["trust_score"] = cts.round(2)
    out["segment"] = np.where(cts < seg["low"], "Low", np.where(cts >= seg["high"], "High", "Moderate"))
    return out


def reliability_report(df: pd.DataFrame) -> dict:
    r = reverse_code(df)
    rep = {"overall": cronbach_alpha(r[list(SURVEY_ITEMS)])}
    for dim in SURVEY_DIMENSIONS:
        qs = [q for q, (d, _, _) in SURVEY_ITEMS.items() if d == dim]
        rep[dim] = cronbach_alpha(r[qs]) if len(qs) > 1 else float("nan")
    return rep


def platform_security_index(recall: float, fpr: float, block_rate: float, validation_pass: float) -> float:
    comps = [recall, 1 - min(fpr * 10, 1.0), block_rate, validation_pass]   # FPR scaled: 10 % FPR -> 0 credit
    return float(100 * np.mean(comps))


def consumer_trust_index(mean_cts: float, psi: float, a: float) -> float:
    return float(a * mean_cts + (1 - a) * psi)
