from __future__ import annotations
from typing import Dict
import numpy as np
import pandas as pd


class MatchHistoryAdapter:
    """SRP: convert DB schema to training schema expected by feature builder."""
    def adapt(self, df_hist: pd.DataFrame, team_map: pd.DataFrame) -> pd.DataFrame:
        df = df_hist.copy()
        rename_map = {}
        if "match_date" in df.columns: rename_map["match_date"] = "Date"
        if "home_goals" in df.columns: rename_map["home_goals"] = "FTHG"
        if "away_goals" in df.columns: rename_map["away_goals"] = "FTAG"
        if "result" in df.columns:     rename_map["result"]     = "FTR"
        opt_map = {
            "b365h": "B365H", "b365d": "B365D", "b365a": "B365A",
            "hs": "HS", "as": "AS", "hc": "HC", "ac": "AC",
            "hy": "HY", "ay": "AY", "hr": "HR", "ar": "AR",
        }
        for k, v in opt_map.items():
            if k in df.columns:
                rename_map[k] = v
        if rename_map:
            df = df.rename(columns=rename_map)

        have_names = ("HomeTeam" in df.columns) and ("AwayTeam" in df.columns)
        if not have_names and {"home_team_id", "away_team_id"}.issubset(df.columns):
            lut = team_map.rename(columns={"team_id": "tid", "name": "tname"})
            df = (
                df.merge(lut, left_on="home_team_id", right_on="tid", how="left")
                  .rename(columns={"tname": "HomeTeam"}).drop(columns=["tid"])
            )
            df = (
                df.merge(lut, left_on="away_team_id", right_on="tid", how="left")
                  .rename(columns={"tname": "AwayTeam"}).drop(columns=["tid"])
            )

        if "FTR" not in df.columns and {"FTHG", "FTAG"}.issubset(df.columns):
            cond_home = df["FTHG"] > df["FTAG"]
            cond_away = df["FTHG"] < df["FTAG"]
            df["FTR"] = np.where(cond_home, "H", np.where(cond_away, "A", "D"))

        req = ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"]
        missing = [c for c in req if c not in df.columns]
        if missing:
            raise ValueError(f"History frame lacks required columns after adaptation: {missing}")

        return df
