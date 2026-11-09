"""Generate review_1..review_4.pptx into review/.  Run inside the Jupyter/dev image:
    docker compose run --rm --no-deps --entrypoint "" jupyter python review/scripts/build_all.py
Reviews 3 and 4 need pipeline output (models/model_metadata/last_run_summary.json, report/figures)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import review_1, review_2, review_3, review_4  # noqa: E402

if __name__ == "__main__":
    for m in (review_1, review_2, review_3, review_4):
        m.build()
