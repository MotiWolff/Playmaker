"""
Module for fetching data from database tables using SQLAlchemy.

Provides the TableFetcher class to query tables dynamically and return
results as a list of dictionaries. Metadata is reused for efficiency.
"""

from typing import List, Dict
from sqlalchemy import MetaData, Table, select
from sqlalchemy.orm import Session
from shared.logging.logger import Logger

my_logger = Logger.get_logger()


class TableFetcher:
    """
    Class to fetch data from database tables dynamically by table name.

    Attributes:
        db (Session): SQLAlchemy session for database access.
        metadata (MetaData): Reusable metadata object to avoid reloading.
    """

    def __init__(self, db: Session):
        """
        Initialize the TableFetcher with a database session.

        Args:
            db (Session): SQLAlchemy session instance.
        """
        self.db = db
        self.metadata = MetaData()

    def fetch_table(self, table_name: str) -> List[Dict]:
        """
        Fetch all data from the specified table.

        Args:
            table_name (str): Name of the table to fetch data from.

        Returns:
            List[Dict]: A list of rows represented as dictionaries.

        Raises:
            Exception: Propagates any exceptions encountered during fetching.

        Logs:
            Info: Successful fetch of table data.
            Error: Any exception that occurs during table fetch.
        """
        try:
            table = Table(table_name, self.metadata, autoload_with=self.db.bind)
            query = select(table)
            data = self.db.execute(query).mappings().all()
            my_logger.info(f"Successfully fetched data from table '{table_name}'.")
            return data
        except Exception as e:
            my_logger.error(f"Error fetching table '{table_name}' from database.\nError: {e}")
            raise
