# Playmaker/services/data_cleaner/services/cleaner.py
from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session
from .table_fetcher import TableFetcher
from .table_creation import GamesTable
from Playmaker.shared.logging.logger import Logger

# use a specific, hierarchical name so logs roll up under "playmaker"
log = Logger.get_logger(name="playmaker.data_cleaner.cleaner")


class Cleaner:
    def __init__(self, db: Session, table_name: str):
        self.db = db
        self.table_name = table_name

    def clean_data(self, table: list):
        # telemetry: input size
        in_rows = len(table) if table is not None else 0
        log.info(f"clean_data.start table={self.table_name} in_rows={in_rows}")

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

        out_rows = len(safe_df)
        dropped = max(in_rows - out_rows, 0)
        log.info(f"clean_data.done table={self.table_name} out_rows={out_rows} dropped={dropped}")
        return safe_df.to_dict(orient="records")

    def save_data(self, cleaned_data: list):
        try:
            rows = len(cleaned_data) if cleaned_data is not None else 0
            log.info(f"save_data.start table=matches_cleaned rows={rows}")
            new_table = GamesTable('matches_cleaned')
            new_table.create_table()
            new_table.insert_data(self.db, cleaned_data)
            log.info("save_data.ok table=matches_cleaned")
        except Exception as e:
            # include traceback
            log.error("save_data.error table=matches_cleaned", exc_info=True)
            # keep existing behavior (re-raising not required here)

    def get_table(self):
        log.info(f"fetch_table.start table={self.table_name}")
        fetcher = TableFetcher(self.db)
        data = fetcher.fetch_table(self.table_name)
        count = len(data) if data is not None else 0
        log.info(f"fetch_table.ok table={self.table_name} rows={count}")
        return data

    def run_pipeline(self):
        try:
            log.info(f"pipeline.start table={self.table_name}")
            table = self.get_table()
            cleaned_data = self.clean_data(table)
            response = self.save_data(cleaned_data)
            log.info(f"pipeline.done table={self.table_name}")
            return {"response": response}
        except Exception as e:
            # include traceback for debugging
            log.error(f"pipeline.error table={self.table_name}", exc_info=True)
            # keep existing behavior (swallow vs. re-raise as you prefer)
