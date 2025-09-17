import pandas as pd
from Playmaker.shared.logging.logger import Logger  # NEW
log = Logger.get_logger(name="playmaker.model.features.validators")  # NEW

REQUIRED_COLS = ["Date","HomeTeam","AwayTeam","FTHG","FTAG","FTR"]

class ColumnValidator:
    def validate(self, df: pd.DataFrame) -> None:
        log.debug("column_validator.check", extra={"have": list(df.columns), "need": REQUIRED_COLS})  # NEW
        missing = [c for c in REQUIRED_COLS if c not in df.columns]
        if missing:
            log.error("column_validator.missing", extra={"missing": missing})  # NEW
            raise ValueError(f"Missing required columns: {missing}. Got: {list(df.columns)}")
        log.debug("column_validator.ok", extra={"cols": len(df.columns)})  # NEW
