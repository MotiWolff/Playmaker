# services/model/features/adapters/elo_ratings.py
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
import math
from ..ports import EloRatingsPort

@dataclass
class EloParams:
    k: float = 20.0
    base: float = 1500.0
    home_adv: float = 60.0  # typical home advantage in Elo points

class EloRatingsAdapter(EloRatingsPort):
    """
    Minimal chronological Elo with pre-match ratings output.
    Uses final score (FTHG/FTAG) to update after each match.
    """
    def __init__(self, params: EloParams | None = None):
        self.params = params or EloParams()

    def compute_elo_pre_post(self, df_matches: pd.DataFrame) -> pd.DataFrame:
        # Expect classic columns and stable order
        req = ["Date","HomeTeam","AwayTeam","FTHG","FTAG"]
        missing = [c for c in req if c not in df_matches.columns]
        if missing:
            raise ValueError(f"EloRatingsAdapter: missing columns {missing}")

        df = df_matches.reset_index(drop=True).copy()
        df["match_key"] = df.index.astype(int)

        ratings: dict[str, float] = {}
        home_pre = []
        away_pre = []

        def get(team: str) -> float:
            return ratings.get(team, self.params.base)

        for i, row in df.iterrows():
            h, a = str(row["HomeTeam"]), str(row["AwayTeam"])
            rh = get(h)
            ra = get(a)

            # pre-match snapshot
            home_pre.append(rh)
            away_pre.append(ra)

            # expected result with home advantage
            eh = 1.0 / (1.0 + math.pow(10.0, ((ra - (rh + self.params.home_adv)) / 400.0)))
            ea = 1.0 - eh

            # actual result from goals
            fthg = row["FTHG"]; ftag = row["FTAG"]
            if pd.isna(fthg) or pd.isna(ftag):
                # skip update if no final score (e.g., fixture rows mistakenly present)
                continue
            if fthg > ftag:
                sh, sa = 1.0, 0.0
            elif fthg < ftag:
                sh, sa = 0.0, 1.0
            else:
                sh, sa = 0.5, 0.5

            # update ratings
            k = self.params.k
            rh_new = rh + k * (sh - eh)
            ra_new = ra + k * (sa - ea)
            ratings[h] = rh_new
            ratings[a] = ra_new

        out = pd.DataFrame({
            "home_elo_pre": home_pre,
            "away_elo_pre": away_pre,
        }, index=df["match_key"])

        # ensure index name for your builder check
        out.index.name = "match_key"
        return out
