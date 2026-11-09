"""Statistical analysis helpers (descriptive, hypothesis tests, correlations)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def descriptive(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    d = df[cols].describe().T
    d["skew"] = df[cols].skew()
    d["kurtosis"] = df[cols].kurt()
    return d


def correlation(df: pd.DataFrame, cols: list[str], method: str = "spearman") -> pd.DataFrame:
    return df[cols].corr(method=method)


def correlation_with_p(df: pd.DataFrame, x: str, ys: list[str], method: str = "spearman") -> pd.DataFrame:
    fn = stats.spearmanr if method == "spearman" else stats.pearsonr
    rows = []
    for y in ys:
        r, p = fn(df[x], df[y])
        rows.append({"variable": y, "r": float(r), "p_value": float(p)})
    return pd.DataFrame(rows).sort_values("r", key=abs, ascending=False)


def mann_whitney(a, b) -> dict:
    u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
    # rank-biserial effect size
    r = 1 - 2 * u / (len(a) * len(b))
    return {"U": float(u), "p_value": float(p), "rank_biserial": float(r), "n_a": len(a), "n_b": len(b)}


def chi_square(df: pd.DataFrame, a: str, b: str) -> dict:
    ct = pd.crosstab(df[a], df[b])
    chi2, p, dof, _ = stats.chi2_contingency(ct)
    n = ct.values.sum()
    cramers_v = float(np.sqrt(chi2 / (n * (min(ct.shape) - 1)))) if min(ct.shape) > 1 else float("nan")
    return {"chi2": float(chi2), "dof": int(dof), "p_value": float(p), "cramers_v": cramers_v}


def kruskal(df: pd.DataFrame, value: str, group: str) -> dict:
    groups = [g[value].to_numpy() for _, g in df.groupby(group, observed=True)]
    h, p = stats.kruskal(*groups)
    return {"H": float(h), "p_value": float(p), "groups": len(groups)}


def mcnemar(y_true, pred_a, pred_b) -> dict:
    """McNemar test (with continuity correction) on paired classifier errors."""
    y_true = np.asarray(y_true)
    a_ok, b_ok = np.asarray(pred_a) == y_true, np.asarray(pred_b) == y_true
    b, c = int((a_ok & ~b_ok).sum()), int((~a_ok & b_ok).sum())
    if b + c == 0:
        return {"b": b, "c": c, "chi2": 0.0, "p_value": 1.0}
    chi2 = (abs(b - c) - 1) ** 2 / (b + c)
    return {"b": b, "c": c, "chi2": float(chi2), "p_value": float(stats.chi2.sf(chi2, 1))}


def ols(X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    """Ordinary least squares with classical standard errors on standardised predictors."""
    Xs = (X - X.mean()) / X.std(ddof=0)
    A = np.column_stack([np.ones(len(Xs)), Xs.to_numpy()])
    beta, *_ = np.linalg.lstsq(A, y.to_numpy(), rcond=None)
    resid = y.to_numpy() - A @ beta
    dof = len(y) - A.shape[1]
    sigma2 = resid @ resid / dof
    se = np.sqrt(np.diag(sigma2 * np.linalg.inv(A.T @ A)))
    t = beta / se
    p = 2 * stats.t.sf(np.abs(t), dof)
    r2 = 1 - (resid @ resid) / ((y - y.mean()) @ (y - y.mean()))
    out = pd.DataFrame({"coef": beta, "std_err": se, "t": t, "p_value": p}, index=["intercept", *X.columns])
    out.attrs["r2"] = float(r2)
    return out
