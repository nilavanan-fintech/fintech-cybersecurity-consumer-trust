"""Optional public benchmark: ULB/Worldline 'Credit Card Fraud Detection' dataset.

The file is NOT redistributed here. To use it, download `creditcard.csv` from
https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud (Database Contents
License / ODbL; cite Dal Pozzolo et al., 2015) and place it in data/external/.
If present, the pipeline benchmarks the same models on it (see src/pipeline.py).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_creditcard(external_dir: Path) -> pd.DataFrame | None:
    f = Path(external_dir) / "creditcard.csv"
    if not f.exists():
        return None
    df = pd.read_csv(f)
    required = {"Time", "Amount", "Class"}
    if not required.issubset(df.columns):
        raise ValueError(f"{f} does not look like the ULB credit card dataset (missing {required - set(df.columns)})")
    return df.sort_values("Time").reset_index(drop=True)
