# services/model/data_access/readers.py
from __future__ import annotations
from typing import Any, Dict, Iterable, Optional, Sequence
import pandas as pd
from sqlalchemy.exc import SQLAlchemyError

class MatchReader:
    """
    Reads historical matches for training in a football-data.co.uk shaped frame:
    Columns: Date, HomeTeam, AwayTeam, FTHG, FTAG, FTR
    (derived from your normalized 'match_clean' table + teams lookup)
    """
    def __init__(self, db, cfg: Dict[str, Any]):
        self.db = db
        self.cfg = cfg

    def read_match_clean(self, columns: Optional[Sequence[str]] = None) -> pd.DataFrame:
        table = self.cfg["tables"]["train"]
        # Safer approach: always select *, subset in pandas
        sql = f"SELECT * FROM {table} ORDER BY match_date;"
        try:
            df = pd.read_sql_query(sql, self.db.engine())
            if columns:
                missing = [c for c in columns if c not in df.columns]
                if missing:
                    raise KeyError(f"Columns not found in {table}: {missing}")
                df = df[list(columns)]
            return df
        except SQLAlchemyError as e:
            raise RuntimeError(f"Failed to read '{table}': {e}") from e

    def read_training_frame(self) -> pd.DataFrame:
        """
        Return a minimal, legacy-friendly training set with the classic columns.
        Requires:
          - tables.train (match_clean): match_date, home_team_id, away_team_id, home_goals, away_goals, result
          - teams: team_id, name
        """
        t_train = self.cfg["tables"]["train"]
        sql = f"""
            SELECT
                mc.match_date AS "Date",
                th.name       AS "HomeTeam",
                ta.name       AS "AwayTeam",
                mc.home_goals AS "FTHG",
                mc.away_goals AS "FTAG",
                CASE
                  -- already compact labels
                  WHEN UPPER(mc.result) IN ('H','D','A') THEN UPPER(mc.result)
                  -- long-form labels
                  WHEN UPPER(mc.result) = 'HOME_WIN' THEN 'H'
                  WHEN UPPER(mc.result) = 'AWAY_WIN' THEN 'A'
                  WHEN UPPER(mc.result) = 'DRAW'     THEN 'D'
                  -- derive from goals if present
                  WHEN mc.home_goals IS NOT NULL AND mc.away_goals IS NOT NULL THEN
                       CASE
                         WHEN mc.home_goals > mc.away_goals THEN 'H'
                         WHEN mc.home_goals < mc.away_goals THEN 'A'
                         ELSE 'D'
                       END
                  ELSE NULL
                END           AS "FTR"
            FROM {t_train} mc
            JOIN teams th ON th.team_id = mc.home_team_id
            JOIN teams ta ON ta.team_id = mc.away_team_id
            ORDER BY mc.match_date;
        """
        try:
            return pd.read_sql_query(sql, self.db.engine())
        except SQLAlchemyError as e:
            raise RuntimeError(f"Failed to read training frame from '{t_train}': {e}") from e


class FixtureReader:
    """
    Reads upcoming fixtures from the 'fixtures' table configured in YAML.
    Assumes:
      - status = 'SCHEDULED'
      - date column named 'match_utc' (TIMESTAMPTZ, UTC). If yours differs, adjust here or in YAML.
    """
    def __init__(self, db, cfg: Dict[str, Any]):
        self.db = db
        self.cfg = cfg

    def read_scheduled(self) -> pd.DataFrame:
        table = self.cfg["tables"]["fixtures"]
        sql = f"""
            SELECT *
            FROM {table}
            WHERE status = 'SCHEDULED'
            ORDER BY match_utc;
        """
        try:
            return pd.read_sql_query(sql, self.db.engine())
        except SQLAlchemyError as e:
            raise RuntimeError(f"Failed to read scheduled fixtures from '{table}': {e}") from e
