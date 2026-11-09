"""Extract facts from the real project files (read-only). Nothing here modifies the project."""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
BUILD = Path(__file__).resolve().parent


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT)).replace("\\", "/")


def read(p) -> str:
    return (ROOT / p).read_text(encoding="utf-8", errors="replace")


def modules() -> list[dict]:
    out = []
    for p in sorted((ROOT / "src").rglob("*.py")):
        if p.name == "__init__.py":
            continue
        tree = ast.parse(p.read_text(encoding="utf-8"))
        doc = (ast.get_docstring(tree) or "").strip().splitlines()
        items = []
        for n in tree.body:
            if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and not n.name.startswith("_"):
                d = (ast.get_docstring(n) or "").strip().splitlines()
                items.append((n.name, d[0] if d else ""))
        out.append({"path": rel(p), "doc": doc[0] if doc else "", "doc_full": "\n".join(doc), "items": items,
                    "lines": len(p.read_text(encoding="utf-8").splitlines())})
    return out


def notebooks() -> list[dict]:
    out = []
    for g in ("analysis", "notebooks", "survey"):
        for p in sorted((ROOT / g).glob("*.ipynb")):
            nb = json.loads(p.read_text(encoding="utf-8"))
            cells = nb["cells"]
            title = next((("".join(c["source"]).splitlines() or [""])[0].lstrip("# ").strip() for c in cells if c["cell_type"] == "markdown"), p.stem)
            code = [c for c in cells if c["cell_type"] == "code"]
            executed = sum(1 for c in code if c.get("outputs"))
            errors = sum(1 for c in code for o in c.get("outputs", []) if o.get("output_type") == "error")
            out.append({"path": rel(p), "title": title, "cells": len(cells), "code": len(code), "with_output": executed, "errors": errors})
    return out


def dashboards() -> list[dict]:
    out = []
    for p in sorted((ROOT / "dashboard/grafana/dashboards").glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        panels = [x for x in d["panels"] if x["type"] != "row"]
        exprs = " ".join(str(t.get("expr", "")) + str(t.get("rawSql", "")) for x in panels for t in x.get("targets", []))
        out.append({"file": p.name, "uid": d["uid"], "title": d["title"], "refresh": d["refresh"], "n_panels": len(panels),
                    "panels": [(x["title"], x["type"], x["datasource"]["type"]) for x in panels],
                    "metrics": sorted(set(re.findall(r"fintech_\w+", exprs))),
                    "sources": sorted({x["datasource"]["type"] for x in panels})})
    return out


def metrics() -> list[tuple[str, str, str, str]]:
    src = read("src/metrics/exporter.py")
    res = []
    for m in re.finditer(r'(Gauge|Counter|Histogram)\(\s*"(\w+)",\s*"([^"]*)"(?:,\s*\[([^\]]*)\])?', src):
        res.append((m.group(2), m.group(1), m.group(3), (m.group(4) or "").replace('"', "")))
    return res


def compose() -> dict:
    return yaml.safe_load(read("docker-compose.yml"))


def sql_tables() -> list[tuple[str, list[str]]]:
    sql = read("database/schema.sql")
    res = []
    for m in re.finditer(r"CREATE TABLE IF NOT EXISTS (\w+) \((.*?)\n\);", sql, re.S):
        cols = [ln.strip().split()[0].strip('",') for ln in m.group(2).splitlines() if ln.strip() and not ln.strip().startswith("--") and not ln.strip().upper().startswith(("PRIMARY", "FOREIGN"))]
        res.append((m.group(1), cols))
    return res


def tests() -> list[tuple[str, list[str]]]:
    out = []
    for p in sorted((ROOT / "tests").glob("test_*.py")):
        tree = ast.parse(p.read_text(encoding="utf-8"))
        out.append((p.name, [n.name for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]))
    return out


def reviews() -> dict[str, list[tuple[str, list[str]]]]:
    from pptx import Presentation
    res = {}
    for i in range(1, 5):
        p = ROOT / "review" / f"review_{i}.pptx"
        if not p.exists():
            continue
        slides = []
        for s in Presentation(p).slides:
            texts = []
            for sh in s.shapes:
                if sh.has_text_frame and sh.text_frame.text.strip():
                    t = sh.text_frame.text.strip()
                    if "| Review" in t and t.startswith("FinTech Cybersecurity"):
                        continue          # slide footer
                    texts.extend(x.strip() for x in t.split("\n") if x.strip())
                if getattr(sh, "has_table", False) and sh.has_table:
                    for r in sh.table.rows:
                        texts.append(" | ".join(c.text for c in r.cells))
            slides.append((texts[0] if texts else "", texts[1:]))
        res[f"review_{i}"] = slides
    return res


def summary() -> dict | None:
    p = ROOT / "models/model_metadata/last_run_summary.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def run_status() -> dict:
    p = BUILD / "run_status.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def settings() -> dict:
    return yaml.safe_load(read("config/settings.yaml"))


def file_list(pattern: str) -> list[str]:
    return sorted(rel(p) for p in ROOT.glob(pattern) if p.is_file())
