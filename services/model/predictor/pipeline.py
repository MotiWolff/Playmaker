from __future__ import annotations
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple, Dict, Any

import numpy as np
import pandas as pd

from services.model.data_access import load_cfg, read_training_frame

from .artifact_loader import JoblibArtifactLoader
from .fixtures_repo import FixturesRepositoryDB, get_team_lookup
from .history_adapter import MatchHistoryAdapter
from .elo_timeline import EloTimeline
from .feature_rows import FixtureFeatureRows
from .imputer import TrainMeansImputer
from .predictor import ThreeClassPredictor
from .writer import DBPredictionsWriter

from Playmaker.shared.logging.logger import Logger
log = Logger.get_logger(name="playmaker.model.predictor.pipeline")

def predict_pipeline(
    cfg_path: str,
    model_id: int,
    artifact_path: str | None = None,
    limit: int | None = None,
) -> int:
    """Load model, prepare features for scheduled fixtures, predict, and upsert."""
    log.info("pipeline.start", extra={"cfg_path": cfg_path, "model_id": model_id, "limit": limit})

    cfg: Dict[str, Any] = load_cfg(cfg_path)

    model, meta = JoblibArtifactLoader().load(artifact_path)
    feature_cols = meta["feature_cols"]
    log.info("pipeline.artifact_ready", extra={"n_features": len(feature_cols)})

    team_map = get_team_lookup(cfg)
    df_hist_db = read_training_frame(cfg)
    df_hist = MatchHistoryAdapter().adapt(df_hist_db, team_map)

    elo_timeline = EloTimeline().build(df_hist)

    train_means = TrainMeansImputer().fit_training_means(df_hist)

    fixtures = FixturesRepositoryDB(cfg).list_scheduled(limit=limit)
    if fixtures.empty:
        log.info("pipeline.no_scheduled_fixtures")
        return 0
    log.info("pipeline.fixtures_to_score", extra={"count": len(fixtures)})

    Xf_raw, snap = FixtureFeatureRows().build_rows(fixtures, df_hist, elo_timeline=elo_timeline)

    Xf = TrainMeansImputer().transform(Xf_raw, train_means, feature_cols)

    y_proba = ThreeClassPredictor().predict_proba(model, Xf)

    # crude xG proxy from 10-match GF means (kept from your original)
    ehg = Xf["home_gf10"].fillna(1.2).to_numpy()
    eag = Xf["away_gf10"].fillna(1.0).to_numpy()

    now_utc = datetime.now(timezone.utc).isoformat()
    rows = []
    for i, r in fixtures.reset_index(drop=True).iterrows():
        rows.append({
            "model_id": int(model_id),
            "fixture_id": int(r["fixture_id"]),
            "p_home": float(y_proba[i, 0]),
            "p_draw": float(y_proba[i, 1]),
            "p_away": float(y_proba[i, 2]),
            "expected_home_goals": float(ehg[i]),
            "expected_away_goals": float(eag[i]),
            "feature_snapshot": {
                "home": r["home_name"],
                "away": r["away_name"],
                "as_of": str(r["match_utc"]),
                **{k: (float(Xf_raw.iloc[i][k]) if pd.notna(Xf_raw.iloc[i][k]) else None)
                   for k in ["home_form5","away_form5","home_gf10","away_gf10","b365_ph","b365_pd","b365_pa"]}
            },
            "generated_at": now_utc,
        })
    df_pred = pd.DataFrame(rows)

    written = DBPredictionsWriter().upsert(cfg, df_pred)
    log.info("pipeline.upsert_done", extra={"rows": int(written)})
    return written

def main():
    parser = argparse.ArgumentParser(description="Score scheduled fixtures and upsert predictions.")
    parser.add_argument("--cfg", default=str(Path(__file__).resolve().parents[1] / "config" / "config.yaml"),
                        help="Path to YAML config.")
    parser.add_argument("--model_id", type=int, required=True,
                        help="model_id from model_version (output of training).")
    parser.add_argument("--artifact", default=None,
                        help="Path to model artifact (.joblib). Defaults to latest in models/.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Optional: score only the first N fixtures.")
    args = parser.parse_args()

    try:
        n = predict_pipeline(cfg_path=args.cfg, model_id=args.model_id,
                             artifact_path=args.artifact, limit=args.limit)
        if n == 0:
            log.info("pipeline.exit_no_rows")
            print("\nℹ️ Nothing scored (no fixtures).")
        else:
            log.info("pipeline.exit_success", extra={"rows": n})
            print(f"\n✅ Scoring complete. Rows written: {n}")
    except Exception as e:
        log.exception("pipeline.failed", extra={"error": str(e)})
        print(f"\n❌ Prediction failed: {e}")
        raise

if __name__ == "__main__":
    main()
