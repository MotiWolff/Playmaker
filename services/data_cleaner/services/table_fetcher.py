from sqlalchemy import MetaData, Table, select
from sqlalchemy.orm import Session
from shared.logging.logger import Logger

my_logger = Logger.get_logger()


class TableFetcher:
    def __init__(self, db: Session):
        self.db = db

    def fetch_table(self, table_name: str):
        try:
            metadata = MetaData()
            table = Table(table_name, metadata, autoload_with=self.db.bind)
            query = select(table)
            data = self.db.execute(query).mappings().all()
            my_logger.info(f"The {table_name} data table successfully pulled from database.")
            return data
        except Exception as e:
            my_logger.error(f"Error fetching table {table_name} from database.\nError:{e}")
