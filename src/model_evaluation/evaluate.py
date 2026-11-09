"""Binary-classification evaluation, plotting and threshold selection."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, average_precision_score, confusion_matrix, f1_score, precision_recall_curve,
    precision_score, recall_score, roc_auc_score, roc_curve,
)


def best_f1_threshold(y_true, scores) -> float:
    p, r, t = precision_recall_curve(y_true, scores)
    f1 = 2 * p[:-1] * r[:-1] / np.clip(p[:-1] + r[:-1], 1e-12, None)
    return float(t[int(np.nanargmax(f1))]) if len(t) else 0.5


def evaluate_binary(y_true, scores, threshold: float) -> dict:
    y_true = np.asarray(y_true)
    pred = (np.asarray(scores) >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    both = len(np.unique(y_true)) == 2
    return {
        "threshold": float(threshold),
        "accuracy": float(accuracy_score(y_true, pred)),
        "precision": float(precision_score(y_true, pred, zero_division=0)),
        "recall": float(recall_score(y_true, pred, zero_division=0)),
        "f1": float(f1_score(y_true, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, scores)) if both else float("nan"),
        "pr_auc": float(average_precision_score(y_true, scores)) if both else float("nan"),
        "false_positive_rate": float(fp / max(fp + tn, 1)),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }


def bootstrap_ci(y_true, scores, metric=roc_auc_score, n_boot: int = 300, seed: int = 0, alpha: float = 0.05):
    rng = np.random.default_rng(seed)
    y_true, scores = np.asarray(y_true), np.asarray(scores)
    vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(y_true), len(y_true))
        if y_true[idx].min() == y_true[idx].max():
            continue
        vals.append(metric(y_true[idx], scores[idx]))
    return float(np.quantile(vals, alpha / 2)), float(np.quantile(vals, 1 - alpha / 2))


def comparison_table(results: dict[str, dict]) -> pd.DataFrame:
    cols = ["accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc", "false_positive_rate", "tp", "fp", "fn", "tn"]
    return pd.DataFrame(results).T[cols].sort_values("pr_auc", ascending=False)


def save_evaluation_plots(y_true, scores_by_model: dict, results: dict, out_dir: Path) -> list[Path]:
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    sns.set_theme(style="whitegrid")

    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    for name, s in scores_by_model.items():
        fpr, tpr, _ = roc_curve(y_true, s)
        ax[0].plot(fpr, tpr, label=f"{name} (AUC {results[name]['roc_auc']:.3f})")
        p, r, _ = precision_recall_curve(y_true, s)
        ax[1].plot(r, p, label=f"{name} (AP {results[name]['pr_auc']:.3f})")
    ax[0].plot([0, 1], [0, 1], "k--", lw=.8); ax[0].set(xlabel="False positive rate", ylabel="True positive rate", title="ROC curves")
    ax[1].axhline(np.mean(y_true), color="k", ls="--", lw=.8); ax[1].set(xlabel="Recall", ylabel="Precision", title="Precision-recall curves")
    ax[0].legend(fontsize=8); ax[1].legend(fontsize=8)
    fig.tight_layout(); p = out_dir / "roc_pr_curves.png"; fig.savefig(p, dpi=130); plt.close(fig); paths.append(p)

    n = len(results)
    fig, axes = plt.subplots(1, n, figsize=(3.6 * n, 3.4))
    for ax_, (name, r) in zip(np.atleast_1d(axes), results.items()):
        cm = np.array([[r["tn"], r["fp"]], [r["fn"], r["tp"]]])
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False, ax=ax_,
                    xticklabels=["Legit", "Fraud"], yticklabels=["Legit", "Fraud"])
        ax_.set(title=f"{name}\nFPR={r['false_positive_rate']:.3%}", xlabel="Predicted", ylabel="Actual")
    fig.tight_layout(); p = out_dir / "confusion_matrices.png"; fig.savefig(p, dpi=130); plt.close(fig); paths.append(p)
    return paths


def save_feature_importance(model, feature_names, out_dir: Path, name: str, top: int = 15):
    est = model.steps[-1][1] if hasattr(model, "steps") else model
    imp = getattr(est, "feature_importances_", None)
    if imp is None and hasattr(est, "coef_"):
        imp = np.abs(est.coef_).ravel()
    if imp is None:
        return None
    s = pd.Series(imp, index=feature_names).sort_values(ascending=False).head(top)[::-1]
    fig, ax = plt.subplots(figsize=(6.5, 5))
    s.plot.barh(ax=ax, color="#2a6f97"); ax.set(title=f"Top features - {name}", xlabel="importance")
    fig.tight_layout(); p = Path(out_dir) / f"feature_importance_{name}.png"; fig.savefig(p, dpi=130); plt.close(fig)
    return p
