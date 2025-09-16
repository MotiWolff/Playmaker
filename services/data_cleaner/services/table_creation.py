from sqlalchemy import (
    Table, Column, Integer, String, DateTime, MetaData, ForeignKey
)
from sqlalchemy.orm import Session
from db.postgres_conn import engine
from shared.logging.logger import Logger

my_logger = Logger.get_logger()

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
                Column("match_id", Integer, primary_key=True),  # מזהה המשחק
                Column("home_team_id", Integer, ForeignKey('teams.team_id'), nullable=False, ),  # קבוצה ביתית
                Column("away_team_id", Integer, ForeignKey('teams.team_id'), nullable=False),  # קבוצה חוץ
                Column("score_full_time_home", Integer),  # תוצאה ביתית
                Column("score_full_time_away", Integer),  # תוצאה חוץ
                Column("utc_date", DateTime),  # תאריך ושעה
                Column("winner", String),  # מנצח
                extend_existing=True
            )
            metadata.create_all(engine)
            my_logger.info(f"New table added, table name:{self.table_name}")
        except Exception as e:
           my_logger.error(f"Error creating new table.\nError:{e}") 


    def insert_data(self, db: Session, data: list[dict]):
        try:
            db.execute(self.table.insert(), data)
            my_logger.info(f"The data was successfully inserted into the PostgreSQL database.")
        except Exception as e:
            my_logger.error(f"Faild to insert data to table:{self.table_name}.\nError:{e}")
    
