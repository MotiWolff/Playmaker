"""
Module for managing the 'games' table in PostgreSQL using SQLAlchemy.

Provides the GamesTable class to create a table dynamically and insert data.
"""

from typing import List, Dict
from sqlalchemy import Table, Column, Integer, String, DateTime, MetaData, ForeignKey
from sqlalchemy.orm import Session
from db.postgres_conn import engine
from shared.logging.logger import Logger

my_logger = Logger.get_logger()

metadata = MetaData()
teams = Table("teams", metadata, autoload_with=engine)


class GamesTable:
    """
    Class to manage a 'games' table in the database.

    Attributes:
        table_name (str): The name of the table to manage.
        table (Table): SQLAlchemy Table object, initialized after creation.
    """

    def __init__(self, table_name: str):
        """
        Initialize the GamesTable with the table name.

        Args:
            table_name (str): Name of the table to create/manage.
        """
        self.table_name = table_name
        self.table: Table = None

    def create_table(self):
        """
        Create the 'games' table with predefined columns in the database.

        Columns include match_id, home_team_id, away_team_id, scores,
        date/time, and winner.

        Logs:
            Info: Table successfully created.
            Error: Any exception during table creation.
        """
        try:
            self.table = Table(
                self.table_name,
                metadata,
                Column("match_id", Integer, primary_key=True),  # Game ID
                Column("home_team_id", Integer, ForeignKey('teams.team_id'), nullable=False),  # Home team
                Column("away_team_id", Integer, ForeignKey('teams.team_id'), nullable=False),  # Away team
                Column("score_full_time_home", Integer),  # Home score
                Column("score_full_time_away", Integer),  # Away score
                Column("utc_date", DateTime),  # Match date/time
                Column("winner", String),  # Winner
                extend_existing=True
            )
            metadata.create_all(engine)
            my_logger.info(f"New table added, table name: {self.table_name}")
        except Exception as e:
            my_logger.error(f"Error creating new table '{self.table_name}'.\nError: {e}")
            raise

    def insert_data(self, db: Session, data: List[Dict]):
        """
        Insert data into the table.

        Args:
            db (Session): SQLAlchemy session used to execute the insert.
            data (List[Dict]): List of dictionaries, each representing a row.

        Logs:
            Info: Data successfully inserted.
            Error: Any exception during data insertion.
        """
        try:
            db.execute(self.table.insert(), data)
            my_logger.info(f"Data successfully inserted into table '{self.table_name}'.")
        except Exception as e:
            my_logger.error(f"Failed to insert data into table '{self.table_name}'.\nError: {e}")
            raise
