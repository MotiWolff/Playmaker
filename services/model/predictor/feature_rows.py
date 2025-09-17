from __future__ import annotations
from typing import Dict, Tuple, List
import numpy as np
import pandas as pd
from Playmaker.shared.logging.logger import Logger

log = Logger.get_logger(name="playmaker.model.predictor.feature_rows")

def _team_points_from_row(row: pd.Series, team_name: str) -> int:
    if row["HomeTeam"] == team_name:
        if row["FTR"] == "H": return 3
        if row["FTR"] == "D": return 1
        return 0
    else:
        if row["FTR"] == "A": return 3
        if row["FTR"] == "D": return 1
        return 0

def _to_utc_naive(ts) -> pd.Timestamp:
    """Parse any datetime-like into UTC and drop timezone info."""
    t = pd.to_datetime(ts, errors="coerce", utc=True)
    if pd.isna(t):
        return t
    return t.tz_convert("UTC").tz_localize(None)

def _pre_match_rolling(
    df_hist: pd.DataFrame,
    team: str,
    as_of: pd.Timestamp,
    form_window: int = 5,
    goal_window: int = 10,
    elo_timeline: Dict[str, pd.DataFrame] | None = None
) -> Dict[str, float]:
    # Sanity
    if df_hist is None or df_hist.empty:
        log.warning("feature_rows.empty_history_for_team", extra={"team": team})
        return {k: np.nan for k in
                ["form5","gf10","ga10","shots5","corn5","yel5","red5","n_prior","rest_days","elo"]}

    dates_all = pd.to_datetime(df_hist["Date"], errors="coerce")
    as_of_naive = _to_utc_naive(as_of)

    mask_team = (df_hist["HomeTeam"] == team) | (df_hist["AwayTeam"] == team)
    mask_date = dates_all < as_of_naive
    h = df_hist[mask_team & mask_date].copy()
    h["Date"] = dates_all[mask_team & mask_date]
    h = h.sort_values("Date")

    last_date = h["Date"].max() if not h.empty else pd.NaT
    rest_days = (as_of_naive - last_date).days if pd.notna(last_date) else np.nan

    # Elo as-of
    elo_as_of = np.nan
    if elo_timeline is not None:
        t = elo_timeline.get(team)
        if t is not None and not t.empty:
            t_dates = pd.to_datetime(t["date"], errors="coerce")
            idx = t_dates.searchsorted(as_of_naive, side="right") - 1
            if idx >= 0:
                elo_as_of = float(t.iloc[idx]["elo_post"])

    if h.empty:
        return {
            "form5": np.nan, "gf10": np.nan, "ga10": np.nan,
            "shots5": np.nan, "corn5": np.nan, "yel5": np.nan, "red5": np.nan,
            "n_prior": 0,
            "rest_days": float(rest_days) if pd.notna(rest_days) else np.nan,
            "elo": float(elo_as_of) if pd.notna(elo_as_of) else np.nan,
        }

    def persp(row):
        if row["HomeTeam"] == team:
            gf, ga = row["FTHG"], row["FTAG"]
            shots, corn, yel, red = row.get("HS", np.nan), row.get("HC", np.nan), row.get("HY", np.nan), row.get("HR", np.nan)
        else:
            gf, ga = row["FTAG"], row["FTHG"]
            shots, corn, yel, red = row.get("AS", np.nan), row.get("AC", np.nan), row.get("AY", np.nan), row.get("AR", np.nan)
        pts = _team_points_from_row(row, team)
        return pd.Series({"gf": gf, "ga": ga, "shots": shots, "corn": corn, "yel": yel, "red": red, "pts": pts})

    T = h.apply(persp, axis=1)

    form5  = T["pts"].tail(form_window).mean()   if len(T) >= 1 else np.nan
    gf10   = T["gf"].tail(goal_window).mean()    if len(T) >= 1 else np.nan
    ga10   = T["ga"].tail(goal_window).mean()    if len(T) >= 1 else np.nan
    shots5 = T["shots"].tail(form_window).mean() if len(T) >= 1 else np.nan
    corn5  = T["corn"].tail(form_window).mean()  if len(T) >= 1 else np.nan
    yel5   = T["yel"].tail(form_window).mean()   if len(T) >= 1 else np.nan
    red5   = T["red"].tail(form_window).mean()   if len(T) >= 1 else np.nan

    return {
        "form5": form5, "gf10": gf10, "ga10": ga10,
        "shots5": shots5, "corn5": corn5, "yel5": yel5, "red5": red5,
        "n_prior": int(len(T)),
        "rest_days": float(rest_days) if pd.notna(rest_days) else np.nan,
        "elo": float(elo_as_of) if pd.notna(elo_as_of) else np.nan,
    }

class FixtureFeatureRows:
    """SRP: build pre-match feature rows for fixtures, aligned with training features."""
    def build_rows(
        self,
        fixtures: pd.DataFrame,
        history: pd.DataFrame,
        elo_timeline: Dict[str, pd.DataFrame] | None = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:

        if fixtures is None or fixtures.empty:
            log.warning("feature_rows.no_fixtures")
            return pd.DataFrame(), pd.DataFrame()

        rows: List[Dict] = []
        snaps: List[Dict] = []

        log.debug("feature_rows.start", extra={"fixtures": len(fixtures)})
        for _, r in fixtures.iterrows():
            as_of = _to_utc_naive(r["match_utc"])
            home, away = r["home_name"], r["away_name"]

            H = _pre_match_rolling(history, home, as_of, elo_timeline=elo_timeline)
            A = _pre_match_rolling(history, away, as_of, elo_timeline=elo_timeline)

            row = {
                "home_form5": H["form5"], "home_gf10": H["gf10"], "home_ga10": H["ga10"],
                "home_shots5": H["shots5"], "home_corn5": H["corn5"], "home_yel5": H["yel5"], "home_red5": H["red5"],
                "away_form5": A["form5"], "away_gf10": A["gf10"], "away_ga10": A["ga10"],
                "away_shots5": A["shots5"], "away_corn5": A["corn5"], "away_yel5": A["yel5"], "away_red5": A["red5"],
                "b365_ph": np.nan, "b365_pd": np.nan, "b365_pa": np.nan,
                "home_rest_days": H["rest_days"], "away_rest_days": A["rest_days"],
                "home_elo": H["elo"], "away_elo": A["elo"],
                "elo_diff": (H["elo"] - A["elo"]) if (pd.notna(H["elo"]) and pd.notna(A["elo"])) else np.nan,
            }
            rows.append(row)

            snaps.append({
                "fixture_id": int(r["fixture_id"]),
                "as_of": str(as_of),
                "home": home, "away": away,
                "home_n_prior": H["n_prior"], "away_n_prior": A["n_prior"],
                "home_gf10": H["gf10"], "away_gf10": A["gf10"],
                "home_form5": H["form5"], "away_form5": A["form5"],
            })

        Xf = pd.DataFrame(rows)
        snap = pd.DataFrame(snaps)
        log.info("feature_rows.built", extra={"rows": len(Xf)})
        return Xf, snap
