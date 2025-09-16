# services/model/predictor/elo_timeline.py
from __future__ import annotations
from typing import Dict
import pandas as pd
import numpy as np

class EloTimeline:
    """
    Build a per-team Elo timeline that can be queried at 'as_of' dates.
    For now we provide a flat 1500 baseline with match dates from history.
    """
    def build(self, df_hist: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        out: Dict[str, pd.DataFrame] = {}
        if df_hist is None or df_hist.empty:
            return out
        # Expect training-shaped columns: Date, HomeTeam, AwayTeam
        cols_req = {"Date", "HomeTeam", "AwayTeam"}
        if not cols_req.issubset(df_hist.columns):
            return out

        dates = pd.to_datetime(df_hist["Date"], errors="coerce")
        # build a simple per-team timeline at each date they played
        for col_team in ("HomeTeam", "AwayTeam"):
            for team, g in df_hist[[col_team, "Date"]].rename(columns={col_team: "Team"}).groupby("Team"):
                d = pd.to_datetime(g["Date"], errors="coerce").dropna().drop_duplicates().sort_values()
                if d.empty:
                    continue
                out[str(team)] = pd.DataFrame({"date": d, "elo_post": np.full(len(d), 1500.0)})
        return out
