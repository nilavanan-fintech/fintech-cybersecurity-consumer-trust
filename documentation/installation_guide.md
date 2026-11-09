# Installation & operation guide

## Prerequisites
* Docker Desktop (Windows/macOS) or Docker Engine + Compose v2, ~8 GB RAM, ~6 GB free disk. Windows: WSL2 backend.
* Optional: `make` (Git Bash / WSL / macOS / Linux) - otherwise run the equivalent `docker compose` commands.

## 1. Start everything
```bash
git clone https://github.com/nilavanan-fintech/fintech-cybersecurity-consumer-trust.git
cd fintech-cybersecurity-consumer-trust
cp .env.example .env        # optional: change passwords / ports
docker compose up --build
```
Timeline: image builds (≈5-10 min first time) → PostgreSQL healthy → **worker** generates data, validates, cleans, builds features,
tunes + trains models, evaluates, writes `models/`, `report/`, PostgreSQL, publishes metrics (≈2-6 min depending on CPU, `fintech_pipeline_ready = 1`)
→ Jupyter starts. Grafana, Prometheus, Loki, cAdvisor start independently.

| Endpoint | URL |
|---|---|
| Grafana | http://localhost:3000 (admin / value of `GRAFANA_ADMIN_PASSWORD`, default `change_me_grafana`) |
| JupyterLab | http://localhost:8888 (token = `JUPYTER_TOKEN`, default `change_me_jupyter`) |
| Prometheus | http://localhost:9090 (Status → Targets should show 5 UP) |
| Worker metrics | http://localhost:8000/metrics |

## 2. Run, train, evaluate, report
| Goal | Command |
|---|---|
| Re-run the whole pipeline (new data, retrain, refresh DB/report) | `make pipeline` then `make retrain` |
| Quick check without DB | `make smoke` |
| Change experiment parameters | edit `config/settings.yaml` (e.g. `tuning.n_iter: 30`, `synthetic.n_transactions: 200000`) then `make pipeline && make retrain` |
| Execute all notebooks and store outputs | `make notebooks` (or open them in Jupyter: *Run → Run All*) |
| Generate report assets | produced by every pipeline run in `report/figures/` and `report/tables/` (`results_summary.md`) |
| Run tests | `make test` |
| Inspect results in SQL | `make psql` → `SELECT * FROM v_latest_model_results;` |

## 3. Monitor
Grafana → *Dashboards → FinTech Research*. Metrics refresh every 5-10 s; the *live stream* panels move because the worker keeps
scoring held-out transactions. See [dashboard_guide.md](dashboard_guide.md).

## 4. Stop / reset
`make down` keeps data; `make reset` removes all volumes (PostgreSQL, Prometheus, Loki, Grafana state). Generated files in
`data/`, `models/`, `report/` are on the host and are removed with `make clean`.

## 5. Troubleshooting
| Symptom | Fix |
|---|---|
| Jupyter not up yet | it waits for the worker health check - `docker compose logs -f worker` |
| Grafana panel "No data" right after start | wait for first scrape (≤10 s) and for `fintech_pipeline_ready`; check Prometheus *Targets* |
| Container panels empty | cAdvisor needs the Docker socket/cgroup mounts; on some hosts `name` labels are missing - see Prometheus query `container_cpu_usage_seconds_total` |
| Port already in use | change the `*_PORT` variable in `.env` |
| `password authentication failed` after changing `.env` | the DB volume keeps the old password: `make reset` |
| Passwords containing `@ : /` | URL-encode them in `DATABASE_URL`, or avoid those characters |
| Want real fraud data | place `creditcard.csv` in `data/external/` (see data/README.md) and `make pipeline` |

## 6. Local development without Docker
```bash
python -m venv .venv && . .venv/bin/activate && pip install -r requirements-dev.txt
python -m pytest -q && python -m src.pipeline --fast
```
Uses SQLite (`data/interim/research.sqlite`) unless `DATABASE_URL` is set. Note: some Windows policies (Application Control /
Smart App Control) block unsigned Python native extensions in virtual environments; use the Docker workflow in that case.
