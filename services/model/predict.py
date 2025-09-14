# services/model/predict.py
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple, List

import joblib
import numpy as np
import pandas as pd
from sqlalchemy import text

from data_access import (
    load_cfg,
    get_engine,
    read_training_frame,
    read_upcoming_fixtures,
    upsert_predictions,
)
from feature_builder import build_features  # used to learn column means/imputation


# ---------------------------
# Helpers
# ---------------------------

def _latest_artifact(models_dir: str = "services/model/models", pattern: str = "*.joblib") -> str:
    p = Path(models_dir)
    files = sorted(p.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No model artifacts found in '{models_dir}'.")
    return str(files[-1])


def _get_team_lookup(cfg: Dict) -> pd.DataFrame:
    """
    Returns: DataFrame with team_id, name
    """
    eng = get_engine(cfg)
    try:
        return pd.read_sql("SELECT team_id, name FROM team;", eng)
    except Exception as e:
        raise RuntimeError(f"Failed reading team table: {e}") from e


def _adapt_history_schema(df_hist: pd.DataFrame, team_map: pd.DataFrame) -> pd.DataFrame:
    """
    Convert DB columns to the columns expected by the feature builder:
      Date, HomeTeam, AwayTeam, FTHG, FTAG, FTR, and optional odds/stats.
    Joins team names if only IDs exist.
    """
    df = df_hist.copy()

    # Map common DB names to expected names
    rename_map = {}
    if "match_date" in df.columns: rename_map["match_date"] = "Date"
    if "home_goals" in df.columns: rename_map["home_goals"] = "FTHG"
    if "away_goals" in df.columns: rename_map["away_goals"] = "FTAG"
    if "result" in df.columns:     rename_map["result"]     = "FTR"
    # Optional odds/stats renames if your cleaner used lowercase:
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

    # Bring team names if we only have team_id columns
    have_names = ("HomeTeam" in df.columns) and ("AwayTeam" in df.columns)
    if not have_names and {"home_team_id", "away_team_id"}.issubset(df.columns):
        lut = team_map.rename(columns={"team_id": "tid", "name": "tname"})
        df = df.merge(lut, left_on="home_team_id", right_on="tid", how="left").rename(columns={"tname": "HomeTeam"}).drop(columns=["tid"])
        df = df.merge(lut, left_on="away_team_id", right_on="tid", how="left").rename(columns={"tname": "AwayTeam"}).drop(columns=["tid"])

    # If FTR missing but goals exist, derive it
    if "FTR" not in df.columns and {"FTHG", "FTAG"}.issubset(df.columns):
        cond_home = df["FTHG"] > df["FTAG"]
        cond_away = df["FTHG"] < df["FTAG"]
        df["FTR"] = np.where(cond_home, "H", np.where(cond_away, "A", "D"))

    # Minimal required columns check (feature builder will re-validate)
    req = ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"]
    missing = [c for c in req if c not in df.columns]
    if missing:
        raise ValueError(f"History frame lacks required columns after adaptation: {missing}")

    return df


def _fixtures_with_names(cfg: Dict) -> pd.DataFrame:
    """
    Join fixtures with team names for convenience.
    Returns: fixture_id, match_utc, home_team_id, away_team_id, home_name, away_name
    """
    eng = get_engine(cfg)
    t_fix = cfg["tables"]["fixtures"]
    sql = text(f"""
      SELECT f.fixture_id, f.match_utc, f.home_team_id, f.away_team_id,
             th.name AS home_name, ta.name AS away_name
      FROM {t_fix} f
      JOIN team th ON th.team_id = f.home_team_id
      JOIN team ta ON ta.team_id = f.away_team_id
      WHERE f.status = 'SCHEDULED'
      ORDER BY f.match_utc;
    """)
    try:
        return pd.read_sql(sql, eng)
    except Exception as e:
        raise RuntimeError(f"Failed to load fixtures with names: {e}") from e


def _team_points_from_row(row: pd.Series, team_name: str) -> int:
    """Points for team_name in a finished match row (3/1/0)."""
    if row["HomeTeam"] == team_name:
        if row["FTR"] == "H": return 3
        if row["FTR"] == "D": return 1
        return 0
    else:  # team is away
        if row["FTR"] == "A": return 3
        if row["FTR"] == "D": return 1
        return 0


def _pre_match_rolling(df_hist: pd.DataFrame, team: str, as_of: pd.Timestamp,
                       form_window: int = 5, goal_window: int = 10) -> Dict[str, float]:
    """
    Compute pre-match rolling stats for a team as of 'as_of' (strictly before).
    Uses the same feature meanings as in training.
    """
    h = df_hist[((df_hist["HomeTeam"] == team) | (df_hist["AwayTeam"] == team)) & (df_hist["Date"] < as_of)].copy()
    h = h.sort_values("Date")

    # Shots/corners/cards per perspective
    # Build columns from the team's perspective
    def persp(row):
        if row["HomeTeam"] == team:
            gf, ga = row["FTHG"], row["FTAG"]
            shots, corn, yel, red = row.get("HS", np.nan), row.get("HC", np.nan), row.get("HY", np.nan), row.get("HR", np.nan)
        else:
            gf, ga = row["FTAG"], row["FTHG"]
            shots, corn, yel, red = row.get("AS", np.nan), row.get("AC", np.nan), row.get("AY", np.nan), row.get("AR", np.nan)
        pts = _team_points_from_row(row, team)
        return pd.Series({"gf": gf, "ga": ga, "shots": shots, "corn": corn, "yel": yel, "red": red, "pts": pts})

    if h.empty:
        return {
            "form5": np.nan, "gf10": np.nan, "ga10": np.nan,
            "shots5": np.nan, "corn5": np.nan, "yel5": np.nan, "red5": np.nan,
            "n_prior": 0
        }

    T = h.apply(persp, axis=1)

    # Rolling means over tail windows
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
        "n_prior": int(len(T))
    }


def _fixture_feature_rows(fixt: pd.DataFrame, hist_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Build one feature row per fixture, matching the training feature names.
    Returns:
      Xf : features for model
      snap : a compact feature_snapshot per row (for debugging/Audit)
    """
    rows: List[Dict] = []
    snaps: List[Dict] = []

    for _, r in fixt.iterrows():
        as_of = pd.to_datetime(r["match_utc"])
        home, away = r["home_name"], r["away_name"]

        H = _pre_match_rolling(hist_df, home, as_of)
        A = _pre_match_rolling(hist_df, away, as_of)

        # Create training-aligned feature names
        row = {
            "home_form5": H["form5"], "home_gf10": H["gf10"], "home_ga10": H["ga10"],
            "home_shots5": H["shots5"], "home_corn5": H["corn5"], "home_yel5": H["yel5"], "home_red5": H["red5"],
            "away_form5": A["form5"], "away_gf10": A["gf10"], "away_ga10": A["ga10"],
            "away_shots5": A["shots5"], "away_corn5": A["corn5"], "away_yel5": A["yel5"], "away_red5": A["red5"],
            # Odds-derived features (if you later store odds for fixtures, fill them here)
            "b365_ph": np.nan, "b365_pd": np.nan, "b365_pa": np.nan,
        }
        rows.append(row)

        snaps.append({
            "fixture_id": int(r["fixture_id"]),
            "as_of": str(as_of),
            "home": home, "away": away,
            "home_n_prior": H["n_prior"], "away_n_prior": A["n_prior"],
            # include a subset of features for audit
            "home_gf10": H["gf10"], "away_gf10": A["gf10"],
            "home_form5": H["form5"], "away_form5": A["form5"],
        })

    Xf = pd.DataFrame(rows)
    snap = pd.DataFrame(snaps)
    return Xf, snap


def _impute_and_align(Xf: pd.DataFrame, X_train_means: pd.Series, feature_order: List[str]) -> pd.DataFrame:
    """
    Fill NaNs using training column means and reorder columns to model's expected order.
    """
    Xf = Xf.copy()
    # Ensure all columns exist
    for c in feature_order:
        if c not in Xf.columns:
            Xf[c] = np.nan
    # Impute with training means where available; otherwise with column mean of Xf
    for c in feature_order:
        if Xf[c].isna().any():
            fill_val = X_train_means.get(c, Xf[c].mean())
            Xf[c] = Xf[c].fillna(fill_val)
    # Reorder
    return Xf[feature_order]


# ---------------------------
# Main prediction pipeline
# ---------------------------

def predict_pipeline(
    cfg_path: str,
    model_id: int,
    artifact_path: str | None = None,
    limit: int | None = None,
) -> int:
    """
    Loads model + history, builds features for scheduled fixtures, predicts probabilities,
    and upserts into prediction. Returns number of rows written.
    """
    print(">> Loading config…")
    cfg = load_cfg(cfg_path)

    print(">> Loading model artifact…")
    artifact = artifact_path or _latest_artifact()
    payload = joblib.load(artifact)
    clf = payload["model"]
    meta = payload.get("meta", {})
    feature_cols = meta.get("feature_cols")
    if feature_cols is None:
        raise RuntimeError("Artifact missing 'feature_cols' in meta; cannot align input features.")

    print(f"   Using artifact: {artifact}")

    print(">> Reading history (match_clean)…")
    # History for (1) feature snapshots and (2) training means via build_features
    team_map = _get_team_lookup(cfg)
    df_hist_db = read_training_frame(cfg)
    df_hist = _adapt_history_schema(df_hist_db, team_map)

    # Learn training column means via the same builder used for training
    print(">> Recomputing training feature means (for imputation)…")
    X_train_all, _, _ = build_features(df_hist)
    train_means = X_train_all.mean()

    print(">> Reading scheduled fixtures…")
    fixt = _fixtures_with_names(cfg)
    if limit:
        fixt = fixt.head(limit)
    if fixt.empty:
        print("   No fixtures with status='SCHEDULED'. Nothing to predict.")
        return 0

    print(f"   Fixtures to score: {len(fixt)}")

    print(">> Building pre-match features for fixtures…")
    Xf_raw, snap = _fixture_feature_rows(fixt, df_hist)

    print(">> Imputing missing values and aligning to model's feature order…")
    Xf = _impute_and_align(Xf_raw, train_means, feature_cols)

    print(">> Predicting probabilities…")
    y_proba = clf.predict_proba(Xf)

    # Ensure 3-class ordering [0,1,2] = [H,D,A]
    classes_ = getattr(clf, "classes_", np.array([0, 1, 2]))
    if set(classes_) != {0, 1, 2}:
        proba_full = np.zeros((y_proba.shape[0], 3))
        for col_idx, cls in enumerate(classes_):
            proba_full[:, int(cls)] = y_proba[:, col_idx]
        y_proba = proba_full

    # Expected goals proxy: use gf10 rolling means (simple, replace later with Poisson/xG model)
    ehg = Xf["home_gf10"].fillna(1.2).to_numpy()
    eag = Xf["away_gf10"].fillna(1.0).to_numpy()

    # Build prediction rows for DB
    now_utc = datetime.now(timezone.utc).isoformat()
    rows = []
    for i, r in fixt.reset_index(drop=True).iterrows():
        rows.append({
            "model_id": int(model_id),
            "fixture_id": int(r["fixture_id"]),
            "p_home": float(y_proba[i, 0]),
            "p_draw": float(y_proba[i, 1]),
            "p_away": float(y_proba[i, 2]),
            "expected_home_goals": float(ehg[i]),
            "expected_away_goals": float(eag[i]),
            # include a compact snapshot for debugging / audit
            "feature_snapshot": {
                "home": r["home_name"],
                "away": r["away_name"],
                "as_of": str(r["match_utc"]),
                **{k: float(Xf_raw.iloc[i][k]) if pd.notna(Xf_raw.iloc[i][k]) else None
                   for k in ["home_form5","away_form5","home_gf10","away_gf10","b365_ph","b365_pd","b365_pa"]}
            },
            "generated_at": now_utc,
        })
    df_pred = pd.DataFrame(rows)

    print(">> Writing predictions (upsert)…")
    written = upsert_predictions(cfg, df_pred)
    print(f"   Upserted rows: {written}")
    return written


# ---------------------------
# CLI
# ---------------------------

def main():
    parser = argparse.ArgumentParser(description="Score scheduled fixtures and upsert predictions.")
    parser.add_argument("--cfg", default="services/model/config/config.yaml", help="Path to YAML config.")
    parser.add_argument("--model_id", type=int, required=True, help="model_id from model_version (output of train.py).")
    parser.add_argument("--artifact", default=None, help="Path to model artifact (.joblib). Defaults to latest in models/.")
    parser.add_argument("--limit", type=int, default=None, help="Optional: score only the first N fixtures.")
    args = parser.parse_args()

    try:
        n = predict_pipeline(cfg_path=args.cfg, model_id=args.model_id, artifact_path=args.artifact, limit=args.limit)
        if n == 0:
            print("\nℹ️ Nothing scored (no fixtures).")
        else:
            print(f"\n✅ Scoring complete. Rows written: {n}")
    except Exception as e:
        print(f"\n❌ Prediction failed: {e}")
        raise


if __name__ == "__main__":
    main()
