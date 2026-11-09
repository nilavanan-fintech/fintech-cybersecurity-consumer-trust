"""End-to-end research pipeline.

    python -m src.pipeline [--fast] [--no-db] [--n-transactions N]

collect -> validate -> clean -> features -> train/tune -> evaluate -> anomaly ->
security analysis -> risk tiers -> survey & trust -> persist -> report -> publish metrics
Every stage is timed and exported to Prometheus (src/metrics/exporter.py).
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import platform
import time
import uuid
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd

from src.anomaly_detection.detectors import (
    evaluate_unsupervised, fit_isolation_forest, fit_lof, iso_scores, lof_scores,
)
from src.common import ROOT, get_logger, load_settings, resolve
from src.data_collection.external import load_creditcard
from src.data_collection.synthetic import generate_security_events, generate_survey, generate_transactions
from src.database import db
from src.feature_engineering.features import build_features, build_security_features, chronological_split, feature_names
from src.fraud_detection.risk import tier_summary
from src.fraud_detection.train import evaluate_models, train_and_select
from src.metrics import exporter as mx
from src.model_evaluation import statistics as st
from src.model_evaluation.evaluate import (
    bootstrap_ci, comparison_table, evaluate_binary, save_evaluation_plots, save_feature_importance,
)
from src.preprocessing.anonymize import enforce_k_anonymity, k_anonymity
from src.preprocessing.cleaning import clean_transactions, frame_hash
from src.preprocessing.validation import validate_transactions, validation_pass_rate
from src.reporting import make_figures, write_tables
from src.schema import SURVEY_ITEMS
from src.trust_scoring.scoring import (
    consumer_trust_index, dimension_scores, platform_security_index, reliability_report, score_respondents,
)

log = get_logger("pipeline")
SUMMARY_FILE = "last_run_summary.json"


def save_df(df: pd.DataFrame, stem, csv: bool = True) -> None:
    try:
        df.to_parquet(f"{stem}.parquet", index=False)
    except Exception as exc:  # pyarrow missing
        log.warning("parquet unavailable (%s) - writing CSV only", exc)
        csv = True
    if csv:
        df.to_csv(f"{stem}.csv", index=False)


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if np.isnan(o) else float(o)
    if isinstance(o, (pd.Timestamp, datetime)):
        return o.isoformat()
    return str(o)


def _daily(df: pd.DataFrame, ts_col: str, **aggs) -> pd.DataFrame:
    d = df.assign(day=pd.to_datetime(df[ts_col]).dt.normalize()).groupby("day").agg(**aggs).reset_index()
    return d


def run_pipeline(cfg: dict | None = None, use_db: bool = True) -> dict:
    cfg = cfg or load_settings()
    seed = cfg["seed"]
    run_id = datetime.now(timezone.utc).strftime("run_%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:4]
    started = datetime.now(timezone.utc)
    t_run = time.perf_counter()
    stages: dict[str, dict] = {}
    syn = cfg["synthetic"]
    raw_dir, interim_dir, proc_dir = resolve(cfg, "raw"), resolve(cfg, "interim"), resolve(cfg, "processed")
    syn_dir, models_dir, eval_dir = resolve(cfg, "synthetic"), resolve(cfg, "models"), resolve(cfg, "evaluation")
    meta_dir = resolve(cfg, "metadata")
    log.info("pipeline start %s", run_id, extra={"stage": "pipeline", "run_id": run_id})

    def stage(name):
        class _S:
            def __enter__(s_):
                s_.cm = mx.instrument_stage(name); s_.info = s_.cm.__enter__(); return s_.info
            def __exit__(s_, *a):
                r = s_.cm.__exit__(*a)
                if a[0] is None:
                    stages[name] = {k: v for k, v in s_.info.items()}
                    log.info("stage %s done in %.2fs", name, s_.info["seconds"], extra={"stage": name, "run_id": run_id})
                else:
                    log.error("stage %s failed: %s", name, a[1], extra={"stage": name, "run_id": run_id})
                return r
        return _S()

    try:
        # ---- 1. collect -----------------------------------------------------------------
        with stage("collect") as s:
            tx = generate_transactions(syn["n_transactions"], syn["n_customers"], syn["fraud_rate"], syn["days"],
                                       seed, syn["end_date"], syn["dirty_fraction"])
            ev = generate_security_events(syn["n_security_events"], syn["days"], seed, syn["end_date"])
            survey_path = ROOT / cfg["paths"]["survey"] / "survey_data.csv"
            if survey_path.exists():
                survey = pd.read_csv(survey_path)
            else:
                survey = enforce_k_anonymity(generate_survey(syn["n_survey_respondents"], seed), cfg["trust"]["k_anonymity"])
                survey.to_csv(survey_path, index=False)
            save_df(tx, syn_dir / "transactions_synthetic", csv=False)
            save_df(ev, syn_dir / "security_events_synthetic", csv=False)
            tx.to_csv(raw_dir / "transactions_raw.csv", index=False)
            ev.to_csv(raw_dir / "security_events_raw.csv", index=False)
            s["rows"] = len(tx)

        # ---- 2. validate ----------------------------------------------------------------
        with stage("validate") as s:
            checks = validate_transactions(tx, cfg)
            pass_rate = validation_pass_rate(checks)
            for c in checks:
                if not c["passed"]:
                    log.warning("validation failed: %s (%s rows) %s", c["check"], c["failed_count"], c["detail"],
                                extra={"stage": "validate", "event": "validation_failure"})
            s["rows"] = len(tx)

        # ---- 3. clean ---------------------------------------------------------------------
        with stage("clean") as s:
            clean, creport = clean_transactions(tx)
            save_df(clean, interim_dir / "transactions_clean")
            s["rows"] = len(clean)
        data_hash = frame_hash(clean.drop(columns=["timestamp"]))

        # ---- 4. feature engineering -----------------------------------------------------------
        with stage("features") as s:
            X = build_features(clean)
            y = clean["is_fraud"].to_numpy()
            tr, va, te = chronological_split(len(clean), cfg["split"]["train"], cfg["split"]["validation"])
            split = np.empty(len(clean), dtype=object); split[tr] = "train"; split[va] = "validation"; split[te] = "test"
            processed = pd.concat([clean[["transaction_id", "timestamp", "customer_id", "channel", "merchant_category",
                                          "amount", "is_fraud", "fraud_pattern"]], X], axis=1)
            processed["split"] = split
            save_df(processed, proc_dir / "transactions_features", csv=False)
            s["rows"] = X.shape[1]
        X_tr, X_va, X_te = X.iloc[tr], X.iloc[va], X.iloc[te]
        y_tr, y_va, y_te = y[tr], y[va], y[te]
        log.info("split sizes train=%d val=%d test=%d; fraud test=%d", len(y_tr), len(y_va), len(y_te), y_te.sum())

        # ---- 5. train + tune ---------------------------------------------------------------------
        with stage("train") as s:
            trained = train_and_select(X_tr, y_tr, X_va, y_va, cfg)
            s["rows"] = len(trained)

        # ---- 6. evaluate ---------------------------------------------------------------------------
        with stage("evaluate") as s:
            results, scores = evaluate_models(trained, X_te, y_te)
            champion = max(results, key=lambda m: results[m]["pr_auc"])
            ci = bootstrap_ci(y_te, scores[champion], n_boot=200, seed=seed)
            lr_name = "logistic_regression" if "logistic_regression" in results else None
            mc = None
            if lr_name and champion != lr_name:
                pc = (scores[champion] >= results[champion]["threshold"]).astype(int)
                pl = (scores[lr_name] >= results[lr_name]["threshold"]).astype(int)
                mc = st.mcnemar(y_te, pc, pl)
            s["rows"] = len(y_te)

        # ---- 7. anomaly detection (unsupervised) ----------------------------------------------------
        with stage("anomaly") as s:
            cont = cfg["anomaly"]["contamination"]
            iso = fit_isolation_forest(X_tr, cont, seed)
            lof = fit_lof(X_tr, cfg["anomaly"]["lof_train_sample"], cfg["anomaly"]["lof_neighbors"], cont, seed)
            for name, mdl, fn in (("isolation_forest", iso, iso_scores), ("local_outlier_factor", lof, lof_scores)):
                sv, ste = fn(mdl, X_va), fn(mdl, X_te)
                results[name] = evaluate_unsupervised(sv, ste, y_te, cont)
                scores[name] = ste
            s["rows"] = len(y_te)

        # ---- 8. security threat analysis ---------------------------------------------------------------
        with stage("security") as s:
            F = build_security_features(ev)
            n_tr = int(len(ev) * cfg["split"]["train"])
            sec_cont = cfg["anomaly"].get("security_contamination", 0.15)
            sec_iso = fit_isolation_forest(F.iloc[:n_tr], sec_cont, seed)
            sec_scores = iso_scores(sec_iso, F)
            sec_thr = float(np.quantile(sec_scores[:n_tr], 1 - sec_cont))
            sec_flag = sec_scores >= sec_thr
            from sklearn.metrics import roc_auc_score
            sec_auc = float(roc_auc_score(ev["is_attack"], sec_scores))
            att = ev[ev["is_attack"] == 1]
            ev_counts = ev.groupby(["event_type", "severity"]).size()
            sec_summary = {
                "events": {f"{a}|{b}": int(v) for (a, b), v in ev_counts.items()},
                "attack_block_rate": float(att["blocked"].mean()),
                "attacks_by_source": {k: int(v) for k, v in att["source_country"].value_counts().items()},
                "anomaly_roc_auc": sec_auc, "anomalies_flagged": int(sec_flag.sum()),
                "mean_response_seconds": {"attack": float(att["response_time_s"].mean()),
                                          "benign": float(ev.loc[ev["is_attack"] == 0, "response_time_s"].mean())},
                "threshold": sec_thr,
            }
            ev_out = pd.concat([ev, F.add_prefix("f_")], axis=1)
            ev_out["anomaly_score"] = sec_scores; ev_out["flagged"] = sec_flag
            ev_out["split"] = np.where(np.arange(len(ev)) < n_tr, "train", "replay")
            save_df(ev_out, proc_dir / "security_events_scored", csv=False)
            s["rows"] = len(ev)

        # ---- 9. risk classification --------------------------------------------------------------------------
        with stage("risk") as s:
            amt_te = clean["amount"].to_numpy()[te]
            risk = tier_summary(scores[champion], y_te, amt_te, cfg["risk_tiers"])
            s["rows"] = len(risk)

        # ---- 10. survey + consumer trust -----------------------------------------------------------------------
        with stage("trust") as s:
            ksum = k_anonymity(survey, cfg["trust"]["k_anonymity"])
            rs = score_respondents(survey, cfg)
            rel = reliability_report(survey)
            full = survey.merge(rs[["respondent_id", "trust_score", "segment"]], on="respondent_id")
            drivers = ["uses_mfa", "experienced_fraud", "digital_literacy"]
            corr = st.correlation_with_p(full, "trust_score", drivers)
            ols_df = st.ols(full[drivers], full["trust_score"])
            by_group = {}
            for g in ("age_band", "usage_frequency", "education", "uses_mfa", "experienced_fraud"):
                for val, m in full.groupby(g)["trust_score"].mean().items():
                    by_group[f"{g}|{val}"] = float(m)
            mean_cts = float(rs["trust_score"].mean())
            rc = results[champion]
            psi = platform_security_index(rc["recall"], rc["false_positive_rate"], sec_summary["attack_block_rate"], pass_rate)
            cti = consumer_trust_index(mean_cts, psi, cfg["trust"]["survey_weight_in_index"])
            trust_summary = {
                "n_respondents": int(len(rs)), "mean_trust_score": mean_cts, "platform_security_index": psi,
                "consumer_trust_index": cti,
                "dimension_means": {k: float(v) for k, v in dimension_scores(survey).mean().items()},
                "segments": {k: int(v) for k, v in rs["segment"].value_counts().reindex(["Low", "Moderate", "High"]).fillna(0).items()},
                "cronbach_alpha": rel,
                "driver_correlations": {r.variable: float(r.r) for r in corr.itertuples()},
                "driver_p_values": {r.variable: float(r.p_value) for r in corr.itertuples()},
                "ols_r2": ols_df.attrs["r2"],
                "item_means": {q: float(survey[q].mean()) for q in SURVEY_ITEMS},
                "by_group": by_group, "k_anonymity_min_group": ksum["min_group_size"],
            }
            save_df(rs, proc_dir / "trust_scores")
            s["rows"] = len(rs)

        # ---- 11. persist models, metadata, evaluation artefacts ------------------------------------------------
        with stage("persist") as s:
            versions = {"python": platform.python_version()}
            import sklearn, xgboost
            versions.update(sklearn=sklearn.__version__, xgboost=xgboost.__version__, pandas=pd.__version__, numpy=np.__version__)
            for name, t in trained.items():
                path = models_dir / f"{name}.joblib"
                joblib.dump(t["model"], path)
                meta = {"model": name, "artifact": str(path.relative_to(ROOT)), "best_params": t["params"],
                        "cv_score": t["cv_score"], "threshold": t["threshold"], "train_seconds": t["train_seconds"],
                        "features": feature_names(), "metrics_test": results[name], "data_hash": data_hash,
                        "seed": seed, "run_id": run_id, "library_versions": versions}
                (meta_dir / f"{name}.json").write_text(json.dumps(meta, indent=2, default=_json_default))
            joblib.dump(iso, models_dir / "isolation_forest.joblib")
            joblib.dump(lof, models_dir / "local_outlier_factor.joblib")
            joblib.dump(sec_iso, models_dir / "security_isolation_forest.joblib")
            (meta_dir / "champion.json").write_text(json.dumps({"champion": champion, "run_id": run_id,
                                                               "security_threshold": sec_thr}, indent=2))
            table = comparison_table(results)
            table.to_csv(eval_dir / "model_comparison.csv")
            (eval_dir / "results.json").write_text(json.dumps(results, indent=2, default=_json_default))
            figs = save_evaluation_plots(y_te, {k: v for k, v in scores.items()}, results, eval_dir)
            for name in trained:
                save_feature_importance(trained[name]["model"], feature_names(), eval_dir, name)
            s["rows"] = len(trained)

        # ---- 12. optional public benchmark -----------------------------------------------------------------------
        external = None
        cc = load_creditcard(resolve(cfg, "external"))
        if cc is not None:
            with stage("external_benchmark") as s:
                Xc = cc.drop(columns=["Class", "Time"]).assign(Amount=np.log1p(cc["Amount"]))
                yc = cc["Class"].to_numpy()
                a, b, c_ = chronological_split(len(cc), 0.7, 0.15)
                tc = train_and_select(Xc.iloc[a], yc[a], Xc.iloc[b], yc[b], cfg)
                external, _ = evaluate_models(tc, Xc.iloc[c_], yc[c_])
                s["rows"] = len(cc)

        # ---- 13. reporting artefacts ----------------------------------------------------------------------------------
        with stage("report") as s:
            make_figures(clean, ev, full, rs, survey, results, scores, y_te, cfg)
            write_tables(table, risk, trust_summary, corr, ols_df, rel, checks, external)
            s["rows"] = 1

        finished = datetime.now(timezone.utc)
        t = clean.groupby("channel").agg(n=("is_fraud", "size"), frauds=("is_fraud", "sum"))
        hour = pd.to_datetime(clean["timestamp"]).dt.hour
        q = {"legit": clean.loc[clean.is_fraud == 0, "amount"], "fraud": clean.loc[clean.is_fraud == 1, "amount"]}
        summary = {
            "run_id": run_id, "started_at": started.replace(tzinfo=None), "finished_at": finished.replace(tzinfo=None),
            "run_seconds": time.perf_counter() - t_run, "seed": seed, "data_hash": data_hash, "versions": versions,
            "stages": stages, "cleaning": creport,
            "validation": {"checks": checks, "pass_rate": pass_rate},
            "transactions": {
                "by_channel": {k: {"n": int(r.n), "frauds": int(r.frauds)} for k, r in t.iterrows()},
                "fraud_rate": float(clean["is_fraud"].mean()),
                "amount_total": float(clean["amount"].sum()),
                "amount_fraud": float(clean.loc[clean.is_fraud == 1, "amount"].sum()),
                "fraud_rate_by_category": {k: float(v) for k, v in clean.groupby("merchant_category")["is_fraud"].mean().items()},
                "fraud_rate_by_hour": {int(k): float(v) for k, v in clean.groupby(hour)["is_fraud"].mean().items()},
                "frauds_by_pattern": {k: int(v) for k, v in clean.loc[clean.is_fraud == 1, "fraud_pattern"].value_counts().items()},
                "amount_quantiles": {c: {str(p): float(s_.quantile(p)) for p in (0.5, 0.9, 0.99)} for c, s_ in q.items()},
            },
            "security": sec_summary,
            "models": {
                "results": results, "champion": champion, "champion_roc_auc_ci95": ci, "mcnemar_vs_lr": mc,
                "train": {k: {"train_seconds": v["train_seconds"], "cv_score": v["cv_score"], "params": v["params"]}
                          for k, v in trained.items()},
                "risk_tiers": risk.replace({np.nan: None}).to_dict("records"),
                "types": {**{k: "supervised" for k in trained}, "isolation_forest": "unsupervised",
                          "local_outlier_factor": "unsupervised"},
            },
            "trust": trust_summary, "external_benchmark": external,
        }

        # ---- 14. database ---------------------------------------------------------------------------------------------------
        with stage("database") as s:
            rows = 0
            if use_db:
                engine = db.get_engine()
                _wait_for_db(engine)
                db.init_schema(engine)
                mr = pd.DataFrame(results).T.reset_index(names="model")
                mr[["tn", "fp", "fn", "tp"]] = mr[["tn", "fp", "fn", "tp"]].astype(int)
                mr["dataset"] = "synthetic_transactions"
                mr["model_type"] = mr["model"].map(summary["models"]["types"])
                tx_daily = _daily(clean, "timestamp", n_transactions=("is_fraud", "size"), n_frauds=("is_fraud", "sum"),
                                  amount_total=("amount", "sum"))
                tx_daily["amount_fraud"] = clean.assign(a=clean.amount * clean.is_fraud).assign(
                    day=pd.to_datetime(clean.timestamp).dt.normalize()).groupby("day")["a"].sum().values
                sec_daily = _daily(ev, "timestamp", n_events=("is_attack", "size"), n_attacks=("is_attack", "sum"),
                                   n_blocked=("blocked", "sum"))
                tables = {
                    "model_results": mr,
                    "data_quality_checks": pd.DataFrame(checks).rename(columns={"check": "check_name"}),
                    "transaction_daily_summary": tx_daily,
                    "security_daily_summary": sec_daily,
                    "risk_tier_summary": risk,
                    "trust_respondent_scores": rs,
                    "model_metadata": pd.DataFrame([{
                        "model": k, "artifact_path": f"models/trained/{k}.joblib", "params": json.dumps(v["params"]),
                        "n_features": len(feature_names()), "threshold": v["threshold"],
                        "train_seconds": v["train_seconds"], "cv_score": v["cv_score"]} for k, v in trained.items()]),
                    "survey_responses": survey,
                }
                db.persist_run(engine, run_id, summary, tables)
                rows = sum(len(v) for v in tables.values())
            s["rows"] = rows
        summary["stages"] = stages
        summary["run_seconds"] = time.perf_counter() - t_run

        (meta_dir / SUMMARY_FILE).write_text(json.dumps(summary, indent=2, default=_json_default))
        mx.publish_summary(json.loads(json.dumps(summary, default=_json_default)))
        mx.PIPELINE_RUNS.labels("success").inc()
        mx.PIPELINE_LAST_SUCCESS.set(time.time())
        log.info("pipeline finished in %.1fs; champion=%s pr_auc=%.3f", summary["run_seconds"], champion,
                 results[champion]["pr_auc"], extra={"stage": "pipeline", "run_id": run_id})
        return summary
    except Exception:
        mx.PIPELINE_RUNS.labels("failure").inc()
        log.exception("pipeline failed", extra={"stage": "pipeline", "run_id": run_id})
        raise


def _wait_for_db(engine, timeout: int = 60) -> None:
    t0 = time.time()
    while True:
        try:
            with engine.connect() as c:
                c.exec_driver_sql("SELECT 1")
            return
        except Exception as exc:
            if time.time() - t0 > timeout:
                raise
            log.warning("waiting for database: %s", str(exc).splitlines()[0])
            time.sleep(2)


def load_last_summary(cfg: dict | None = None) -> dict | None:
    cfg = cfg or load_settings()
    p = ROOT / cfg["paths"]["metadata"] / SUMMARY_FILE
    return json.loads(p.read_text()) if p.exists() else None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fast", action="store_true", help="small dataset + minimal tuning (smoke test)")
    ap.add_argument("--no-db", action="store_true", help="skip PostgreSQL persistence")
    ap.add_argument("--n-transactions", type=int)
    a = ap.parse_args()
    cfg = copy.deepcopy(load_settings())
    if a.fast:
        cfg["synthetic"]["n_transactions"] = 15000
        cfg["synthetic"]["n_security_events"] = 6000
        cfg["tuning"]["n_iter"] = 2
    if a.n_transactions:
        cfg["synthetic"]["n_transactions"] = a.n_transactions
    run_pipeline(cfg, use_db=not a.no_db)


if __name__ == "__main__":
    main()
