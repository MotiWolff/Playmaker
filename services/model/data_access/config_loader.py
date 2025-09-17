# services/model/data_access/config_loader.py
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
import os, re, yaml
from functools import lru_cache

from Playmaker.shared.logging.logger import Logger
log = Logger.get_logger(name="playmaker.model.data_access.config")

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
        log.debug("config.load.start", extra={"candidates": [str(c) for c in candidates]})

        last_err = None
        for cand in candidates:
            try:
                with open(cand, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
                log.info("config.loaded", extra={"path": str(cand)})

                env_dsn = os.getenv("DB_DSN")
                if env_dsn:
                    cfg["db_dsn"] = env_dsn
                    log.info("config.db_dsn.override_env")

                if not cfg.get("db_dsn"):
                    raise ValueError("db_dsn missing and DB_DSN not set.")

                _validate_tables(cfg)

                tables_req = {"train", "fixtures", "predictions", "versions"}
                missing = tables_req - set((cfg.get("tables") or {}).keys())
                if missing:
                    # log first so you'll see which keys were missing
                    log.error("config.tables.missing_keys", extra={"missing": sorted(missing)})
                    raise ValueError(f"tables missing keys: {sorted(missing)}")

                try:
                    cfg["seed"] = int(cfg.get("seed", 42))
                except Exception:
                    log.error("config.seed.invalid", extra={"value": cfg.get("seed")})
                    raise ValueError("seed must be an integer")
                else:
                    log.debug("config.seed.set", extra={"seed": cfg["seed"]})

                log.debug("config.load.success")
                return cfg

            except FileNotFoundError as e:
                last_err = e
                log.debug("config.candidate_not_found", extra={"path": str(cand)})
                continue
            except Exception as e:
                # include the candidate so you can pinpoint which file failed to parse
                log.exception("config.parse_failed", extra={"path": str(cand)})
                raise RuntimeError(f"Failed to parse config at '{cand}': {e}") from e

        log.error("config.not_found", extra={"last_error": str(last_err) if last_err else None})
        raise FileNotFoundError("Config file not found.") from last_err
