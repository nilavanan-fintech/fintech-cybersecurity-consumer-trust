# Chapter 4 - Implementation

## 4.1 Architecture
Seven-service Docker Compose stack (PostgreSQL, worker, JupyterLab, Prometheus, Loki + Promtail, cAdvisor, Grafana); diagrams in
[`documentation/system_architecture.md`](../../documentation/system_architecture.md).

## 4.2 Pipeline
`src/pipeline.py` runs timed stages: collect → validate → clean → features → train → evaluate → anomaly → security → risk → trust → persist → (external benchmark) → report → database.
Artefacts: joblib models with JSON metadata (parameters, threshold, features, metrics, data hash, seed, versions), figures and tables, PostgreSQL rows.

## 4.3 Observability
`src/metrics/exporter.py` publishes metrics derived from the actual run. After training, `src/worker.py` replays the held-out test partition in batches through the
champion model, incrementing counters (TP/FP/FN/TN, risk tiers, latency histogram), so live precision and recall in Grafana are computed, not hard-coded.
Structured JSON logs reach Loki through Promtail. Seven dashboards and five alert rules are provisioned from files.

## 4.4 Quality assurance
pytest covers validation, cleaning, leakage-freedom of features, metric correctness, reproducibility, scoring, reliability and statistics helpers.
Container health checks enforce start-up order (worker healthy only when `fintech_pipeline_ready = 1`).

## 4.5 Reproducibility
Seeds in `config/settings.yaml`; `docker compose up --build` reproduces the environment; notebooks consume the same artefacts via `src/notebook_utils.py`.
