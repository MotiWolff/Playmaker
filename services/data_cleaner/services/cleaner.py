"""
Module for cleaning and processing raw match data.

Provides the Cleaner class which fetches a table from the database,
cleans the data, and saves it into a new table.
"""

from typing import List, Dict
import pandas as pd
from sqlalchemy.orm import Session
from services.table_fetcher import TableFetcher
from services.table_creation import GamesTable
from shared.logging.logger import Logger

my_logger = Logger.get_logger()


class Cleaner:
    """
    Class for cleaning raw match data from a database table and saving it.

    Attributes:
        db (Session): SQLAlchemy session for database operations.
        table_name (str): Name of the table to clean.
    """

    def __init__(self, db: Session, table_name: str):
        """
        Initialize the Cleaner with a database session and table name.

        Args:
            db (Session): SQLAlchemy session instance.
            table_name (str): Name of the table to clean.
        """
        self.db = db
        self.table_name = table_name

    def clean_data(self, table: List[Dict]) -> List[Dict]:
        """
        Clean the raw table data.

        Steps:
            - Keep only relevant columns.
            - Remove duplicate rows.
            - Remove rows with more than half missing values.

        Args:
            table (List[Dict]): Raw table data fetched from the database.

        Returns:
            List[Dict]: Cleaned data ready for insertion into a new table.
        """
        columns_to_keep = [
            "away_team_id",
            "home_team_id",
            "match_id",
            "score_full_time_away",
            "score_full_time_home",
            "utc_date",
            "winner",
        ]
        df = pd.DataFrame(table)
        relevant_data = df[columns_to_keep]
        relevant_data = relevant_data.drop_duplicates()
        
        # Deletes a row with more than half empty values
        total_columns = relevant_data.shape[1]
        relevant_data = relevant_data[relevant_data.notna().sum(axis=1) > total_columns / 2]

        return relevant_data.to_dict(orient="records")

    def save_data(self, cleaned_data: List[Dict]):
        """
        Save the cleaned data into a new table.

        Args:
            cleaned_data (List[Dict]): Data after cleaning.

        Logs:
            Info: Table created and data inserted successfully.
            Error: Any exception during table creation or data insertion.
        """
        try:
            new_table = GamesTable(f"{self.table_name}_cleaned")
            new_table.create_table()
            new_table.insert_data(self.db, cleaned_data)
        except Exception as e:
            my_logger.error(f"Failed to save a new table '{self.table_name}_cleaned'.\nError: {e}")
            raise

    def get_table(self) -> List[Dict]:
        """
        Fetch the raw table from the database.

        Returns:
            List[Dict]: Raw table data.
        """
        fetcher = TableFetcher(self.db)
        data = fetcher.fetch_table(self.table_name)
        return data

    def run_pipeline(self) -> Dict:
        """
        Run the full cleaning pipeline: fetch, clean, and save.

        Logs:
            Info: Start and completion of the cleaning process.
            Error: Any exception during the pipeline execution.

        Returns:
            Dict: Response indicating completion of the pipeline.
        """
        try:
            my_logger.info(f"Cleaner started for table '{self.table_name}'.")
            table = self.get_table()
            cleaned_data = self.clean_data(table)
            self.save_data(cleaned_data)
            my_logger.info(f"Cleaning process for '{self.table_name}' completed successfully.")
            return {"response": f"Table '{self.table_name}' cleaned and saved successfully."}
        except Exception as e:
            my_logger.error(f"Cleaner failed for table '{self.table_name}'.\nError: {e}")
            raise
