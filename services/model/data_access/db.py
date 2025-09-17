# services/model/data_access/db.py
from __future__ import annotations
from typing import Any, Dict, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from Playmaker.shared.logging.logger import Logger
log = Logger.get_logger(name="playmaker.model.data_access.db")

class Database:
    def __init__(self, cfg: Dict[str, Any]):
        self._cfg = cfg
        self._engine: Optional[Engine] = None

    def engine(self) -> Engine:
        if self._engine is None:
            try:
                log.info("db.engine.create")
                eng = create_engine(
                    self._cfg["db_dsn"],
                    pool_pre_ping=True,
                    pool_size=5,
                    max_overflow=5,
                    pool_recycle=1800,
                    pool_timeout=30,
                    future=True,
                    connect_args={"application_name": "soccer-model"},
                )
                with eng.connect() as conn:
                    conn.execute(text("SELECT 1"))
                self._engine = eng
                log.info("db.engine.ready")
            except SQLAlchemyError as e:
                log.exception("db.engine.connect_failed")
                raise ConnectionError(f"Failed to connect to database: {e}") from e
        return self._engine
