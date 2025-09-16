# services/model/ratings.py
from __future__ import annotations
from typing import Dict, Tuple
import pandas as pd
import numpy as np

def compute_elo_pre_post(
    df_matches: pd.DataFrame,
    k: float = 20.0,
    home_field_adv: float = 60.0,
    start_rating: float = 1500.0,
) -> pd.DataFrame:
    """
    Compute pre- and post-match Elo for each original match.
    Expects columns: Date, HomeTeam, AwayTeam, FTR  (like your training frame).
    Returns a DataFrame indexed by match_key (original df index) with:
      - home_elo_pre, away_elo_pre, home_elo_post, away_elo_post
      - Date, HomeTeam, AwayTeam   (useful for building a per-team time series)
    """
    if not {"Date", "HomeTeam", "AwayTeam", "FTR"}.issubset(df_matches.columns):
        raise ValueError("Elo requires columns: Date, HomeTeam, AwayTeam, FTR")

    df = df_matches.copy().sort_values("Date").reset_index()
    df = df.rename(columns={"index": "match_key"})

    ratings: Dict[str, float] = {}

    def r(team: str) -> float:
        return ratings.get(team, start_rating)

    rows = []
    for _, row in df.iterrows():
        h, a = row["HomeTeam"], row["AwayTeam"]
        rh, ra = r(h), r(a)

        # pre-match
        home_elo_pre, away_elo_pre = rh, ra

        # expected scores (Elo uses 1/0.5/0)
        # home advantage applied to home rating in expectation
        exp_home = 1.0 / (1.0 + 10 ** (-( (rh + home_field_adv) - ra ) / 400.0))
        exp_away = 1.0 - exp_home

        # actual scores
        if row["FTR"] == "H":
            s_home, s_away = 1.0, 0.0
        elif row["FTR"] == "A":
            s_home, s_away = 0.0, 1.0
        else:  # Draw
            s_home, s_away = 0.5, 0.5

        rh_post = rh + k * (s_home - exp_home)
        ra_post = ra + k * (s_away - exp_away)

        ratings[h] = rh_post
        ratings[a] = ra_post

        rows.append({
            "match_key": int(row["match_key"]),
            "Date": row["Date"],
            "HomeTeam": h,
            "AwayTeam": a,
            "home_elo_pre": home_elo_pre,
            "away_elo_pre": away_elo_pre,
            "home_elo_post": rh_post,
            "away_elo_post": ra_post,
        })

    out = pd.DataFrame(rows).set_index("match_key").sort_index()
    return out
