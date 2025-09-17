import pandas as pd
from Playmaker.shared.logging.logger import Logger
log = Logger.get_logger(name="playmaker.model.features.merge")

class PreMatchMerger:
    """
    Merges per-team rolling features back to the per-match wide frame.
    """
    HOME_MAP = {
        "form5": "home_form5",
        "gf10": "home_gf10",
        "ga10": "home_ga10",
        "shots5": "home_shots5",
        "corn5": "home_corn5",
        "yel5": "home_yel5",
        "red5": "home_red5",
        "n_prior": "home_n_prior",
        "rest_days": "home_rest_days",
    }
    AWAY_MAP = {
        "form5": "away_form5",
        "gf10": "away_gf10",
        "ga10": "away_ga10",
        "shots5": "away_shots5",
        "corn5": "away_corn5",
        "yel5": "away_yel5",
        "red5": "away_red5",
        "n_prior": "away_n_prior",
        "rest_days": "away_rest_days",
    }

    def merge(self, df: pd.DataFrame, pre: pd.DataFrame) -> pd.DataFrame:
        m = df.reset_index(drop=True).copy()
        if "match_key" not in m.columns:
            m["match_key"] = m.index.astype(int)

        cols_keep = ["match_key","team","is_home","form5","gf10","ga10","shots5","corn5","yel5","red5","n_prior","rest_days"]
        missing = [c for c in cols_keep if c not in pre.columns]
        if missing:
            log.error("merge.missing_columns_in_pre", extra={"missing": missing})
            raise ValueError(f"Pre features missing columns: {missing}")

        pre = pre[cols_keep].copy()
        home_rows = pre[pre["is_home"]].drop(columns=["team","is_home"]).rename(columns=self.HOME_MAP)
        away_rows = pre[~pre["is_home"]].drop(columns=["team","is_home"]).rename(columns=self.AWAY_MAP)

        m = m.merge(home_rows, on="match_key", how="left").merge(away_rows, on="match_key", how="left")
        log.debug("merge.done", extra={"rows": len(m), "cols": list(m.columns)})
        return m
