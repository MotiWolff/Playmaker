# Playmaker/services/data_cleaner/services/table_creation.py
from sqlalchemy import Table, Column, Integer, String, DateTime, MetaData, ForeignKey
from sqlalchemy.orm import Session
from ..db.postgres_conn import engine
from Playmaker.shared.logging.logger import Logger

# hierarchical name so it rolls up under "playmaker"
log = Logger.get_logger(name="playmaker.data_cleaner.table_creation")

metadata = MetaData()
teams = Table("teams", metadata, autoload_with=engine)


class GamesTable:
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.table = None

    def create_table(self):
        try:
            self.table = Table(
                self.table_name,
                metadata,
                Column("match_id", Integer, primary_key=True),
                Column("home_team_id", Integer, ForeignKey("teams.team_id"), nullable=False),
                Column("away_team_id", Integer, ForeignKey("teams.team_id"), nullable=False),
                Column("score_full_time_home", Integer),
                Column("score_full_time_away", Integer),
                Column("utc_date", DateTime),
                Column("winner", String),
                extend_existing=True,
            )
            metadata.create_all(engine)
            log.info(f"table.create.ok table={self.table_name}")
        except Exception:
            # includes stack trace
            log.exception(f"table.create.error table={self.table_name}")

    def insert_data(self, db: Session, data: list[dict]):
        try:
            db.execute(self.table.insert(), data)
            db.commit()
            rows = len(data) if data is not None else 0
            log.info(f"insert.ok table={self.table_name} rows={rows}")
        except Exception:
            # includes stack trace
            log.exception(f"insert.error table={self.table_name}")
