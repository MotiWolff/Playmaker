# services/model/feature_builder.py
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Tuple, List

# ---------------------------
# Config-like constants
# ---------------------------

REQUIRED_COLS: List[str] = [
    "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"
]

OPTIONAL_COLS: List[str] = [
    "HS", "AS", "HC", "AC", "HY", "AY", "HR", "AR",
    "B365H", "B365D", "B365A",
]


# ---------------------------
# Helpers
# ---------------------------

def _ensure_datetime(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure Date is datetime; coerce bad values to NaT."""
    df = df.copy()
    try:
        if not pd.api.types.is_datetime64_any_dtype(df.get("Date", pd.Series(dtype="datetime64[ns]"))):
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce", utc=False)
    except Exception as e:
        raise ValueError(f"Failed to parse 'Date' to datetime: {e}")
    return df


def _validate_columns(df: pd.DataFrame) -> None:
    """Raise a clear error if any required column is missing."""
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}. "
                         f"Got columns: {list(df.columns)}")


def _long_format(df: pd.DataFrame) -> pd.DataFrame:
    """
    Expand each match into two rows: one per team perspective.
    Produces:
      - team, opp, date, is_home
      - gf (goals for), ga (goals against)
      - shots, corners, yellows, reds
      - points (3/1/0 from this team’s perspective)
      - n_played (number of prior games for this team before current row)
    """
    # Ensure optional columns exist (as NaN) to simplify downstream operations
    for c in OPTIONAL_COLS:
        if c not in df.columns:
            df[c] = np.nan

    m = df.copy()

    # Home perspective
    home = pd.DataFrame({
        "match_key": m.index,
        "date": m["Date"],
        "team": m["HomeTeam"],
        "opp": m["AwayTeam"],
        "is_home": True,
        "gf": m["FTHG"],
        "ga": m["FTAG"],
        "shots": m["HS"],
        "corners": m["HC"],
        "yellows": m["HY"],
        "reds": m["HR"],
    })

    # Away perspective
    away = pd.DataFrame({
        "match_key": m.index,
        "date": m["Date"],
        "team": m["AwayTeam"],
        "opp": m["HomeTeam"],
        "is_home": False,
        "gf": m["FTAG"],
        "ga": m["FTHG"],
        "shots": m["AS"],
        "corners": m["AC"],
        "yellows": m["AY"],
        "reds": m["AR"],
    })

    long = pd.concat([home, away], ignore_index=True)

    # Points from the team’s perspective
    try:
        ftr = m["FTR"].reindex(long["match_key"].values).values
    except Exception as e:
        raise ValueError(f"Failed to align FTR with long format: {e}")

    is_home = long["is_home"].values
    # H->home gets 3, D->1 both, A->away gets 3
    points = np.where(
        (ftr == "H") & is_home, 3,
        np.where((ftr == "D"), 1,
                 np.where((ftr == "A") & (~is_home), 3, 0))
    )
    long["points"] = points

    # Sort for rolling and compute "games already played" (prior matches)
    long = long.sort_values(["team", "date"]).reset_index(drop=True)
    # cumcount gives 0 for first appearance; that already means "prior games"
    long["n_played"] = long.groupby("team").cumcount()

    return long


def _rolling_team_features(long: pd.DataFrame,
                           form_window: int = 5,
                           goal_window: int = 10) -> pd.DataFrame:
    """
    Compute pre-match rolling features per team, then shift(1) so the current match isn't included.
    Returns a dataframe with one row per (team, match_key) containing pre-match features.
    """
    def _roll(grp: pd.DataFrame) -> pd.DataFrame:
        grp = grp.sort_values("date")
        # Rolling means BEFORE current match → shift(1)
        grp["form5"]   = grp["points"].rolling(form_window, min_periods=3).mean().shift(1)
        grp["gf10"]    = grp["gf"].rolling(goal_window, min_periods=5).mean().shift(1)
        grp["ga10"]    = grp["ga"].rolling(goal_window, min_periods=5).mean().shift(1)
        grp["shots5"]  = grp["shots"].rolling(form_window, min_periods=3).mean().shift(1)
        grp["corn5"]   = grp["corners"].rolling(form_window, min_periods=3).mean().shift(1)
        grp["yel5"]    = grp["yellows"].rolling(form_window, min_periods=3).mean().shift(1)
        grp["red5"]    = grp["reds"].rolling(form_window, min_periods=3).mean().shift(1)
        # Prior games count (already excludes current by shift(1) conceptually)
        grp["n_prior"] = grp["n_played"].shift(1)
        return grp

    try:
        rolled = long.groupby("team", group_keys=False).apply(_roll)
    except Exception as e:
        raise RuntimeError(f"Failed during rolling feature computation: {e}")

    keep_cols = [
        "match_key", "team", "is_home",
        "form5", "gf10", "ga10", "shots5", "corn5", "yel5", "red5",
        "n_prior"
    ]
    return rolled[keep_cols]


def _attach_pre_match_features(wide_df: pd.DataFrame, pre: pd.DataFrame) -> pd.DataFrame:
    """
    Merge pre-match team features back to match-level:
      - columns prefixed with home_ for is_home=True
      - away_ for is_home=False
    """
    home_pre = pre[pre["is_home"]].copy()
    away_pre = pre[~pre["is_home"]].copy()

    def add_prefix(df, prefix):
        cols = ["form5", "gf10", "ga10", "shots5", "corn5", "yel5", "red5", "n_prior"]
        ren = {c: f"{prefix}_{c}" for c in cols}
        return df.rename(columns=ren)

    home_pre = add_prefix(home_pre, "home")
    away_pre = add_prefix(away_pre, "away")

    try:
        m = wide_df.reset_index().rename(columns={"index": "match_key"})
        m = m.merge(
            home_pre.drop(columns=["is_home"]),
            left_on=["match_key", "HomeTeam"],
            right_on=["match_key", "team"],
            how="left"
        )
        m = m.merge(
            away_pre.drop(columns=["is_home"]),
            left_on=["match_key", "AwayTeam"],
            right_on=["match_key", "team"],
            how="left"
        )
        m = m.drop(columns=[c for c in m.columns if c == "team"])
        m = m.set_index("match_key").sort_index()
    except Exception as e:
        raise RuntimeError(f"Failed to merge pre-match features into match rows: {e}")

    return m


def _odds_to_implied_probs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert decimal odds to implied probabilities (normalized to remove margin).
    If odds missing/invalid, leave NaN; caller may impute later.
    Guards against zero/negative odds.
    """
    out = df.copy()
    for col in ("B365H", "B365D", "B365A"):
        if col not in out.columns:
            out[col] = np.nan

    # mask of valid positive odds
    valid_h = (out["B365H"] > 0)
    valid_d = (out["B365D"] > 0)
    valid_a = (out["B365A"] > 0)

    pH_raw = np.where(valid_h, 1.0 / out["B365H"], np.nan)
    pD_raw = np.where(valid_d, 1.0 / out["B365D"], np.nan)
    pA_raw = np.where(valid_a, 1.0 / out["B365A"], np.nan)

    s = pd.Series(pH_raw) + pd.Series(pD_raw) + pd.Series(pA_raw)
    with np.errstate(divide="ignore", invalid="ignore"):
        out["b365_ph"] = pH_raw / s
        out["b365_pd"] = pD_raw / s
        out["b365_pa"] = pA_raw / s

    return out


# ---------------------------
# Public API
# ---------------------------

def build_features(
    df_matches: pd.DataFrame,
    min_history_games: int = 3
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """
    Build safe pre-match features and a 3-class target.

    Parameters
    ----------
    df_matches : DataFrame with one row per finished match.
        Required: Date, HomeTeam, AwayTeam, FTHG, FTAG, FTR
        Optional: HS, AS, HC, AC, HY, AY, HR, AR, B365H, B365D, B365A
    min_history_games : Minimum prior games each team must have
        before we keep a row for training (avoids cold start bias).

    Returns
    -------
    X : DataFrame  (features)
    y : Series     (0=Home win, 1=Draw, 2=Away win)
    meta : DataFrame (Date, HomeTeam, AwayTeam aligned to X/y)
    """
    try:
        # 0) Validate and prep
        _validate_columns(df_matches)
        df = _ensure_datetime(df_matches).sort_values("Date").reset_index(drop=True)
        if df.empty:
            raise ValueError("Input DataFrame is empty after sorting.")

        # 1) Long perspective + rolling pre-match features
        long = _long_format(df)
        pre = _rolling_team_features(long, form_window=5, goal_window=10)

        # 2) Merge back into match-level
        m = _attach_pre_match_features(df, pre)

        # 3) Add odds-derived features (best-effort)
        try:
            m = _odds_to_implied_probs(m)
        except Exception as e:
            # Keep going without odds if anything goes wrong
            print(f"[Warning] Odds conversion failed; continuing without odds: {e}")

        # 4) Target (3-class)
        if "FTR" not in m.columns:
            # Safe alignment fallback
            m["FTR"] = df["FTR"].values

        y = m["FTR"].map({"H": 0, "D": 1, "A": 2})

        # 5) Choose final features
        feature_cols = [
            # home rolling
            "home_form5", "home_gf10", "home_ga10",
            "home_shots5", "home_corn5", "home_yel5", "home_red5",
            # away rolling
            "away_form5", "away_gf10", "away_ga10",
            "away_shots5", "away_corn5", "away_yel5", "away_red5",
            # odds-derived (may be NaN if missing)
            "b365_ph", "b365_pd", "b365_pa",
        ]
        for c in feature_cols:
            if c not in m.columns:
                m[c] = np.nan  # ensure presence

        # 6) History filter: both teams must have >= min_history_games prior matches
        #    (computed during rolling as "n_prior")
        if ("home_n_prior" not in m.columns) or ("away_n_prior" not in m.columns):
            # If not present yet, bring them from pre tables
            # (they should be there because we added to prefixes in _attach_pre_match_features)
            pass  # columns are named during attach

        # Sanity: make sure the prefixed n_prior exist
        if "home_n_prior" not in m.columns or "away_n_prior" not in m.columns:
            raise RuntimeError("Internal error: prior-games counters missing after merge.")

        hist_ok = (m["home_n_prior"] >= min_history_games) & (m["away_n_prior"] >= min_history_games)

        X = m.loc[hist_ok, feature_cols].copy()
        y = y.loc[hist_ok].copy()

        if X.empty:
            raise ValueError(
                "No rows left after history filtering. "
                "Try lowering min_history_games or check data coverage."
            )

        # 7) Fill NaNs with column means (conservative, transparent)
        X = X.apply(lambda col: col.fillna(col.mean()), axis=0)

        # 8) Meta
        meta = df.loc[X.index, ["Date", "HomeTeam", "AwayTeam"]].reset_index(drop=True)

        return X.reset_index(drop=True), y.reset_index(drop=True), meta

    except Exception as e:
        # Re-raise with context so caller sees a helpful message
        raise RuntimeError(f"build_features failed: {e}") from e
