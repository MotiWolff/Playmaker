# services/model/data_access/uow.py
class UnitOfWork:
    """
    Simple transaction scope manager.
    Usage:
        with UnitOfWork(db) as conn:
            # execute statements using conn
    """
    def __init__(self, db):
        self._db = db
        self._conn = None
        self._txn = None

    def __enter__(self):
        self._conn = self._db.engine().connect()
        self._txn = self._conn.begin()
        return self._conn

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type:
                self._txn.rollback()
            else:
                self._txn.commit()
        finally:
            # always attempt to close
            if self._conn is not None:
                self._conn.close()
