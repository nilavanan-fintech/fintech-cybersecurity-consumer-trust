"""Generate the synthetic datasets only (no training).

    python infrastructure/scripts/generate_synthetic_data.py [--seed 42] [--out data/synthetic]
Writes transactions, security events and a pseudonymised, k-anonymous survey sample.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.common import load_settings  # noqa: E402
from src.data_collection.synthetic import generate_security_events, generate_survey, generate_transactions  # noqa: E402
from src.preprocessing.anonymize import enforce_k_anonymity  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int)
    ap.add_argument("--out", default="data/synthetic")
    ap.add_argument("--sample-rows", type=int, default=0, help="also write a small head sample CSV (for git)")
    a = ap.parse_args()
    cfg = load_settings(); s = cfg["synthetic"]; seed = a.seed if a.seed is not None else cfg["seed"]
    out = ROOT / a.out; out.mkdir(parents=True, exist_ok=True)
    tx = generate_transactions(s["n_transactions"], s["n_customers"], s["fraud_rate"], s["days"], seed, s["end_date"], s["dirty_fraction"])
    ev = generate_security_events(s["n_security_events"], s["days"], seed, s["end_date"])
    sv = enforce_k_anonymity(generate_survey(s["n_survey_respondents"], seed), cfg["trust"]["k_anonymity"])
    tx.to_parquet(out / "transactions_synthetic.parquet", index=False)
    ev.to_parquet(out / "security_events_synthetic.parquet", index=False)
    sv.to_csv(ROOT / "survey" / "survey_data.csv", index=False)
    if a.sample_rows:
        tx.head(a.sample_rows).to_csv(out / "sample_transactions.csv", index=False)
        ev.head(a.sample_rows).to_csv(out / "sample_security_events.csv", index=False)
    print(f"transactions={len(tx)} (fraud rate {tx.is_fraud.mean():.3%}) events={len(ev)} survey={len(sv)} seed={seed}")


if __name__ == "__main__":
    main()
