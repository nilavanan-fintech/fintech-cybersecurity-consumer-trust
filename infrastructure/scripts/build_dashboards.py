"""Generate the provisioned Grafana dashboard JSON files (dashboard/grafana/dashboards/*.json).

Run `python infrastructure/scripts/build_dashboards.py` after editing. Every panel queries a live
data source (Prometheus / Loki / PostgreSQL); there are no hardcoded demonstration values.
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "dashboard" / "grafana" / "dashboards"
PROM = {"type": "prometheus", "uid": "prometheus"}
LOKI = {"type": "loki", "uid": "loki"}
PG = {"type": "grafana-postgresql-datasource", "uid": "postgres"}


class Dash:
    def __init__(self, uid, title, tags, refresh="10s", frm="now-30m"):
        self.d = {"uid": uid, "title": title, "tags": ["fintech", *tags], "timezone": "browser", "schemaVersion": 39,
                  "version": 1, "editable": True, "refresh": refresh, "time": {"from": frm, "to": "now"},
                  "graphTooltip": 1, "templating": {"list": []}, "annotations": {"list": []}, "panels": []}
        self._id = 0
        self.y = 0
        self.x = 0
        self.row_h = 0

    def _place(self, w, h):
        if self.x + w > 24:
            self.x, self.y, self.row_h = 0, self.y + self.row_h, 0
        pos = {"x": self.x, "y": self.y, "w": w, "h": h}
        self.x += w
        self.row_h = max(self.row_h, h)
        return pos

    def row(self, title):
        self.x, self.y, self.row_h = 0, self.y + self.row_h, 0
        self._id += 1
        self.d["panels"].append({"id": self._id, "type": "row", "title": title, "collapsed": False,
                                 "gridPos": {"x": 0, "y": self.y, "w": 24, "h": 1}, "panels": []})
        self.y += 1

    def add(self, ptype, title, targets, ds, w=6, h=6, unit=None, desc=None, options=None, thresholds=None,
            min_=None, max_=None, custom=None, overrides=None, decimals=None, mappings=None, transformations=None, time_from=None):
        self._id += 1
        defaults = {"color": {"mode": "palette-classic" if ptype in ("timeseries", "piechart", "barchart") else "thresholds"}}
        if unit:
            defaults["unit"] = unit
        if min_ is not None:
            defaults["min"] = min_
        if max_ is not None:
            defaults["max"] = max_
        if decimals is not None:
            defaults["decimals"] = decimals
        if thresholds:
            defaults["thresholds"] = {"mode": "absolute", "steps": [{"color": c, "value": v} for v, c in thresholds]}
        if custom:
            defaults["custom"] = custom
        if mappings:
            defaults["mappings"] = mappings
        p = {"id": self._id, "type": ptype, "title": title, "datasource": ds, "gridPos": self._place(w, h),
             "targets": targets, "fieldConfig": {"defaults": defaults, "overrides": overrides or []},
             "options": options or {}}
        if desc:
            p["description"] = desc
        if transformations:
            p["transformations"] = transformations
        if time_from:
            p["timeFrom"] = time_from
        self.d["panels"].append(p)

    def save(self, name):
        (OUT / name).write_text(json.dumps(self.d, indent=2), encoding="utf-8")


def q(expr, legend="", instant=False, ref="A"):
    t = {"refId": ref, "expr": expr, "legendFormat": legend or "__auto", "datasource": PROM}
    if instant:
        t.update(instant=True, range=False)
    return t


def pg(sql, fmt="time_series", ref="A"):
    return {"refId": ref, "datasource": PG, "format": fmt, "rawQuery": True, "editorMode": "code", "rawSql": sql}


def lq(expr, ref="A"):
    return {"refId": ref, "datasource": LOKI, "expr": expr, "queryType": "range"}


GREEN, YEL, RED, BLUE = "green", "yellow", "red", "blue"
STAT = {"reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False}, "colorMode": "background",
        "graphMode": "area", "textMode": "auto"}
STAT_VAL = {**STAT, "colorMode": "value"}
BARG = {"reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False}, "orientation": "horizontal",
        "displayMode": "gradient", "showUnfilled": True, "namePlacement": "left"}
LEGEND = {"legend": {"displayMode": "table", "placement": "bottom", "calcs": ["lastNotNull", "mean"]},
          "tooltip": {"mode": "multi", "sort": "desc"}}
PIE = {"reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False}, "pieType": "donut",
       "legend": {"displayMode": "table", "placement": "right", "values": ["value", "percent"]},
       "tooltip": {"mode": "single"}}
LOGS = {"showTime": True, "wrapLogMessage": True, "sortOrder": "Descending", "enableLogDetails": True}
TS = {"lineWidth": 2, "fillOpacity": 12, "showPoints": "never", "spanNulls": True}
LOG_BASE = '{job="fintech"} | json'


def fintech_overview():
    d = Dash("fintech-overview", "FinTech Research Overview", ["overview"])
    d.row("Headline indicators (computed by the pipeline)")
    d.add("stat", "Pipeline ready", [q("fintech_pipeline_ready", instant=True)], PROM, 3, 4,
          mappings=[{"type": "value", "options": {"0": {"text": "BUILDING", "color": "orange"}, "1": {"text": "READY", "color": "green"}}}],
          options=STAT)
    d.add("stat", "Last successful run", [q("time() - fintech_pipeline_last_success_timestamp_seconds", instant=True)], PROM, 3, 4,
          unit="s", desc="Age of the last successful pipeline run.", thresholds=[(None, GREEN), (86400, YEL), (604800, RED)], options=STAT)
    d.add("stat", "Fraud rate (dataset)", [q("fintech_txn_dataset_fraud_rate", instant=True)], PROM, 3, 4, unit="percentunit",
          decimals=2, thresholds=[(None, GREEN), (0.03, YEL), (0.06, RED)], options=STAT)
    d.add("stat", "Champion PR-AUC", [q('fintech_model_metric{metric="pr_auc"} * on(model) group_left() (fintech_model_champion == 1)', "{{model}}", instant=True)],
          PROM, 3, 4, decimals=3, min_=0, max_=1, thresholds=[(None, RED), (0.5, YEL), (0.8, GREEN)], options=STAT)
    d.add("stat", "Mean trust score", [q("fintech_trust_score_mean", instant=True)], PROM, 3, 4, decimals=1, min_=0, max_=100,
          thresholds=[(None, RED), (50, YEL), (75, GREEN)], options=STAT)
    d.add("stat", "Consumer Trust Index", [q("fintech_trust_consumer_trust_index", instant=True)], PROM, 3, 4, decimals=1, min_=0, max_=100,
          thresholds=[(None, RED), (50, YEL), (75, GREEN)], options=STAT)
    d.add("stat", "Platform Security Index", [q("fintech_trust_platform_security_index", instant=True)], PROM, 3, 4, decimals=1,
          min_=0, max_=100, thresholds=[(None, RED), (60, YEL), (80, GREEN)], options=STAT)
    d.add("stat", "Transactions scored (live)", [q("sum(fintech_stream_transactions_total)", instant=True)], PROM, 3, 4, options=STAT_VAL)
    d.row("Live stream (held-out replay through champion model)")
    d.add("timeseries", "Transactions scored / s", [q("sum by (predicted) (rate(fintech_stream_transactions_total[1m]))", "{{predicted}}")],
          PROM, 8, 8, unit="ops", options=LEGEND, custom=TS)
    d.add("timeseries", "Security events / s by severity", [q("sum by (severity) (rate(fintech_stream_security_events_total[1m]))", "{{severity}}")],
          PROM, 8, 8, unit="ops", options=LEGEND, custom=TS)
    d.add("bargauge", "Model PR-AUC (test set)", [q('fintech_model_metric{metric="pr_auc"}', "{{model}}", instant=True)], PROM, 8, 8,
          min_=0, max_=1, decimals=3, options=BARG, thresholds=[(None, RED), (0.4, YEL), (0.7, GREEN)])
    d.row("Application logs (Loki)")
    d.add("logs", "Warnings and errors", [lq('{job="fintech", level=~"WARNING|ERROR|CRITICAL"}')], LOKI, 24, 9, options=LOGS)
    d.save("fintech_overview.json")


def fraud_detection():
    d = Dash("fraud-detection", "Transaction & Fraud Analytics", ["fraud", "transactions"])
    d.row("Dataset-level fraud analytics")
    d.add("stat", "Transactions", [q("sum(fintech_txn_dataset_transactions)", instant=True)], PROM, 4, 4, options=STAT_VAL)
    d.add("stat", "Labelled frauds", [q("sum(fintech_txn_dataset_frauds)", instant=True)], PROM, 4, 4, options=STAT_VAL)
    d.add("stat", "Fraud rate", [q("fintech_txn_dataset_fraud_rate", instant=True)], PROM, 4, 4, unit="percentunit", decimals=2, options=STAT_VAL)
    d.add("stat", "Fraud value", [q('fintech_txn_dataset_amount_total{kind="fraud"}', instant=True)], PROM, 4, 4, unit="short", options=STAT_VAL)
    d.add("stat", "Fraud share of value", [q('fintech_txn_dataset_amount_total{kind="fraud"} / fintech_txn_dataset_amount_total{kind="total"}', instant=True)],
          PROM, 4, 4, unit="percentunit", decimals=2, options=STAT_VAL)
    d.add("stat", "Median amount fraud / legit", [q('fintech_txn_amount_quantile{class="fraud",quantile="0.5"}', "fraud", instant=True),
                                                   q('fintech_txn_amount_quantile{class="legit",quantile="0.5"}', "legit", instant=True, ref="B")],
          PROM, 4, 4, decimals=1, options=STAT_VAL)
    d.add("bargauge", "Fraud rate by merchant category", [q("fintech_txn_fraud_rate_by_category", "{{merchant_category}}", instant=True)],
          PROM, 8, 9, unit="percentunit", decimals=2, options=BARG, thresholds=[(None, GREEN), (0.02, YEL), (0.04, RED)])
    d.add("barchart", "Fraud rate by hour of day", [q("fintech_txn_fraud_rate_by_hour", "{{hour}}", instant=True)], PROM, 8, 9, unit="percentunit",
          options={"orientation": "vertical", "xTickLabelRotation": 0, "legend": {"showLegend": False}, "tooltip": {"mode": "single"}},
          transformations=[{"id": "reduce", "options": {"reducers": ["lastNotNull"], "mode": "reduceFields"}}])
    d.add("piechart", "Frauds by attack pattern", [q("fintech_txn_frauds_by_pattern", "{{pattern}}", instant=True)], PROM, 8, 9, options=PIE)
    d.row("PostgreSQL: daily series from the latest run")
    d.add("timeseries", "Daily transactions vs frauds",
          [pg("SELECT day AS time, n_transactions AS \"transactions\" FROM v_latest_txn_daily WHERE $__timeFilter(day) ORDER BY 1"),
           pg("SELECT day AS time, n_frauds AS \"frauds\" FROM v_latest_txn_daily WHERE $__timeFilter(day) ORDER BY 1", ref="B")],
          PG, 12, 8, options=LEGEND, custom=TS, time_from="100d",
          overrides=[{"matcher": {"id": "byName", "options": "frauds"}, "properties": [{"id": "custom.axisPlacement", "value": "right"}]}])
    d.add("timeseries", "Daily fraud value", [pg("SELECT day AS time, amount_fraud AS \"fraud value\" FROM v_latest_txn_daily WHERE $__timeFilter(day) ORDER BY 1")],
          PG, 12, 8, options=LEGEND, custom=TS, time_from="100d")
    d.row("Live detection performance (champion model on replayed held-out data)")
    d.add("timeseries", "Outcomes / s (TP, FP, FN, TN)", [q("sum by (outcome) (rate(fintech_stream_outcomes_total[1m]))", "{{outcome}}")],
          PROM, 8, 8, unit="ops", options=LEGEND, custom=TS)
    d.add("stat", "Live precision", [q('sum(increase(fintech_stream_outcomes_total{outcome="tp"}[$__range])) / clamp_min(sum(increase(fintech_stream_outcomes_total{outcome=~"tp|fp"}[$__range])), 1)', instant=True)],
          PROM, 4, 8, unit="percentunit", decimals=1, thresholds=[(None, RED), (0.5, YEL), (0.8, GREEN)], options=STAT)
    d.add("stat", "Live recall", [q('sum(increase(fintech_stream_outcomes_total{outcome="tp"}[$__range])) / clamp_min(sum(increase(fintech_stream_outcomes_total{outcome=~"tp|fn"}[$__range])), 1)', instant=True)],
          PROM, 4, 8, unit="percentunit", decimals=1, thresholds=[(None, RED), (0.5, YEL), (0.8, GREEN)], options=STAT)
    d.add("timeseries", "Fraud value caught vs missed / s", [q("sum by (kind) (rate(fintech_stream_amount_total{kind=~\"fraud_caught|fraud_missed\"}[1m]))", "{{kind}}")],
          PROM, 8, 8, unit="short", options=LEGEND, custom=TS)
    d.row("Risk classification")
    d.add("piechart", "Live transactions by risk tier", [q("sum by (tier) (increase(fintech_stream_risk_tier_total[$__range]))", "{{tier}}", instant=True)], PROM, 8, 8, options=PIE)
    d.add("bargauge", "Observed fraud rate per tier (test set)", [q("fintech_risk_tier_observed_fraud_rate", "{{tier}}", instant=True)], PROM, 8, 8,
          unit="percentunit", decimals=1, options=BARG, thresholds=[(None, GREEN), (0.1, YEL), (0.5, RED)])
    d.add("table", "Risk tier summary (PostgreSQL)", [pg("SELECT r.tier, r.transactions, r.frauds, ROUND(r.observed_fraud_rate::numeric,4) AS observed_fraud_rate, r.action FROM risk_tier_summary r WHERE r.run_id=(SELECT run_id FROM latest_run) ORDER BY CASE r.tier WHEN 'low' THEN 1 WHEN 'medium' THEN 2 WHEN 'high' THEN 3 ELSE 4 END", fmt="table")],
          PG, 8, 8)
    d.save("fraud_detection.json")


def cybersecurity():
    d = Dash("cyber-monitoring", "Cybersecurity Threat Monitoring", ["security", "threats"])
    d.row("Threat landscape (dataset)")
    atk = 'event_type!~"login_success|password_reset|api_call"'
    d.add("stat", "Attack events", [q(f"sum(fintech_security_dataset_events{{{atk}}})", instant=True)], PROM, 4, 4, options=STAT_VAL)
    d.add("stat", "Attack block rate", [q("fintech_security_block_rate", instant=True)], PROM, 4, 4, unit="percentunit", decimals=1,
          thresholds=[(None, RED), (0.7, YEL), (0.85, GREEN)], options=STAT)
    d.add("stat", "Anomaly detector ROC-AUC", [q("fintech_security_anomaly_roc_auc", instant=True)], PROM, 4, 4, decimals=3, min_=0, max_=1,
          thresholds=[(None, RED), (0.7, YEL), (0.85, GREEN)], options=STAT)
    d.add("stat", "Anomalies flagged", [q("fintech_security_anomalies_flagged", instant=True)], PROM, 4, 4, options=STAT_VAL)
    d.add("stat", "Mean response: attack (s)", [q('fintech_security_mean_response_seconds{kind="attack"}', instant=True)], PROM, 4, 4, unit="s", decimals=3, options=STAT_VAL)
    d.add("stat", "Mean response: benign (s)", [q('fintech_security_mean_response_seconds{kind="benign"}', instant=True)], PROM, 4, 4, unit="s", decimals=3, options=STAT_VAL)
    d.add("bargauge", "Attacks by type", [q(f"sum by (event_type) (fintech_security_dataset_events{{{atk}}})", "{{event_type}}", instant=True)], PROM, 8, 8, options=BARG)
    d.add("piechart", "Attack events by severity", [q(f"sum by (severity) (fintech_security_dataset_events{{{atk}}})", "{{severity}}", instant=True)], PROM, 8, 8, options=PIE)
    d.add("bargauge", "Attacks by source country", [q("fintech_security_attacks_by_source_country", "{{country}}", instant=True)], PROM, 8, 8, options=BARG)
    d.row("PostgreSQL: attack campaigns over time")
    d.add("timeseries", "Daily attacks vs blocked", [pg("SELECT day AS time, n_attacks AS \"attacks\" FROM v_latest_security_daily WHERE $__timeFilter(day) ORDER BY 1"),
                                                     pg("SELECT day AS time, n_blocked AS \"blocked (all)\" FROM v_latest_security_daily WHERE $__timeFilter(day) ORDER BY 1", ref="B")],
          PG, 24, 8, options=LEGEND, custom=TS, time_from="100d")
    d.row("Live replay (unsupervised Isolation Forest on security events)")
    d.add("timeseries", "Security events / s by type", [q("sum by (event_type) (rate(fintech_stream_security_events_total[1m]))", "{{event_type}}")],
          PROM, 12, 8, unit="ops", options=LEGEND, custom=TS)
    d.add("timeseries", "Anomalies flagged / s", [q("rate(fintech_stream_security_anomalies_total[1m])", "anomalies")], PROM, 6, 8, unit="ops", options=LEGEND, custom=TS)
    d.add("timeseries", "Blocked share of replayed events", [q('sum(rate(fintech_stream_security_events_total{blocked="true"}[2m])) / clamp_min(sum(rate(fintech_stream_security_events_total[2m])), 1e-9)', "blocked share")],
          PROM, 6, 8, unit="percentunit", options=LEGEND, custom=TS)
    d.row("Security-related log events (Loki)")
    d.add("logs", "Validation failures and warnings", [lq('{job="fintech", level=~"WARNING|ERROR"}')], LOKI, 24, 8, options=LOGS)
    d.save("cybersecurity_monitoring.json")


def consumer_trust():
    d = Dash("consumer-trust", "Consumer Trust Indicators", ["trust", "survey"], refresh="30s", frm="now-1h")
    d.row("Trust indices (0-100)")
    th = [(None, RED), (50, YEL), (75, GREEN)]
    d.add("gauge", "Mean Consumer Trust Score", [q("fintech_trust_score_mean", instant=True)], PROM, 6, 6, min_=0, max_=100, decimals=1, thresholds=th,
          options={"reduceOptions": {"calcs": ["lastNotNull"]}, "showThresholdMarkers": True})
    d.add("gauge", "Platform Security Index", [q("fintech_trust_platform_security_index", instant=True)], PROM, 6, 6, min_=0, max_=100, decimals=1,
          thresholds=[(None, RED), (60, YEL), (80, GREEN)], options={"reduceOptions": {"calcs": ["lastNotNull"]}, "showThresholdMarkers": True})
    d.add("gauge", "Consumer Trust Index (combined)", [q("fintech_trust_consumer_trust_index", instant=True)], PROM, 6, 6, min_=0, max_=100, decimals=1, thresholds=th,
          options={"reduceOptions": {"calcs": ["lastNotNull"]}, "showThresholdMarkers": True})
    d.add("stat", "Respondents / k-anonymity min group", [q("fintech_trust_survey_respondents", "respondents", instant=True),
                                                         q("fintech_trust_k_anonymity_min_group", "min group size", instant=True, ref="B")],
          PROM, 6, 6, options={**STAT_VAL, "textMode": "value_and_name"})
    d.row("Survey results")
    d.add("bargauge", "Trust by dimension", [q("fintech_trust_dimension_mean", "{{dimension}}", instant=True)], PROM, 8, 8, min_=0, max_=100, decimals=1, options=BARG, thresholds=th)
    d.add("piechart", "Trust segments", [q("fintech_trust_segment_respondents", "{{segment}}", instant=True)], PROM, 8, 8, options=PIE)
    d.add("histogram", "Trust score distribution (PostgreSQL)", [pg("SELECT trust_score FROM v_latest_trust", fmt="table")], PG, 8, 8,
          options={"bucketCount": 20, "legend": {"showLegend": False}})
    d.add("bargauge", "Mean Likert response per item (1-5)", [q("fintech_trust_item_mean", "{{item}}", instant=True)], PROM, 8, 9, min_=1, max_=5, decimals=2, options=BARG)
    d.add("bargauge", "Trust score by respondent group", [q("fintech_trust_score_by_group", "{{group}}: {{value}}", instant=True)], PROM, 8, 9, min_=0, max_=100, decimals=1, options=BARG, thresholds=th)
    d.add("bargauge", "Spearman correlation: trust vs driver", [q("fintech_trust_driver_correlation", "{{driver}}", instant=True)], PROM, 8, 9, min_=-1, max_=1, decimals=2,
          options=BARG, thresholds=[(None, RED), (0, YEL), (0.2, GREEN)])
    d.row("Measurement quality")
    d.add("bargauge", "Cronbach's alpha (scale reliability)", [q("fintech_trust_cronbach_alpha", "{{scale}}", instant=True)], PROM, 12, 7, min_=0, max_=1, decimals=2, options=BARG,
          thresholds=[(None, RED), (0.6, YEL), (0.7, GREEN)], desc="alpha >= 0.7 is conventionally acceptable (Cronbach, 1951; Nunnally).")
    d.add("table", "Survey-derived trust per segment (PostgreSQL)", [pg("SELECT segment, COUNT(*) AS respondents, ROUND(AVG(trust_score)::numeric,1) AS mean_trust FROM v_latest_trust GROUP BY segment ORDER BY mean_trust DESC", fmt="table")], PG, 12, 7)
    d.save("consumer_trust.json")


def model_performance():
    d = Dash("model-performance", "Machine Learning Model Performance", ["ml", "models"], refresh="30s", frm="now-1h")
    d.row("Held-out test metrics per model (Logistic Regression, Random Forest, XGBoost, Isolation Forest, LOF)")
    for title, m, thr in (("F1-score", "f1", [(None, RED), (0.4, YEL), (0.7, GREEN)]), ("Recall", "recall", [(None, RED), (0.5, YEL), (0.8, GREEN)]),
                          ("Precision", "precision", [(None, RED), (0.4, YEL), (0.7, GREEN)])):
        d.add("bargauge", title, [q(f'fintech_model_metric{{metric="{m}"}}', "{{model}}", instant=True)], PROM, 8, 7, min_=0, max_=1, decimals=3, options=BARG, thresholds=thr)
    d.add("bargauge", "ROC-AUC", [q('fintech_model_metric{metric="roc_auc"}', "{{model}}", instant=True)], PROM, 8, 7, min_=0, max_=1, decimals=3, options=BARG, thresholds=[(None, RED), (0.7, YEL), (0.9, GREEN)])
    d.add("bargauge", "PR-AUC (average precision)", [q('fintech_model_metric{metric="pr_auc"}', "{{model}}", instant=True)], PROM, 8, 7, min_=0, max_=1, decimals=3, options=BARG, thresholds=[(None, RED), (0.4, YEL), (0.7, GREEN)])
    d.add("bargauge", "False-positive rate (lower is better)", [q('fintech_model_metric{metric="false_positive_rate"}', "{{model}}", instant=True)], PROM, 8, 7, min_=0, unit="percentunit", decimals=3,
          options=BARG, thresholds=[(None, GREEN), (0.01, YEL), (0.03, RED)])
    d.row("Confusion matrices, cost of training, calibration")
    d.add("table", "Confusion-matrix counts (test set)", [q("fintech_model_confusion", "", instant=True)], PROM, 12, 8,
          transformations=[{"id": "labelsToFields", "options": {"mode": "columns", "keepLabels": ["model", "cell"], "valueLabel": "cell"}},
                           {"id": "merge", "options": {}}])
    d.add("bargauge", "Training + tuning time (s)", [q("fintech_model_training_seconds", "{{model}}", instant=True)], PROM, 6, 8, unit="s", decimals=1, options=BARG)
    d.add("bargauge", "Decision threshold (validation F1-optimal)", [q("fintech_model_threshold", "{{model}}", instant=True)], PROM, 6, 8, min_=0, max_=1, decimals=3, options=BARG)
    d.row("Live inference")
    d.add("timeseries", "Inference latency p50 / p95 / p99 (per batch)",
          [q("histogram_quantile(0.5, sum by (le) (rate(fintech_model_inference_seconds_bucket[2m])))", "p50"),
           q("histogram_quantile(0.95, sum by (le) (rate(fintech_model_inference_seconds_bucket[2m])))", "p95", ref="B"),
           q("histogram_quantile(0.99, sum by (le) (rate(fintech_model_inference_seconds_bucket[2m])))", "p99", ref="C")],
          PROM, 12, 8, unit="s", options=LEGEND, custom=TS)
    d.add("timeseries", "Live false-positive rate (replay)", [q('sum(increase(fintech_stream_outcomes_total{outcome="fp"}[5m])) / clamp_min(sum(increase(fintech_stream_outcomes_total{outcome=~"fp|tn"}[5m])), 1)', "FPR")],
          PROM, 12, 8, unit="percentunit", decimals=2, options=LEGEND, custom=TS)
    d.row("Stored in PostgreSQL")
    d.add("table", "model_results (latest run)", [pg('SELECT model, model_type AS type, ROUND("precision"::numeric,3) AS "precision", ROUND(recall::numeric,3) AS recall, ROUND(f1::numeric,3) AS f1, ROUND(roc_auc::numeric,3) AS roc_auc, ROUND(pr_auc::numeric,3) AS pr_auc, ROUND(false_positive_rate::numeric,4) AS fpr, tp, fp, fn, tn FROM v_latest_model_results ORDER BY pr_auc DESC', fmt="table")],
          PG, 24, 8)
    d.save("model_performance.json")


def pipeline_monitoring():
    d = Dash("pipeline-monitoring", "Data Pipeline Monitoring", ["pipeline", "data-quality"])
    d.row("Run health")
    d.add("stat", "Runs (success / failure)", [q('sum(fintech_pipeline_runs_total{status=~"success|restored"})', "ok", instant=True), q('sum(fintech_pipeline_runs_total{status="failure"}) or vector(0)', "failed", instant=True, ref="B")],
          PROM, 6, 5, options={**STAT_VAL, "textMode": "value_and_name"})
    d.add("stat", "Last run duration", [q("fintech_pipeline_run_duration_seconds", instant=True)], PROM, 6, 5, unit="s", decimals=1, options=STAT_VAL)
    d.add("stat", "Validation pass rate", [q("fintech_data_validation_pass_rate", instant=True)], PROM, 6, 5, unit="percentunit", decimals=1, thresholds=[(None, RED), (0.8, YEL), (0.95, GREEN)], options=STAT)
    d.add("stat", "DB write failures", [q("sum(fintech_db_write_failures_total) or vector(0)", instant=True)], PROM, 6, 5, thresholds=[(None, GREEN), (1, RED)], options=STAT)
    d.row("Stage performance")
    d.add("bargauge", "Stage duration (s)", [q("fintech_pipeline_stage_duration_seconds", "{{stage}}", instant=True)], PROM, 8, 9, unit="s", decimals=2, options=BARG)
    d.add("bargauge", "Rows / items per stage", [q("fintech_pipeline_stage_rows", "{{stage}}", instant=True)], PROM, 8, 9, options=BARG)
    d.add("state-timeline", "Stage success (1 = ok)", [q("fintech_pipeline_stage_success", "{{stage}}")], PROM, 8, 9,
          mappings=[{"type": "value", "options": {"0": {"text": "FAIL", "color": "red"}, "1": {"text": "OK", "color": "green"}}}], options={"legend": {"showLegend": False}})
    d.row("Data quality")
    d.add("table", "Validation checks", [q("fintech_data_validation_check_passed", "", instant=True), q("fintech_data_validation_failed_rows", "", instant=True, ref="B")], PROM, 12, 10,
          transformations=[{"id": "labelsToFields", "options": {"mode": "columns", "keepLabels": ["check"]}}, {"id": "merge", "options": {}}])
    d.add("bargauge", "Cleaning row accounting", [q("fintech_data_cleaning_rows", "{{kind}}", instant=True)], PROM, 6, 10, options=BARG)
    d.add("bargauge", "Rows written to PostgreSQL", [q("fintech_db_rows_written", "{{table}}", instant=True)], PROM, 6, 10, options=BARG)
    d.add("table", "Pipeline run history (PostgreSQL)", [pg("SELECT run_id, finished_at, status, rows_raw, rows_clean, champion_model, data_hash FROM pipeline_runs ORDER BY finished_at DESC LIMIT 20", fmt="table")], PG, 24, 7)
    d.row("Structured logs (Loki)")
    d.add("timeseries", "Log volume by level", [lq('sum by (level) (count_over_time({job="fintech"}[1m]))')], LOKI, 10, 8, options=LEGEND, custom={**TS, "drawStyle": "bars", "fillOpacity": 60, "stacking": {"mode": "normal"}})
    d.add("logs", "Pipeline stage logs", [lq('{job="fintech", logger=~"pipeline|worker"}')], LOKI, 14, 8, options=LOGS)
    d.save("pipeline_monitoring.json")


def system_performance():
    d = Dash("docker-infrastructure", "Docker Infrastructure Health", ["docker", "infrastructure"])
    c = 'name=~"fintech-.+"'
    d.row("Service availability")
    d.add("stat", "Scrape targets up", [q("sum(up == 1)", "up", instant=True), q("count(up)", "total", instant=True, ref="B")], PROM, 6, 5,
          options={**STAT_VAL, "textMode": "value_and_name"})
    d.add("state-timeline", "Target status (1 = up)", [q("up", "{{job}}")], PROM, 18, 5,
          mappings=[{"type": "value", "options": {"0": {"text": "DOWN", "color": "red"}, "1": {"text": "UP", "color": "green"}}}], options={"legend": {"showLegend": False}})
    d.row("Containers (cAdvisor)")
    d.add("timeseries", "CPU usage (cores)", [q(f"sum by (name) (rate(container_cpu_usage_seconds_total{{{c}}}[1m]))", "{{name}}")], PROM, 12, 8, unit="short", options=LEGEND, custom=TS)
    d.add("timeseries", "Memory working set", [q(f"sum by (name) (container_memory_working_set_bytes{{{c}}})", "{{name}}")], PROM, 12, 8, unit="bytes", options=LEGEND, custom=TS)
    d.add("timeseries", "Network receive", [q(f"sum by (name) (rate(container_network_receive_bytes_total{{{c}}}[1m]))", "{{name}}")], PROM, 8, 8, unit="Bps", options=LEGEND, custom=TS)
    d.add("timeseries", "Network transmit", [q(f"sum by (name) (rate(container_network_transmit_bytes_total{{{c}}}[1m]))", "{{name}}")], PROM, 8, 8, unit="Bps", options=LEGEND, custom=TS)
    d.add("bargauge", "Container uptime", [q(f"time() - container_start_time_seconds{{{c}}}", "{{name}}", instant=True)], PROM, 8, 8, unit="s", options=BARG)
    d.add("timeseries", "Disk I/O (read + write)", [q(f"sum by (name) (rate(container_fs_reads_bytes_total{{{c}}}[1m]))", "read {{name}}"), q(f"sum by (name) (rate(container_fs_writes_bytes_total{{{c}}}[1m]))", "write {{name}}", ref="B")],
          PROM, 12, 8, unit="Bps", options=LEGEND, custom=TS)
    d.add("bargauge", "Container restarts (last start time age)", [q(f"changes(container_start_time_seconds{{{c}}}[1h])", "{{name}}", instant=True)], PROM, 12, 8, options=BARG, thresholds=[(None, GREEN), (1, YEL), (3, RED)])
    d.row("Platform internals")
    d.add("timeseries", "Pipeline worker RSS memory", [q('process_resident_memory_bytes{job="worker"}', "worker")], PROM, 8, 7, unit="bytes", options=LEGEND, custom=TS)
    d.add("timeseries", "Prometheus ingested samples / s", [q("rate(prometheus_tsdb_head_samples_appended_total[1m])", "samples/s")], PROM, 8, 7, unit="ops", options=LEGEND, custom=TS)
    d.add("timeseries", "Loki ingest rate (bytes/s)", [q("sum(rate(loki_distributor_bytes_received_total[1m]))", "bytes/s")], PROM, 8, 7, unit="Bps", options=LEGEND, custom=TS)
    d.add("timeseries", "Scrape duration by job", [q("scrape_duration_seconds", "{{job}}")], PROM, 12, 7, unit="s", options=LEGEND, custom=TS)
    d.add("timeseries", "Grafana HTTP requests / s", [q('sum by (code) (rate(grafana_http_request_duration_seconds_count[1m]))', "{{code}}")], PROM, 12, 7, unit="ops", options=LEGEND, custom=TS)
    d.row("Container logs")
    d.add("logs", "Errors across stack (Loki)", [lq('{job="fintech", level=~"ERROR|CRITICAL"}')], LOKI, 24, 8, options=LOGS)
    d.save("system_performance.json")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for f in (fintech_overview, fraud_detection, cybersecurity, consumer_trust, model_performance, pipeline_monitoring, system_performance):
        f()
    print("wrote", len(list(OUT.glob("*.json"))), "dashboards to", OUT)
