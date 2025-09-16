import pandas as pd
from sqlalchemy.orm import Session
from .table_fetcher import TableFetcher
from .table_creation import GamesTable
from shared.logging.logger import Logger

my_logger = Logger.get_logger()


class Cleaner:

    def __init__(self, db: Session, table_name: str):
        self.db = db
        self.table_name = table_name

    def clean_data(self, table: list):
        columns_to_keep = [
            "away_team_id",
            "home_team_id",
            "match_id",
            "score_full_time_away",
            "score_full_time_home",
            "utc_date",
            "score_winner",
        ]
        df = pd.DataFrame(table)
        # keep only relevant columns and normalize names
        relevent_data = df[columns_to_keep].rename(columns={
            "score_winner": "winner",
        })
        # coerce dtypes and drop invalid rows
        # coerce numeric types strictly
        for col in ["match_id", "home_team_id", "away_team_id"]:
            if col in relevent_data.columns:
                relevent_data[col] = pd.to_numeric(relevent_data[col], errors="coerce").astype("Int64")
        for col in ["score_full_time_home", "score_full_time_away"]:
            if col in relevent_data.columns:
                relevent_data[col] = pd.to_numeric(relevent_data[col], errors="coerce").astype("Int64")
        # drop rows missing required IDs
        relevent_data = relevent_data.dropna(subset=["match_id", "home_team_id", "away_team_id"])        
        relevent_data = relevent_data.drop_duplicates()
        
        # Deletes a row with more than half empty values
        total_columns = relevent_data.shape[1]
        relevent_data = relevent_data[relevent_data.notna().sum(axis=1) > total_columns / 2] 

        # replace pandas NA with None for DB insertion
        safe_df = relevent_data.where(pd.notna(relevent_data), None)
        return safe_df.to_dict(orient="records")
    
    def save_data(self, cleaned_data: list):
        try:
            # write canonical cleaned matches table
            new_table = GamesTable('matches_cleaned')
            new_table.create_table()
            new_table.insert_data(self.db, cleaned_data)
        except Exception as e:
            my_logger.error(f"Failed to save a new table.")

    def get_table(self):
        fetcher = TableFetcher(self.db)
        data = fetcher.fetch_table(self.table_name)
        return data

    def run_pipeline(self):
        try:
            my_logger.info(f"The cleaner start to clean {self.table_name} table.") 
            table = self.get_table()
            cleaned_data = self.clean_data(table)
            response = self.save_data(cleaned_data)
            my_logger.info(f"The cleaning process has completed successfully.")
            return {"response" : response}
        except Exception as e:
            my_logger.error(f"Error ocorce, cleaner failed to clean.\nError:{e}")
        
