"""Long-running service: runs the pipeline, exposes /metrics, then replays held-out data as a live stream.

The stream scores *held-out* synthetic transactions / security events with the trained champion
and anomaly models, so Prometheus counters reflect genuine model inference (precision/recall can
be derived from the outcome counters). It is a replay, not production traffic.
"""
from __future__ import annotations

import json
import os
import signal
import time

import joblib
import numpy as np
import pandas as pd

from src.common import ROOT, get_logger, load_settings, resolve
from src.feature_engineering.features import feature_names
from src.fraud_detection.risk import classify_risk
from src.metrics import exporter as mx
from src.pipeline import load_last_summary, run_pipeline

log = get_logger("worker")
_stop = False


def _sig(*_):
    global _stop
    _stop = True


def _artifacts_present(cfg) -> bool:
    meta = ROOT / cfg["paths"]["metadata"]
    return (meta / "champion.json").exists() and (meta / "last_run_summary.json").exists() and \
        (ROOT / cfg["paths"]["processed"] / "transactions_features.parquet").exists()


def main() -> None:
    cfg = load_settings()
    signal.signal(signal.SIGTERM, _sig); signal.signal(signal.SIGINT, _sig)
    port = int(os.environ.get("EXPORTER_PORT", cfg["exporter"]["port"]))
    mx.start_exporter(port)           # health endpoint is live immediately; fintech_pipeline_ready=0 until built
    log.info("metrics exporter listening on :%d", port, extra={"stage": "worker"})

    force = os.environ.get("FORCE_RETRAIN", "0") == "1"
    if force or not _artifacts_present(cfg):
        run_pipeline(cfg, use_db=True)
    else:
        summary = load_last_summary(cfg)
        mx.publish_summary(summary)
        mx.PIPELINE_RUNS.labels("restored").inc()
        log.info("re-published metrics from saved run %s", summary["run_id"], extra={"stage": "worker"})

    if not cfg["stream"]["enabled"]:
        while not _stop:
            time.sleep(1)
        return

    meta = json.loads((ROOT / cfg["paths"]["metadata"] / "champion.json").read_text())
    champion = meta["champion"]
    model = joblib.load(ROOT / cfg["paths"]["models"] / f"{champion}.joblib")
    thr = json.loads((ROOT / cfg["paths"]["metadata"] / f"{champion}.json").read_text())["threshold"]
    sec_model = joblib.load(ROOT / cfg["paths"]["models"] / "security_isolation_forest.joblib")
    tx = pd.read_parquet(ROOT / cfg["paths"]["processed"] / "transactions_features.parquet")
    tx = tx[tx["split"] == "test"].reset_index(drop=True)
    ev = pd.read_parquet(ROOT / cfg["paths"]["processed"] / "security_events_scored.parquet")
    ev = ev[ev["split"] == "replay"].reset_index(drop=True)
    sec_thr = meta["security_threshold"]
    fcols = [c for c in ev.columns if c.startswith("f_")]
    sec_cols = [c[2:] for c in fcols]

    bs, interval = cfg["stream"]["batch_size"], cfg["stream"]["interval_seconds"]
    i = j = 0
    log.info("stream started: champion=%s batch=%d every %ss", champion, bs, interval, extra={"stage": "stream", "model": champion})
    while not _stop:
        t0 = time.perf_counter()
        b = tx.iloc[[(i + k) % len(tx) for k in range(bs)]]
        i = (i + bs) % len(tx)
        with mx.INFER_LATENCY.labels(champion).time():
            p = model.predict_proba(b[feature_names()])[:, 1]
        pred = (p >= thr).astype(int)
        y = b["is_fraud"].to_numpy()
        for (ch, pr), n in pd.Series(list(zip(b["channel"], pred))).value_counts().items():
            mx.STREAM_TXN.labels(ch, "fraud" if pr else "legit").inc(int(n))
        mx.STREAM_OUTCOME.labels("tp").inc(int(((pred == 1) & (y == 1)).sum()))
        mx.STREAM_OUTCOME.labels("fp").inc(int(((pred == 1) & (y == 0)).sum()))
        mx.STREAM_OUTCOME.labels("fn").inc(int(((pred == 0) & (y == 1)).sum()))
        mx.STREAM_OUTCOME.labels("tn").inc(int(((pred == 0) & (y == 0)).sum()))
        amt = b["amount"].to_numpy()
        mx.STREAM_AMOUNT.labels("total").inc(float(amt.sum()))
        mx.STREAM_AMOUNT.labels("flagged").inc(float(amt[pred == 1].sum()))
        mx.STREAM_AMOUNT.labels("fraud_missed").inc(float(amt[(pred == 0) & (y == 1)].sum()))
        mx.STREAM_AMOUNT.labels("fraud_caught").inc(float(amt[(pred == 1) & (y == 1)].sum()))
        for tier, n in pd.Series(classify_risk(p, cfg["risk_tiers"])).value_counts().items():
            mx.STREAM_RISK.labels(tier).inc(int(n))

        e = ev.iloc[[(j + k) % len(ev) for k in range(max(1, bs // 2))]]
        j = (j + len(e)) % len(ev)
        sc = -sec_model.score_samples(e[fcols].set_axis(sec_cols, axis=1))
        mx.STREAM_ANOMALY.inc(int((sc >= sec_thr).sum()))
        for (et, sev, bl), n in e.groupby(["event_type", "severity", "blocked"]).size().items():
            mx.STREAM_SEC.labels(et, sev, str(bool(bl)).lower()).inc(int(n))
        mx.STREAM_BATCH_SECONDS.set(time.time())

        time.sleep(max(0.0, interval - (time.perf_counter() - t0)))
    log.info("worker stopped", extra={"stage": "worker"})


if __name__ == "__main__":
    main()
