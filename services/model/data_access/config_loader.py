# services/model/data_access/config_loader.py
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
import os, re, yaml
from functools import lru_cache

_VALID_TABLE_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_\.]*$")

def _validate_tables(cfg: Dict[str, Any]) -> None:
    tables = cfg.get("tables", {})
    if not isinstance(tables, dict) or not tables:
        raise ValueError("tables section missing.")
    for k, v in tables.items():
        if not isinstance(v, str) or not _VALID_TABLE_RE.match(v):
            raise ValueError(f"Invalid table name for '{k}': {v!r}")

class ConfigService:
    def __init__(self, path: str = "services/model/config/config.yaml"):
        self.path = path

    @lru_cache(maxsize=1)
    def load(self) -> Dict[str, Any]:
        candidates = [
            Path(self.path),
            Path(__file__).resolve().parent.parent / "config" / "config.yaml",
            Path.cwd() / "services" / "model" / "config" / "config.yaml",
        ]
        last_err = None
        for cand in candidates:
            try:
                with open(cand, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
                env_dsn = os.getenv("DB_DSN")
                if env_dsn:
                    cfg["db_dsn"] = env_dsn
                if not cfg.get("db_dsn"):
                    raise ValueError("db_dsn missing and DB_DSN not set.")
                _validate_tables(cfg)
                # add to ConfigService.load() after yaml load
                tables_req = {"train", "fixtures", "predictions", "versions"}
                missing = tables_req - set((cfg.get("tables") or {}).keys())
                if missing:
                    raise ValueError(f"tables missing keys: {sorted(missing)}")
                try:
                    cfg["seed"] = int(cfg.get("seed", 42))
                except Exception:
                    raise ValueError("seed must be an integer")
                return cfg
            except FileNotFoundError as e:
                last_err = e
                continue
            except Exception as e:
                raise RuntimeError(f"Failed to parse config at '{cand}': {e}") from e
        raise FileNotFoundError("Config file not found.") from last_err
