"""Execute every notebook in place (stores outputs so they render on GitHub / in viva without re-running).

    python infrastructure/scripts/execute_notebooks.py [pattern]
Requires the pipeline artefacts (data/processed, models/trained). Fails loudly on the first broken cell.
"""
import sys
import time
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
GLOBS = ["analysis/*.ipynb", "notebooks/*.ipynb", "survey/*.ipynb"]


def main() -> int:
    pattern = sys.argv[1] if len(sys.argv) > 1 else ""
    failed = 0
    for g in GLOBS:
        for path in sorted(ROOT.glob(g)):
            if pattern not in str(path):
                continue
            nb = nbformat.read(path, as_version=4)
            t0 = time.time()
            try:
                NotebookClient(nb, timeout=900, kernel_name="python3", resources={"metadata": {"path": str(path.parent)}}).execute()
                nbformat.write(nb, path)
                print(f"OK   {path.relative_to(ROOT)}  ({time.time() - t0:.0f}s)")
            except Exception as exc:  # noqa: BLE001
                failed += 1
                print(f"FAIL {path.relative_to(ROOT)}: {str(exc)[-600:]}")
    return failed


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
