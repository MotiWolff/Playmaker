import pandas as pd
from sqlalchemy.orm import Session
from services.table_fetcher import TableFetcher
from services.table_creation import CreateGamesTable


class Cleaner:

    def __init__(self, db: Session):
        self.db = db
        self.table_name = ''

    def clean_data(self, table: list):
        columns_to_keep = [
            "code",
            "competition_id",
            "country",
            "created_at",
            "current_matchday",
            "name",
            "status",
            "actual_home_score",
            "actual_away_score"
        ]
        df = pd.DataFrame(table)
        # print(df.head(20))
        relevent_data = df[columns_to_keep]
        relevent_data = relevent_data.drop_duplicates()
        
        # Deletes a row with more than half empty values
        total_columns = relevent_data.shape[1]
        relevent_data = relevent_data[relevent_data.notna().sum(axis=1) > total_columns / 2] 

        return relevent_data.to_dict(orient="records")
    
    def save_data(self, cleaned_data: list):
        new_table = CreateGamesTable(f'{self.table_name}-cleaned')
        new_table.insert_data(cleaned_data)

    def get_table(self):
        fetcher = TableFetcher(self.db)
        data = fetcher.fetch_table(self.table_name)
        return data

    def run_pipeline(self, table_name):
        self.table_name = table_name
        table = self.get_table()
        cleaned_data = self.clean_data(table)
        # self.save_data(cleaned_data)
        # return data
        
