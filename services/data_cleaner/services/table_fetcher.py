# Playmaker/services/data_cleaner/services/table_fetcher.py
from sqlalchemy import MetaData, Table, select
from sqlalchemy.orm import Session
from Playmaker.shared.logging.logger import Logger

# use a hierarchical name so it rolls up under "playmaker"
log = Logger.get_logger(name="playmaker.data_cleaner.table_fetcher")


class TableFetcher:
    def __init__(self, db: Session):
        self.db = db

    def fetch_table(self, table_name: str):
        try:
            metadata = MetaData()
            table = Table(table_name, metadata, autoload_with=self.db.bind)
            query = select(table)
            data = self.db.execute(query).mappings().all()
            log.info(f"table.fetch.ok table={table_name} rows={len(data)}")
            return data
        except Exception:
            # includes stack trace; keeps behavior (no re-raise)
            log.exception(f"table.fetch.error table={table_name}")
