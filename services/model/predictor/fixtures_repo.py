from __future__ import annotations
from typing import Dict, Optional
import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
from services.model.data_access import Database  # facade
from Playmaker.shared.logging.logger import Logger

log = Logger.get_logger(name="playmaker.model.predictor.fixtures_repo")

def get_team_lookup(cfg: Dict[str, any]) -> pd.DataFrame:
    sql = "SELECT team_id, name FROM teams;"
    eng = Database(cfg).engine()
    df = pd.read_sql_query(sql, eng)
    log.debug("fixtures_repo.team_lookup", extra={"rows": len(df)})
    return df

class FixturesRepositoryDB:
    """
    Read scheduled fixtures and return fixture_id, match_utc, home_name, away_name.
    Works even if the fixture table does NOT have name columns.
    """
    def __init__(self, cfg: Dict[str, any]):
        self.cfg = cfg

    def list_scheduled(self, limit: Optional[int] = None) -> pd.DataFrame:
        table = self.cfg["tables"]["fixtures"]  # e.g. "fixture"
        sql = f"""
            SELECT f.fixture_id,
                   f.match_utc,
                   th.name AS home_name,
                   ta.name AS away_name
            FROM {table} f
            LEFT JOIN teams th ON th.team_id = f.home_team_id
            LEFT JOIN teams ta ON ta.team_id = f.away_team_id
            WHERE f.status = 'SCHEDULED'
            ORDER BY f.match_utc
            {f"LIMIT {int(limit)}" if limit else ""}
        """
        eng = Database(self.cfg).engine()
        try:
            df = pd.read_sql_query(sql, eng)
        except SQLAlchemyError as e:
            log.exception("fixtures_repo.db_read_failed", extra={"table": table})
            raise RuntimeError(f"Failed to read fixtures from '{table}': {e}") from e
        df["home_name"] = df["home_name"].fillna("HOME_UNKNOWN")
        df["away_name"] = df["away_name"].fillna("AWAY_UNKNOWN")
        log.info("fixtures_repo.list_scheduled", extra={"rows": len(df), "limit": limit})
        return df
