# Interfaces & programmatic API

This project has no web API/front end by design. Its interfaces are the Python modules, CLI entry points, the metrics endpoint and the SQL schema.

## CLI
| Command | Purpose |
|---|---|
| `python -m src.pipeline [--fast] [--no-db] [--n-transactions N]` | full pipeline, writes artefacts, DB and registers metrics |
| `python -m src.worker` | pipeline (if needed) + `/metrics` + live replay (container entry point) |
| `python infrastructure/scripts/generate_synthetic_data.py [--seed S] [--sample-rows N]` | generate datasets only |
| `python infrastructure/scripts/build_dashboards.py` / `build_notebooks.py` / `execute_notebooks.py` | regenerate dashboards / notebooks / execute them |

## Python modules (selected)
| Module | Function | Description |
|---|---|---|
| `src.data_collection.synthetic` | `generate_transactions`, `generate_security_events`, `generate_survey` | seeded, isolated generators |
| `src.preprocessing.validation` | `validate_transactions(df, cfg) → list[dict]` | check/pass/failed_count records |
| `src.preprocessing.cleaning` | `clean_transactions(df) → (df, report)` | |
| `src.preprocessing.anonymize` | `pseudonymise_ids`, `k_anonymity`, `enforce_k_anonymity` | survey privacy |
| `src.feature_engineering.features` | `build_features(df)`, `feature_names()`, `chronological_split` | leakage-safe |
| `src.fraud_detection.train` | `train_and_select`, `evaluate_models` | tuned LR/RF/XGB |
| `src.fraud_detection.risk` | `classify_risk`, `tier_summary` | probability → action tier |
| `src.anomaly_detection.detectors` | `fit_isolation_forest`, `fit_lof`, `iso_scores`, `lof_scores` | unsupervised |
| `src.model_evaluation.evaluate` | `evaluate_binary`, `bootstrap_ci`, plots | |
| `src.model_evaluation.statistics` | `mann_whitney`, `chi_square`, `kruskal`, `mcnemar`, `ols`, `correlation_with_p` | |
| `src.trust_scoring.scoring` | `score_respondents`, `cronbach_alpha`, `platform_security_index`, `consumer_trust_index` | |
| `src.metrics.exporter` | `publish_summary`, `instrument_stage`, Prometheus objects | |
| `src.database.db` | `get_engine`, `init_schema`, `write_table`, `persist_run` | PostgreSQL / SQLite |

Example:
```python
from src.common import load_settings
from src.pipeline import run_pipeline
summary = run_pipeline(load_settings(), use_db=False)
summary["models"]["results"]["xgboost"]["pr_auc"]
```

## Metrics endpoint
`GET http://localhost:8000/metrics` (Prometheus text format). Readiness probe: `fintech_pipeline_ready 1.0`. Metric catalogue: [dashboard_guide.md](dashboard_guide.md).

## Configuration
`config/settings.yaml` (experiment parameters; override file with `FINTECH_SETTINGS`), `config/logging.yaml`.
Environment: `DATABASE_URL`, `SURVEY_SALT`, `FORCE_RETRAIN`, `EXPORTER_PORT`, `FINTECH_LOG_DIR`, `FINTECH_ROOT`.

## Database
Tables: `pipeline_runs`, `model_results`, `model_metadata`, `data_quality_checks`, `transaction_daily_summary`, `security_daily_summary`,
`risk_tier_summary`, `trust_respondent_scores`, `survey_responses`, `ref_risk_tier_actions`. Views: `latest_run`, `v_latest_*`. See `database/schema.sql`.
```sql
SELECT model, pr_auc, recall, false_positive_rate FROM v_latest_model_results ORDER BY pr_auc DESC;
```

## Serialised artefacts
`models/trained/<name>.joblib` (scikit-learn pipelines / XGBoost), `models/model_metadata/<name>.json` (params, threshold, features, metrics,
data hash, seed, library versions), `champion.json`, `last_run_summary.json`. Load with `joblib.load`; only load artefacts you produced yourself (pickle is not safe for untrusted files).
