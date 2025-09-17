# services/model/data_access/uow.py
from __future__ import annotations
from typing import Optional
from sqlalchemy.engine import Connection
from Playmaker.shared.logging.logger import Logger

log = Logger.get_logger(name="playmaker.model.data_access.uow")


class UnitOfWork:
    """
    Simple transaction scope manager.
    Usage:
        with UnitOfWork(db) as conn:
            # execute statements using conn
    """
    def __init__(self, db):
        self._db = db
        self._conn: Optional[Connection] = None
        self._txn = None

    def __enter__(self) -> Connection:
        self._conn = self._db.engine().connect()
        self._txn = self._conn.begin()
        log.debug("uow.opened")
        return self._conn

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type:
                log.error(
                    "uow.rollback",
                    extra={"exc_type": getattr(exc_type, "__name__", str(exc_type))}
                )
                try:
                    self._txn.rollback()
                except Exception:
                    log.exception("uow.rollback_failed")
            else:
                log.debug("uow.commit")
                try:
                    self._txn.commit()
                except Exception:
                    log.exception("uow.commit_failed")
                    raise
        finally:
            if self._conn is not None:
                try:
                    self._conn.close()
                    log.debug("uow.closed")
                except Exception:
                    log.exception("uow.close_failed")
