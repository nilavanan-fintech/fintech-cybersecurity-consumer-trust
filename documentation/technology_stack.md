# Technology stack

| Layer | Technology | Why |
|---|---|---|
| Language | Python 3.11 (container), tested also on 3.14 | ecosystem for data science |
| Data | pandas, NumPy, SciPy, PyArrow (Parquet) | tabular processing, statistics, columnar storage |
| ML | scikit-learn (LR, RF, IsolationForest, LOF, RandomizedSearchCV), XGBoost | justified in methodology.md §5 |
| Visualisation | Matplotlib, Seaborn, Plotly | static report figures + interactive notebooks |
| Research UI | JupyterLab 4 | interactive experiments, executed notebooks stored with outputs |
| Database | PostgreSQL 16 (SQLite fallback for local/test) via SQLAlchemy + psycopg2 | structured results & metadata |
| Metrics | prometheus-client → Prometheus 2.53 | pull-based time series, PromQL, alert rules |
| Logs | JSON logging → Promtail → Loki 3.1 | label-indexed log search next to metrics |
| Dashboards | Grafana 11.2 (file provisioning) | datasources, 7 dashboards, alert rules as code |
| Containers | Docker Compose v2, cAdvisor | one-command environment; container health metrics |
| Quality | pytest (≈30 tests), config in YAML, Makefile | repeatability |

`requirements.txt` ranges are lower-bounded by features used (e.g. pandas ≥ 2.2, SQLAlchemy ≥ 2.0, scikit-learn ≥ 1.4) and
upper-bounded at the next major release to avoid unannounced breaking changes. `requirements-dev.txt` adds Jupyter and pytest.

Deliberately not used: React/HTML front ends, static dashboards, SMOTE oversampling (distorts probabilities), deep learning
(tabular data of this size favours trees; listed as future work), Alertmanager (lab scope).
