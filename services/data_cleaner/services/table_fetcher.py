from sqlalchemy import MetaData, Table, select
from sqlalchemy.orm import Session

class TableFetcher:
    def __init__(self, db: Session):
        self.db = db

    def fetch_table(self, table_name: str):
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=self.db.bind)
        query = select(table)
        return self.db.execute(query).mappings().all()

