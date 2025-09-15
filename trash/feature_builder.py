# services/model/feature_builder.py
from __future__ import annotations
import pandas as pd
import numpy as np
import warnings
from typing import Tuple, List
from services.model.ratings import compute_elo_pre_post

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
    """Ensure Date is datetime64[ns] naive (no tz). Coerce bad values to NaT and validate."""
    df = df.copy()
    if "Date" not in df.columns:
        raise ValueError("Column 'Date' is missing.")

    try:
        # Parse with UTC then convert to naive (consistent baseline)
        parsed = pd.to_datetime(df["Date"], errors="coerce", utc=True)
        before = len(parsed)
        df["Date"] = parsed.dt.tz_convert("UTC").dt.tz_localize(None)
        n_nat = df["Date"].isna().sum()
        if n_nat > 0 and n_nat / before > 0.05:
            # If >5% failed to parse, treat as a data issue worth surfacing
            raise ValueError(f"Too many unparseable dates: {n_nat}/{before}")
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
    long["n_played"] = long.groupby("team").cumcount()
    # days between this match and the team's previous match (rest before current)
    # long["rest_days"] = long.groupby("team")["date"].diff().dt.days


    return long


def _rolling_team_features(
    long: pd.DataFrame,
    form_window: int = 5,
    goal_window: int = 10,
    min_periods_form: int = 1,
    min_periods_goal: int = 1
) -> pd.DataFrame:
    """
    Compute pre-match rolling features per team, then shift(1) so the current match isn't included.
    min_periods_* controls how many prior games are required to compute a value.
    """
    def _roll(grp: pd.DataFrame) -> pd.DataFrame:
        grp = grp.sort_values("date")
        # days since last match for this team before current match
        grp["rest_days"] = grp["date"].diff().dt.days

        # rolling means BEFORE current match → shift(1)
        grp["form5"]   = grp["points"].rolling(form_window,  min_periods=min_periods_form).mean().shift(1)
        grp["gf10"]    = grp["gf"].rolling(goal_window,      min_periods=min_periods_goal).mean().shift(1)
        grp["ga10"]    = grp["ga"].rolling(goal_window,      min_periods=min_periods_goal).mean().shift(1)
        grp["shots5"]  = grp["shots"].rolling(form_window,   min_periods=min_periods_form).mean().shift(1)
        grp["corn5"]   = grp["corners"].rolling(form_window, min_periods=min_periods_form).mean().shift(1)
        grp["yel5"]    = grp["yellows"].rolling(form_window, min_periods=min_periods_form).mean().shift(1)
        grp["red5"]    = grp["reds"].rolling(form_window,    min_periods=min_periods_form).mean().shift(1)
        # prior games before this row
        grp["n_prior"] = grp["n_played"].shift(1)

        return grp

    g = long.groupby("team", group_keys=False)

    # Keep compatibility with pandas versions: try default behavior and silence future warning.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        rolled = g.apply(_roll)

    # If pandas excluded the group columns and 'team' is missing, restore it
    if "team" not in rolled.columns:
        if isinstance(rolled.index, pd.MultiIndex) and "team" in rolled.index.names:
            rolled = rolled.reset_index(level="team")
        else:
            # Fallback: merge back from original long using match_key
            rolled = rolled.merge(long[["match_key", "team"]], on="match_key", how="left")

    keep_cols = [
        "match_key", "team", "is_home",
        "form5", "gf10", "ga10", "shots5", "corn5", "yel5", "red5",
        "n_prior",
        "rest_days",
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
        cols = ["form5", "gf10", "ga10", "shots5", "corn5", "yel5", "red5", "n_prior", "rest_days"]

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
    Convert decimal odds (B365H/B365D/B365A) to margin-removed implied probs.
    Leaves NaN where odds are invalid/missing.
    """
    out = df.copy()
    for col in ("B365H", "B365D", "B365A"):
        if col not in out.columns:
            out[col] = np.nan

    # ensure numeric
    out["B365H"] = pd.to_numeric(out["B365H"], errors="coerce")
    out["B365D"] = pd.to_numeric(out["B365D"], errors="coerce")
    out["B365A"] = pd.to_numeric(out["B365A"], errors="coerce")

    H = out["B365H"].to_numpy()
    D = out["B365D"].to_numpy()
    A = out["B365A"].to_numpy()

    pH_raw = np.where(H > 0, 1.0 / H, np.nan)
    pD_raw = np.where(D > 0, 1.0 / D, np.nan)
    pA_raw = np.where(A > 0, 1.0 / A, np.nan)

    s = pH_raw + pD_raw + pA_raw
    with np.errstate(divide="ignore", invalid="ignore"):
        out["b365_ph"] = np.where(s > 0, pH_raw / s, np.nan)
        out["b365_pd"] = np.where(s > 0, pD_raw / s, np.nan)
        out["b365_pa"] = np.where(s > 0, pA_raw / s, np.nan)

    return out


# ---------------------------
# Public API
# ---------------------------

def build_features(
    df_matches: pd.DataFrame,
    min_history_games: int = 3,
    form_window: int = 5,
    goal_window: int = 10,
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """
    Build pre-match features and a 3-class target (H/D/A -> 0/1/2).
    No leakage: all rolling stats are shifted.
    """
    try:
        _validate_columns(df_matches)
        df = _ensure_datetime(df_matches).sort_values("Date").reset_index(drop=True)
        if df.empty:
            raise ValueError("Input DataFrame is empty after sorting.")

        long = _long_format(df)
        pre = _rolling_team_features(
            long,
            form_window=form_window,
            goal_window=goal_window,
            min_periods_form=max(1, min_history_games),
            min_periods_goal=max(1, min_history_games),
        )

        m = _attach_pre_match_features(df, pre)

        # ELO (pre-match) + alignment
        elo = compute_elo_pre_post(df)
        if elo.index.name is None:
            elo.index.name = "match_key"
        if len(elo) != len(df) or not (elo.index.values == pd.RangeIndex(len(df)).values).all():
            raise RuntimeError("compute_elo_pre_post must be indexed by match_key (0..N-1).")
        m = m.join(elo[["home_elo_pre", "away_elo_pre"]])
        m = m.rename(columns={"home_elo_pre": "home_elo", "away_elo_pre": "away_elo"})
        m["elo_diff"] = m["home_elo"] - m["away_elo"]

        # Odds
        try:
            m = _odds_to_implied_probs(m)
        except Exception as e:
            print(f"[Warning] Odds conversion failed; continuing without odds: {e}")

        # Target
        label_map = {"H": 0, "D": 1, "A": 2}
        if "FTR" not in m.columns:
            m["FTR"] = df["FTR"].values
        y = m["FTR"].map(label_map).astype("Int64")

        feature_cols = [
            "home_form5", "home_gf10", "home_ga10",
            "home_shots5", "home_corn5", "home_yel5", "home_red5",
            "away_form5", "away_gf10", "away_ga10",
            "away_shots5", "away_corn5", "away_yel5", "away_red5",
            "b365_ph", "b365_pd", "b365_pa",
            "home_rest_days", "away_rest_days",
            "home_elo", "away_elo", "elo_diff",
        ]
        for c in feature_cols:
            if c not in m.columns:
                m[c] = np.nan

        needed_prior = ["home_n_prior", "away_n_prior"]
        missing_prior = [c for c in needed_prior if c not in m.columns]
        if missing_prior:
            raise RuntimeError(f"Internal error: missing prior counters {missing_prior} after merge.")

        hist_ok = (m["home_n_prior"] >= min_history_games) & (m["away_n_prior"] >= min_history_games)
        if not hist_ok.any() and min_history_games > 0:
            print(f"[Warning] No rows pass both-team history >= {min_history_games}. Relaxing to either-team.")
            hist_ok = ((m["home_n_prior"] >= min_history_games) | (m["away_n_prior"] >= min_history_games))
        if not hist_ok.any():
            print("[Warning] Still empty after relaxation. Using no history filter (demo mode).")
            hist_ok = pd.Series(True, index=m.index)

        X = m.loc[hist_ok, feature_cols].copy()
        y = y.loc[hist_ok].copy()

        # Impute
        X = X.apply(lambda col: col.fillna(col.mean()), axis=0)
        if X.isna().any().any():
            X = X.fillna(0.0)

        meta = df.loc[X.index, ["Date", "HomeTeam", "AwayTeam"]].reset_index(drop=True)
        return X.reset_index(drop=True), y.reset_index(drop=True), meta

    except Exception as e:
        raise RuntimeError(f"build_features failed: {e}") from e

