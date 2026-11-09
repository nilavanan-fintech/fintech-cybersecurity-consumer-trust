"""Prometheus instrumentation. Every value is computed by the pipeline - nothing hardcoded.

Metric families (prefix `fintech_`):
  pipeline_*     stage duration / rows / status / readiness / last success
  data_*         validation checks, missing/duplicate ratios
  txn_*          transaction analytics from the processed dataset
  security_*     security event analytics + anomaly detector output
  model_*        per-model evaluation metrics, confusion cells, training time, latency
  trust_*        survey-derived trust scores and platform security index
  stream_*       live replay of held-out transactions through the champion model
"""
from __future__ import annotations

import time
from contextlib import contextmanager

from prometheus_client import Counter, Gauge, Histogram, start_http_server

# ---- pipeline -------------------------------------------------------------
PIPELINE_READY = Gauge("fintech_pipeline_ready", "1 once artefacts are built and metrics published")
PIPELINE_RUNS = Counter("fintech_pipeline_runs_total", "Pipeline executions", ["status"])
PIPELINE_LAST_SUCCESS = Gauge("fintech_pipeline_last_success_timestamp_seconds", "Unix time of last successful run")
PIPELINE_RUN_SECONDS = Gauge("fintech_pipeline_run_duration_seconds", "Duration of the last full run")
STAGE_SECONDS = Gauge("fintech_pipeline_stage_duration_seconds", "Duration of last execution of a stage", ["stage"])
STAGE_STATUS = Gauge("fintech_pipeline_stage_success", "1 if the last execution of the stage succeeded", ["stage"])
STAGE_ROWS = Gauge("fintech_pipeline_stage_rows", "Rows output by a stage", ["stage"])
STAGE_ERRORS = Counter("fintech_pipeline_stage_errors_total", "Stage failures", ["stage"])
DB_WRITE_FAILURES = Counter("fintech_db_write_failures_total", "Failed PostgreSQL writes", ["table"])
DB_ROWS_WRITTEN = Gauge("fintech_db_rows_written", "Rows written to PostgreSQL in last run", ["table"])

# ---- data quality -----------------------------------------------------------
VALIDATION_CHECK = Gauge("fintech_data_validation_check_passed", "1 if the validation check passed", ["check"])
VALIDATION_FAILED_ROWS = Gauge("fintech_data_validation_failed_rows", "Rows violating a validation check", ["check"])
VALIDATION_PASS_RATE = Gauge("fintech_data_validation_pass_rate", "Share of validation checks passed")
CLEANING_ROWS = Gauge("fintech_data_cleaning_rows", "Row accounting during cleaning", ["kind"])

# ---- transactions -------------------------------------------------------------
TXN_COUNT = Gauge("fintech_txn_dataset_transactions", "Transactions in processed dataset", ["channel"])
TXN_FRAUD_COUNT = Gauge("fintech_txn_dataset_frauds", "Labelled frauds in processed dataset", ["channel"])
TXN_FRAUD_RATE = Gauge("fintech_txn_dataset_fraud_rate", "Overall labelled fraud rate")
TXN_AMOUNT = Gauge("fintech_txn_dataset_amount_total", "Total transaction value", ["kind"])
FRAUD_RATE_CATEGORY = Gauge("fintech_txn_fraud_rate_by_category", "Fraud rate per merchant category", ["merchant_category"])
FRAUD_RATE_HOUR = Gauge("fintech_txn_fraud_rate_by_hour", "Fraud rate per hour of day", ["hour"])
FRAUD_BY_PATTERN = Gauge("fintech_txn_frauds_by_pattern", "Frauds per generative pattern", ["pattern"])
AMOUNT_QUANTILE = Gauge("fintech_txn_amount_quantile", "Amount quantiles", ["class", "quantile"])

# ---- security ---------------------------------------------------------------
SEC_EVENTS = Gauge("fintech_security_dataset_events", "Security events in dataset", ["event_type", "severity"])
SEC_BLOCK_RATE = Gauge("fintech_security_block_rate", "Share of attack events blocked")
SEC_SOURCE = Gauge("fintech_security_attacks_by_source_country", "Attack events by source country", ["country"])
SEC_ANOMALY_AUC = Gauge("fintech_security_anomaly_roc_auc", "ROC-AUC of unsupervised detector vs known attacks")
SEC_ANOMALIES = Gauge("fintech_security_anomalies_flagged", "Events flagged anomalous by Isolation Forest")
SEC_MTTR = Gauge("fintech_security_mean_response_seconds", "Mean response time", ["kind"])

# ---- models -----------------------------------------------------------------
MODEL_METRIC = Gauge("fintech_model_metric", "Test-set evaluation metric", ["model", "metric"])
MODEL_CONFUSION = Gauge("fintech_model_confusion", "Confusion-matrix cell counts (test set)", ["model", "cell"])
MODEL_TRAIN_SECONDS = Gauge("fintech_model_training_seconds", "Training + tuning wall time", ["model"])
MODEL_THRESHOLD = Gauge("fintech_model_threshold", "Decision threshold chosen on validation", ["model"])
MODEL_CV = Gauge("fintech_model_cv_score", "Best cross-validated tuning score", ["model"])
CHAMPION = Gauge("fintech_model_champion", "1 for the champion model", ["model"])
RISK_TIER = Gauge("fintech_risk_tier_transactions", "Test transactions per risk tier", ["tier"])
RISK_TIER_RATE = Gauge("fintech_risk_tier_observed_fraud_rate", "Observed fraud rate per risk tier", ["tier"])
INFER_LATENCY = Histogram("fintech_model_inference_seconds", "Batch inference latency", ["model"],
                          buckets=(.001, .005, .01, .025, .05, .1, .25, .5, 1, 2.5))

# ---- trust ------------------------------------------------------------------
TRUST_MEAN = Gauge("fintech_trust_score_mean", "Mean Consumer Trust Score (0-100)")
TRUST_DIM = Gauge("fintech_trust_dimension_mean", "Mean score per trust dimension (0-100)", ["dimension"])
TRUST_SEGMENT = Gauge("fintech_trust_segment_respondents", "Respondents per trust segment", ["segment"])
TRUST_PSI = Gauge("fintech_trust_platform_security_index", "Platform Security Index (0-100)")
TRUST_CTI = Gauge("fintech_trust_consumer_trust_index", "Combined Consumer Trust Index (0-100)")
TRUST_N = Gauge("fintech_trust_survey_respondents", "Survey respondents analysed")
TRUST_ALPHA = Gauge("fintech_trust_cronbach_alpha", "Cronbach's alpha", ["scale"])
TRUST_CORR = Gauge("fintech_trust_driver_correlation", "Spearman rho of trust score with driver", ["driver"])
TRUST_ITEM = Gauge("fintech_trust_item_mean", "Mean Likert response per item (1-5)", ["item"])
TRUST_GROUP = Gauge("fintech_trust_score_by_group", "Mean trust score by respondent group", ["group", "value"])
KANON = Gauge("fintech_trust_k_anonymity_min_group", "Smallest quasi-identifier group in published survey data")

# ---- live stream --------------------------------------------------------------
STREAM_TXN = Counter("fintech_stream_transactions_total", "Replayed transactions scored", ["channel", "predicted"])
STREAM_OUTCOME = Counter("fintech_stream_outcomes_total", "Confusion outcome of replayed transactions", ["outcome"])
STREAM_AMOUNT = Counter("fintech_stream_amount_total", "Value of replayed transactions", ["kind"])
STREAM_RISK = Counter("fintech_stream_risk_tier_total", "Replayed transactions per risk tier", ["tier"])
STREAM_SEC = Counter("fintech_stream_security_events_total", "Replayed security events", ["event_type", "severity", "blocked"])
STREAM_ANOMALY = Counter("fintech_stream_security_anomalies_total", "Replayed security events flagged anomalous")
STREAM_BATCH_SECONDS = Gauge("fintech_stream_last_batch_unixtime", "Unix time of last scored batch")


def start_exporter(port: int) -> None:
    start_http_server(port)


@contextmanager
def instrument_stage(name: str):
    """Time a pipeline stage and record success / failure. Yields a dict; set ['rows'] to export row counts."""
    info: dict = {}
    t0 = time.perf_counter()
    try:
        yield info
    except Exception:
        STAGE_STATUS.labels(name).set(0)
        STAGE_ERRORS.labels(name).inc()
        STAGE_SECONDS.labels(name).set(time.perf_counter() - t0)
        raise
    else:
        STAGE_STATUS.labels(name).set(1)
        STAGE_SECONDS.labels(name).set(time.perf_counter() - t0)
        if "rows" in info:
            STAGE_ROWS.labels(name).set(info["rows"])
        info["seconds"] = time.perf_counter() - t0


def _reset(*gauges):
    for g in gauges:
        g.clear()


def publish_summary(s: dict) -> None:
    """Publish a run summary (dict produced by src.pipeline) to the Prometheus registry."""
    _reset(VALIDATION_CHECK, VALIDATION_FAILED_ROWS, CLEANING_ROWS, TXN_COUNT, TXN_FRAUD_COUNT, TXN_AMOUNT,
           FRAUD_RATE_CATEGORY, FRAUD_RATE_HOUR, FRAUD_BY_PATTERN, AMOUNT_QUANTILE, SEC_EVENTS, SEC_SOURCE, SEC_MTTR,
           MODEL_METRIC, MODEL_CONFUSION, MODEL_TRAIN_SECONDS, MODEL_THRESHOLD, MODEL_CV, CHAMPION, RISK_TIER,
           RISK_TIER_RATE, TRUST_DIM, TRUST_SEGMENT, TRUST_ALPHA, TRUST_CORR, TRUST_ITEM, TRUST_GROUP,
           STAGE_SECONDS, STAGE_ROWS, STAGE_STATUS)

    for st, v in s.get("stages", {}).items():
        STAGE_SECONDS.labels(st).set(v["seconds"]); STAGE_STATUS.labels(st).set(1)
        if "rows" in v:
            STAGE_ROWS.labels(st).set(v["rows"])
    PIPELINE_RUN_SECONDS.set(s.get("run_seconds", 0))

    for c in s["validation"]["checks"]:
        VALIDATION_CHECK.labels(c["check"]).set(int(c["passed"]))
        VALIDATION_FAILED_ROWS.labels(c["check"]).set(c["failed_count"])
    VALIDATION_PASS_RATE.set(s["validation"]["pass_rate"])
    for k, v in s["cleaning"].items():
        CLEANING_ROWS.labels(k).set(v)

    t = s["transactions"]
    for ch, v in t["by_channel"].items():
        TXN_COUNT.labels(ch).set(v["n"]); TXN_FRAUD_COUNT.labels(ch).set(v["frauds"])
    TXN_FRAUD_RATE.set(t["fraud_rate"])
    TXN_AMOUNT.labels("total").set(t["amount_total"]); TXN_AMOUNT.labels("fraud").set(t["amount_fraud"])
    for k, v in t["fraud_rate_by_category"].items():
        FRAUD_RATE_CATEGORY.labels(k).set(v)
    for k, v in t["fraud_rate_by_hour"].items():
        FRAUD_RATE_HOUR.labels(str(k)).set(v)
    for k, v in t["frauds_by_pattern"].items():
        FRAUD_BY_PATTERN.labels(k).set(v)
    for cls, qs in t["amount_quantiles"].items():
        for q, v in qs.items():
            AMOUNT_QUANTILE.labels(cls, q).set(v)

    sec = s["security"]
    for k, v in sec["events"].items():
        et, sev = k.split("|")
        SEC_EVENTS.labels(et, sev).set(v)
    SEC_BLOCK_RATE.set(sec["attack_block_rate"])
    for k, v in sec["attacks_by_source"].items():
        SEC_SOURCE.labels(k).set(v)
    SEC_ANOMALY_AUC.set(sec["anomaly_roc_auc"]); SEC_ANOMALIES.set(sec["anomalies_flagged"])
    for k, v in sec["mean_response_seconds"].items():
        SEC_MTTR.labels(k).set(v)

    for name, r in s["models"]["results"].items():
        for m in ("accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc", "false_positive_rate"):
            MODEL_METRIC.labels(name, m).set(r[m])
        for cell in ("tp", "fp", "tn", "fn"):
            MODEL_CONFUSION.labels(name, cell).set(r[cell])
        MODEL_THRESHOLD.labels(name).set(r["threshold"])
        if name in s["models"]["train"]:
            MODEL_TRAIN_SECONDS.labels(name).set(s["models"]["train"][name]["train_seconds"])
            MODEL_CV.labels(name).set(s["models"]["train"][name]["cv_score"])
        CHAMPION.labels(name).set(int(name == s["models"]["champion"]))
    for row in s["models"]["risk_tiers"]:
        RISK_TIER.labels(row["tier"]).set(row["transactions"])
        RISK_TIER_RATE.labels(row["tier"]).set(row["observed_fraud_rate"] or 0)

    tr = s["trust"]
    TRUST_MEAN.set(tr["mean_trust_score"]); TRUST_PSI.set(tr["platform_security_index"])
    TRUST_CTI.set(tr["consumer_trust_index"]); TRUST_N.set(tr["n_respondents"])
    for k, v in tr["dimension_means"].items():
        TRUST_DIM.labels(k).set(v)
    for k, v in tr["segments"].items():
        TRUST_SEGMENT.labels(k).set(v)
    for k, v in tr["cronbach_alpha"].items():
        if v == v:
            TRUST_ALPHA.labels(k).set(v)
    for k, v in tr["driver_correlations"].items():
        TRUST_CORR.labels(k).set(v)
    for k, v in tr["item_means"].items():
        TRUST_ITEM.labels(k).set(v)
    for k, v in tr["by_group"].items():
        g, val = k.split("|")
        TRUST_GROUP.labels(g, val).set(v)
    KANON.set(tr["k_anonymity_min_group"])

    PIPELINE_READY.set(1)
