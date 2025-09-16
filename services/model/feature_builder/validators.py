import pandas as pd

REQUIRED_COLS = ["Date","HomeTeam","AwayTeam","FTHG","FTAG","FTR"]

class ColumnValidator:
    def validate(self, df: pd.DataFrame) -> None:
        missing = [c for c in REQUIRED_COLS if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}. Got: {list(df.columns)}")
