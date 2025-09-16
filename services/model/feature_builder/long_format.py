# services/model/features/long_format.py
import numpy as np
import pandas as pd

OPTIONAL_COLS = ["HS","AS","HC","AC","HY","AY","HR","AR","B365H","B365D","B365A"]

class LongFormatter:
    """
    Build a long (per-team) frame from the classic football-data-like wide match frame.
    Expects at least: Date, HomeTeam, AwayTeam, FTHG, FTAG, FTR
    Optional: HS, AS, HC, AC, HY, AY, HR, AR, B365H, B365D, B365A
    Output columns (per row/team): match_key, team, date, is_home, gf, ga, shots, corners, yellows, reds
    """
    def to_long(self, df: pd.DataFrame) -> pd.DataFrame:
        m = df.copy()

        # ensure optional columns exist
        for c in OPTIONAL_COLS:
            if c not in m.columns:
                m[c] = np.nan

        # stable integer key 0..N-1
        m = m.reset_index(drop=True)
        m["match_key"] = m.index.astype(int)

        # build home and away long-slices
        home = pd.DataFrame({
            "match_key": m["match_key"].values,
            "team":      m["HomeTeam"].values,
            "date":      m["Date"].values,
            "is_home":   True,
            "gf":        m["FTHG"].values,
            "ga":        m["FTAG"].values,
            "shots":     m["HS"].values,
            "corners":   m["HC"].values,
            "yellows":   m["HY"].values,
            "reds":      m["HR"].values,
        })

        away = pd.DataFrame({
            "match_key": m["match_key"].values,
            "team":      m["AwayTeam"].values,
            "date":      m["Date"].values,
            "is_home":   False,
            "gf":        m["FTAG"].values,
            "ga":        m["FTHG"].values,
            "shots":     m["AS"].values,
            "corners":   m["AC"].values,
            "yellows":   m["AY"].values,
            "reds":      m["AR"].values,
        })

        long = pd.concat([home, away], ignore_index=True)

        # derive points per team-row from FTR and home/away flag (for rolling form)
        ftr = m["FTR"].reindex(long["match_key"].values).to_numpy()
        is_home = long["is_home"].to_numpy()
        # points: win=3, draw=1, loss=0
        points = np.where(
            (ftr == "H") & is_home, 3,
            np.where(
                (ftr == "D"), 1,
                np.where((ftr == "A") & (~is_home), 3, 0)
            )
        )
        long["points"] = points

        long = long.sort_values(["team", "date"]).reset_index(drop=True)
        long["n_played"] = long.groupby("team").cumcount()

        return long
