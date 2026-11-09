# FinTech Cybersecurity & Consumer Trust - convenience targets.
# Docker targets need Docker Desktop; `local-*` targets need a Python venv:  make venv
.DEFAULT_GOAL := help
COMPOSE ?= docker compose
PY      ?= python

help:           ## list targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-16s\033[0m %s\n",$$1,$$2}'

env:            ## create .env from .env.example (keeps an existing .env)
	@test -f .env || cp .env.example .env

up:             ## build and start the whole stack (JupyterLab :8888, Grafana :3000, Prometheus :9090)
	$(COMPOSE) up --build -d
	@echo "JupyterLab http://localhost:8888 | Grafana http://localhost:3000 | Prometheus http://localhost:9090"

up-fg:          ## same as `docker compose up --build` (foreground logs)
	$(COMPOSE) up --build

down:           ## stop the stack (data volumes kept)
	$(COMPOSE) down

reset:          ## stop the stack AND delete all volumes (database, dashboards state, logs)
	$(COMPOSE) down -v

ps:             ## service status and health
	$(COMPOSE) ps

logs:           ## follow worker logs
	$(COMPOSE) logs -f worker

pipeline:       ## re-run the full research pipeline inside the worker image (fresh data, retrain, refresh DB)
	$(COMPOSE) run --rm --no-deps -e FINTECH_LOG_DIR=/app/logs worker python -m src.pipeline

retrain:        ## restart the worker with FORCE_RETRAIN=1 so Grafana metrics reflect the new run
	FORCE_RETRAIN=1 $(COMPOSE) up -d --force-recreate worker

smoke:          ## fast pipeline (15k transactions, minimal tuning) without PostgreSQL
	$(COMPOSE) run --rm --no-deps worker python -m src.pipeline --fast --no-db

test:           ## run the automated test-suite in the Jupyter image
	$(COMPOSE) run --rm --no-deps --entrypoint "" jupyter python -m pytest -q

notebooks:      ## execute every notebook in place (needs processed data from `make up`)
	$(COMPOSE) run --rm --no-deps --entrypoint "" jupyter python infrastructure/scripts/execute_notebooks.py

build-notebooks: ## regenerate notebook sources from infrastructure/scripts/build_notebooks.py
	$(PY) infrastructure/scripts/build_notebooks.py

dashboards:     ## regenerate Grafana dashboard JSON from infrastructure/scripts/build_dashboards.py
	$(PY) infrastructure/scripts/build_dashboards.py

report:         ## regenerate figures and tables (part of the pipeline) and list the report folder
	$(MAKE) pipeline
	@ls report/figures report/tables

data:           ## generate synthetic datasets only
	$(COMPOSE) run --rm --no-deps worker python infrastructure/scripts/generate_synthetic_data.py

psql:           ## open a psql shell on the research database
	$(COMPOSE) exec postgres sh -c 'psql -U $$POSTGRES_USER -d $$POSTGRES_DB'

venv:           ## create a local virtualenv with all dependencies
	$(PY) -m venv .venv && .venv/bin/pip install -r requirements-dev.txt

local-pipeline: ## run the pipeline with the local interpreter (SQLite instead of PostgreSQL)
	$(PY) -m src.pipeline

local-test:     ## run tests with the local interpreter
	$(PY) -m pytest -q

clean:          ## remove generated artefacts (keeps survey_data.csv)
	rm -rf data/raw/* data/interim/* data/processed/* data/synthetic/* models/trained/* models/evaluation/* models/model_metadata/*
	@find . -name __pycache__ -type d -prune -exec rm -rf {} +

.PHONY: help env up up-fg down reset ps logs pipeline retrain smoke test notebooks build-notebooks dashboards report data psql venv local-pipeline local-test clean
