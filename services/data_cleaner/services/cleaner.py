import pandas as pd
from sqlalchemy.orm import Session
from services.table_fetcher import TableFetcher
from services.table_creation import GamesTable
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
            "winner",
        ]
        df = pd.DataFrame(table)
        relevent_data = df[columns_to_keep]
        relevent_data = relevent_data.drop_duplicates()
        
        # Deletes a row with more than half empty values
        total_columns = relevent_data.shape[1]
        relevent_data = relevent_data[relevent_data.notna().sum(axis=1) > total_columns / 2] 

        return relevent_data.to_dict(orient="records")
    
    def save_data(self, cleaned_data: list):
        try:
            new_table = GamesTable(f'{self.table_name}_cleaned')
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
        
