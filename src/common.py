"""Shared helpers: project paths, settings, structured (JSON) logging."""
from __future__ import annotations

import json
import logging
import logging.config
import os
from pathlib import Path

import yaml

ROOT = Path(os.environ.get("FINTECH_ROOT", Path(__file__).resolve().parents[1]))


def load_settings(path: str | os.PathLike | None = None) -> dict:
    p = Path(path or os.environ.get("FINTECH_SETTINGS", ROOT / "config" / "settings.yaml"))
    with open(p, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def resolve(cfg: dict, key: str) -> Path:
    """Absolute, created directory for a key under cfg['paths']."""
    p = ROOT / cfg["paths"][key]
    p.mkdir(parents=True, exist_ok=True)
    return p


class JsonFormatter(logging.Formatter):
    """One JSON object per line -> parsed by Promtail, queried in Loki."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key in ("stage", "run_id", "model", "event"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


_configured = False


def setup_logging() -> None:
    global _configured
    if _configured:
        return
    log_dir = Path(os.environ.get("FINTECH_LOG_DIR", ROOT / "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    with open(ROOT / "config" / "logging.yaml", encoding="utf-8") as fh:
        conf = yaml.safe_load(fh)
    conf["handlers"]["file"]["filename"] = str(log_dir / "fintech.log")
    logging.config.dictConfig(conf)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)
