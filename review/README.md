# Monthly review presentations

Four editable PowerPoint decks (16:9, shared navy/teal theme, native shapes, tables and charts - nothing is a flattened image except real figures produced by the pipeline) for the monthly academic progress reviews.

| File | Month | Content | Uses pipeline results? |
|---|---|---|---|
| `review_1.pptx` | 1 | Introduction, problem statement, objectives, literature survey, research gap, proposed solution, plan, ethics | No (planning only) |
| `review_2.pptx` | 2 | Methodology workflow, system architecture, technology stack, datasets, preprocessing, initial implementation progress, evaluation plan | No (no model results claimed) |
| `review_3.pptx` | 3 | ML implementation, fraud and anomaly detection flow, preliminary experiments, trust scoring, Grafana development, issues and next steps | Yes - first-run numbers, labelled preliminary |
| `review_4.pptx` | 4 | Completed implementation, final architecture, model comparison, metrics, statistics, risk tiers, security/trust results, dashboards, conclusions, limitations, future work | Yes |

## Integrity rules
* Decks 3 and 4 read `models/model_metadata/last_run_summary.json` and `report/figures/*.png` produced by the pipeline. If these are missing the build **fails** rather than inserting placeholder numbers.
* All results come from synthetic data and a synthetic survey; slides say so. Do not present them as findings about real consumers.
* Grafana screenshots are included only if you add real captures to `review/assets/` (`grafana_overview.png`, `grafana_pipeline.png`, `grafana_fraud.png`, `grafana_models.png`, `grafana_infra.png`). Otherwise the slide is omitted or replaced by a demo-plan slide.
* Student name, register number, guide and institution are bracketed placeholders on each title slide - edit them.
* Progressive timeline: reviews 1-2 describe design and the implemented foundations; reviews 3-4 report experiments. Adjust wording to match what you have actually completed in each month.

## Regenerate
```bash
# 1. run the pipeline so results exist (docker compose up --build, or: make pipeline)
# 2. build the decks inside the dev image (needs python-pptx, in requirements-dev.txt)
docker compose run --rm --no-deps --entrypoint "" jupyter python review/scripts/build_all.py
```
Scripts: `review/scripts/theme.py` (theme and slide helpers), `review_1.py` ... `review_4.py` (content), `build_all.py`.
