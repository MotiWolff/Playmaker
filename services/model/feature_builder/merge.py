# services/model/features/merge.py
import pandas as pd

class PreMatchMerger:
    """
    Merges per-team rolling features back to the per-match wide frame, producing
    home_* and away_* columns, plus rest_days and n_prior for each side.

    Expects:
      - df (wide): columns Date, HomeTeam, AwayTeam; will be augmented with match_key
      - pre (long, from RollingTeamFeatures.compute): columns
        match_key, team, is_home, form5, gf10, ga10, shots5, corn5, yel5, red5, n_prior, rest_days
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
        # ensure match_key exists and is aligned 0..N-1
        m = df.reset_index(drop=True).copy()
        if "match_key" not in m.columns:
            m["match_key"] = m.index.astype(int)

        # separate home/away rows from long features
        cols_keep = ["match_key","team","is_home","form5","gf10","ga10","shots5","corn5","yel5","red5","n_prior","rest_days"]
        pre = pre[cols_keep].copy()

        home_rows = pre[pre["is_home"]].drop(columns=["team","is_home"]).rename(columns=self.HOME_MAP)
        away_rows = pre[~pre["is_home"]].drop(columns=["team","is_home"]).rename(columns=self.AWAY_MAP)

        # Merge home/away features on match_key
        m = m.merge(home_rows, on="match_key", how="left").merge(away_rows, on="match_key", how="left")

        return m
