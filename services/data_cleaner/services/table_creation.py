from sqlalchemy import (
    Table, Column, Integer, String, Date, Time, ForeignKey, MetaData
)
from sqlalchemy.orm import Session
from db.postgres_conn import engine, SessionLocal

metadata = MetaData()

class CreateGamesTable:
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.table = Table(
            table_name,
            metadata,
            Column("match_id", Integer, primary_key=True),
            Column("matchday", Integer, nullable=False),
            Column("match_date", Date, nullable=False),
            Column("match_time", Time, nullable=False),
            Column("home_team_id", Integer, ForeignKey("teams.team_id"), nullable=False),
            Column("away_team_id", Integer, ForeignKey("teams.team_id"), nullable=False),
            Column("status", String(20)),
            Column("actual_home_score", Integer),
            Column("actual_away_score", Integer),
            extend_existing=True
        )
        respons = metadata.create_all(engine)
        return respons
    
    def insert_data(self, db: Session, data: list[dict]):
        with db.begin():
            db.execute(self.table.insert(), data)

    
