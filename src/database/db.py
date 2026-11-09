"""PostgreSQL persistence (SQLite fallback for local runs and tests)."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.common import ROOT, get_logger
from src.metrics import exporter as mx

log = get_logger(__name__)


def get_engine(url: str | None = None) -> Engine:
    url = url or os.environ.get("DATABASE_URL")
    if not url:
        url = f"sqlite:///{ROOT / 'data' / 'interim' / 'research.sqlite'}"
    return create_engine(url, pool_pre_ping=True, future=True)


def is_postgres(engine: Engine) -> bool:
    return engine.dialect.name == "postgresql"


def init_schema(engine: Engine) -> None:
    """Apply database/schema.sql + migrations to PostgreSQL (idempotent: IF NOT EXISTS everywhere)."""
    if not is_postgres(engine):
        return
    files = [ROOT / "database" / "schema.sql", *sorted((ROOT / "database" / "migrations").glob("*.sql"))]
    with engine.begin() as conn:
        for f in files:
            conn.exec_driver_sql(Path(f).read_text(encoding="utf-8"))


def write_table(engine: Engine, df: pd.DataFrame, table: str, replace: bool = False) -> int:
    """Append (or truncate+append) a DataFrame; failures are logged and counted, never fatal."""
    try:
        if replace:
            with engine.begin() as conn:
                try:
                    conn.execute(text(f"DELETE FROM {table}"))
                except Exception:
                    pass  # table does not exist yet (SQLite first run)
        df.to_sql(table, engine, if_exists="append", index=False, method="multi", chunksize=2000)
        mx.DB_ROWS_WRITTEN.labels(table).set(len(df))
        return len(df)
    except Exception as exc:
        mx.DB_WRITE_FAILURES.labels(table).inc()
        log.error("database write failed for %s: %s", table, exc, extra={"stage": "persist"})
        return 0


def persist_run(engine: Engine, run_id: str, s: dict, tables: dict[str, pd.DataFrame]) -> None:
    run = pd.DataFrame([{
        "run_id": run_id, "started_at": s["started_at"], "finished_at": s["finished_at"], "status": "success",
        "rows_raw": s["cleaning"]["rows_in"], "rows_clean": s["cleaning"]["rows_out"],
        "seed": s["seed"], "data_hash": s["data_hash"], "champion_model": s["models"]["champion"],
        "notes": json.dumps({"stages": {k: round(v["seconds"], 3) for k, v in s["stages"].items()}}),
    }])
    write_table(engine, run, "pipeline_runs")
    for name, df in tables.items():
        df = df.copy()
        df.insert(0, "run_id", run_id)
        write_table(engine, df, name)
