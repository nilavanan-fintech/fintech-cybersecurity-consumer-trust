# FinTech Cybersecurity and Consumer Trust

A reproducible, Python-based **research & development platform** for a final-year project. It studies how
cybersecurity capability (fraud detection, anomaly detection, threat monitoring) relates to **consumer trust** in
FinTech services - and exposes the live state of the whole experiment through **Prometheus, Grafana and Loki**.

> **Data & ethics.** Every security experiment runs against *synthetic* data generated inside an isolated Docker
> network, or against an optional, licensed public dataset. No real customer data, no live systems and no offensive
> tooling are involved. The bundled survey file is **synthetic** (it exercises the pipeline); replace it with real,
> consented responses for the final study (see [survey/questionnaire.md](survey/questionnaire.md)).

## Quick start

Requires Docker Desktop (8 GB RAM recommended). No `.env` is needed for a first run; `cp .env.example .env` to change passwords.

```bash
docker compose up --build
```

First start takes several minutes (image builds, then the worker generates data, tunes and trains the models).
Jupyter starts after the worker reports healthy; Grafana opens with data as soon as the first metrics are scraped.

| Service | URL | Login |
|---|---|---|
| **Grafana** (7 dashboards, alerts) | http://localhost:3000 | `admin` / `change_me_grafana` |
| **JupyterLab** (16 notebooks) | http://localhost:8888 | token `change_me_jupyter` |
| **Prometheus** (targets, rules, alerts) | http://localhost:9090 | - |
| Loki (log store) | http://localhost:3100/ready | - |
| Worker `/metrics` | http://localhost:8000/metrics | - |
| cAdvisor (container stats) | http://localhost:8081 | - |
| PostgreSQL | `localhost:5432`, db `fintech_research` | `fintech` / `change_me_postgres` |

All ports bind to `127.0.0.1` only.

## What the platform does

```
 synthetic / public data ──► validate ──► clean ──► features ──► train + tune ──► evaluate ──► risk tiers
                                                        │                              │
 security events ──► Isolation Forest ──► threat analysis                              ├─► models/ (joblib + metadata JSON)
 survey (pseudonymised) ──► Consumer Trust Score ──► Consumer Trust Index              ├─► report/ (figures, tables)
                                                                                       ├─► PostgreSQL (results & metadata)
 every stage ──► Prometheus metrics (:8000) ──► Grafana    logs (JSON) ──► Promtail ──► Loki ──► Grafana
```

* **Models:** Logistic Regression, Random Forest, XGBoost (randomised hyper-parameter search, chronological split,
  validation-tuned threshold) + Isolation Forest and Local Outlier Factor (unsupervised). Metrics: accuracy, precision,
  recall, F1, ROC-AUC, PR-AUC, confusion matrix, false-positive rate, bootstrap CIs, McNemar test.
* **Consumer trust:** 12-item Likert instrument → five-dimension Consumer Trust Score (0-100), Cronbach's α, drivers
  (Spearman, OLS), a measured Platform Security Index, and a combined Consumer Trust Index with sensitivity analysis.
* **Monitoring:** nothing in Grafana is hardcoded. Dashboards query metrics computed by the pipeline (and a live replay of
  held-out data through the trained champion model), logs in Loki, and results tables in PostgreSQL.

### Grafana dashboards (auto-provisioned, folder *FinTech Research*)

| Dashboard | Shows |
|---|---|
| FinTech Research Overview | readiness, fraud rate, champion PR-AUC, trust indices, live stream, error logs |
| Transaction & Fraud Analytics | fraud by category/hour/pattern, daily series (SQL), live precision/recall, risk tiers |
| Cybersecurity Threat Monitoring | attacks by type/severity/source, block rate, anomaly detector, campaigns |
| Consumer Trust Indicators | CTS/PSI/CTI gauges, dimensions, segments, drivers, Cronbach's α, k-anonymity |
| Machine Learning Model Performance | all metrics per model, confusion cells, training time, latency, FPR |
| Data Pipeline Monitoring | stage timing/status, validation checks, cleaning accounting, DB writes, log volume |
| Docker Infrastructure Health | target status, per-container CPU/memory/network/disk, Prometheus/Loki internals |

Alert rules: [dashboard/grafana/alerts/alert-rules.yml](dashboard/grafana/alerts/alert-rules.yml) (Grafana) and
[dashboard/prometheus/alert_rules.yml](dashboard/prometheus/alert_rules.yml) (Prometheus).

## Common tasks (`make help`)

| Task | Command |
|---|---|
| Start / stop | `make up` / `make down` (`make reset` also deletes volumes) |
| Re-run pipeline & retrain | `make pipeline` then `make retrain` (refreshes Grafana) |
| Fast smoke run (no DB) | `make smoke` |
| Run tests | `make test` |
| Execute all notebooks (store outputs) | `make notebooks` |
| Regenerate dashboards / notebooks | `make dashboards` / `make build-notebooks` |
| SQL shell | `make psql` |

Without `make` (Windows): use the `docker compose ...` commands inside the [Makefile](Makefile).

### Local (non-Docker) run

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m pytest -q
python -m src.pipeline --fast        # SQLite fallback; set DATABASE_URL for PostgreSQL
```

## Repository layout

```
analysis/        7 focused analysis notebooks (EDA, quality, transactions, threats, trust, fraud patterns, statistics)
notebooks/       01-08 research sequence: preprocessing → features → fraud → anomaly → trust → training → evaluation → visuals
survey/          questionnaire, (synthetic) survey data, analysis notebook, results write-up
src/             pipeline code (data_collection, preprocessing, feature_engineering, fraud_detection, anomaly_detection,
                 trust_scoring, model_evaluation, metrics, database) + pipeline.py and worker.py
models/          trained/ (joblib)  evaluation/ (curves, tables)  model_metadata/ (JSON, run summary)
database/        schema.sql, migrations/, seed_data/
dashboard/       grafana/ (dashboards, provisioning, alerts)  prometheus/
infrastructure/  docker/ (Dockerfiles), scripts/, loki/, promtail/
config/          settings.yaml (all experiment parameters), logging.yaml
documentation/   architecture, methodology, datasets, research questions, guides   report/  thesis chapters + references.bib
tests/           pytest suite    data/ raw, interim, processed, synthetic, external   Makefile, docker-compose.yml, requirements*.txt
```

## Documentation

[Project overview](documentation/project_overview.md) · [Architecture & data flow](documentation/system_architecture.md) ·
[Methodology](documentation/methodology.md) · [Research questions](documentation/research_questions.md) ·
[Datasets](documentation/dataset_description.md) · [Technology stack](documentation/technology_stack.md) ·
[Installation](documentation/installation_guide.md) · [Dashboard guide](documentation/dashboard_guide.md) ·
[Interfaces / metrics API](documentation/api_documentation.md) · [Report chapters](report/chapters/)

## Limitations (read before citing numbers)

Results come from synthetic data with stylised fraud patterns; they demonstrate and validate the *method*, not real-world
fraud prevalence or performance. The Consumer Trust Index is a proposed composite, not a validated psychometric scale.
See [report/chapters/chapter_6_conclusion.md](report/chapters/chapter_6_conclusion.md).
