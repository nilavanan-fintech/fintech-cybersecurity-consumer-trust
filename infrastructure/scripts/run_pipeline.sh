#!/usr/bin/env bash
# Run the full research pipeline (inside the worker container or a local venv).
set -euo pipefail
cd "$(dirname "$0")/../.."
python -m src.pipeline "$@"
