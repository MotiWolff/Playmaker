# services/model/data_access/writers.py
from __future__ import annotations
from typing import Any, Dict, Optional, List
import json
import pandas as pd
from sqlalchemy import text, bindparam
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import SQLAlchemyError

class ModelVersionRepo:
    """
    Minimal model metadata writer for a simple table (cfg.tables.versions),
    with columns: model_id (PK serial), model_name, trained_on_dset, metrics JSONB, artifact_uri.
    """
    def __init__(self, db, cfg: Dict[str, Any]):
        self.db = db
        self.cfg = cfg

    def insert(
        self,
        model_name: str,
        trained_on_dset: str,
        metrics: Dict[str, Any],
        artifact_uri: str,
        conn=None
    ) -> int:
        table = self.cfg["tables"]["versions"]
        sql = text(f"""
            INSERT INTO {table} (model_name, trained_on_dset, metrics, artifact_uri)
            VALUES (:model_name, :trained_on_dset, :metrics, :artifact_uri)
            RETURNING model_id;
        """).bindparams(bindparam("metrics", type_=JSONB))

        params = {
            "model_name": model_name,
            "trained_on_dset": trained_on_dset,
            "metrics": metrics,
            "artifact_uri": artifact_uri,
        }

        try:
            if conn is None:
                with self.db.engine().begin() as con:
                    res = con.execute(sql, params)
                    return int(res.scalar_one())
            else:
                res = conn.execute(sql, params)
                return int(res.scalar_one())
        except SQLAlchemyError as e:
            raise RuntimeError(
                f"Failed to insert into '{table}' (model_name={model_name}): {e}"
            ) from e


class PredictionRepo:
    """
    Upserts batch predictions into cfg.tables.predictions.
    Expects df columns:
      - model_id (int)
      - fixture_id (int)   # If you store by match_id instead, rename this column upstream and update ON CONFLICT
      - p_home, p_draw, p_away (floats summing ≈ 1.0)
      - expected_home_goals, expected_away_goals (floats)
      - feature_snapshot (dict or JSON string)
      - generated_at (tz-aware timestamp recommended)
    Requires a UNIQUE constraint on (model_id, fixture_id).
    """
    def __init__(self, db, cfg: Dict[str, Any]):
        self.db = db
        self.cfg = cfg

    def upsert(self, df: pd.DataFrame, conn=None) -> int:
        table = self.cfg["tables"]["predictions"]
        required = [
            "model_id", "fixture_id", "p_home", "p_draw", "p_away",
            "expected_home_goals", "expected_away_goals",
            "feature_snapshot", "generated_at",
        ]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Predictions upsert missing columns: {missing}")

        # basic probability sanity check
        if (df[["p_home", "p_draw", "p_away"]].sum(axis=1) - 1.0).abs().max() > 1e-3:
            raise ValueError("Each prediction row must have p_home+p_draw+p_away ≈ 1.0 (±1e-3).")

        # normalize feature_snapshot to dict for JSONB
        df = df.copy()
        try:
            def _to_dict(v):
                if isinstance(v, dict):
                    return v
                if isinstance(v, str):
                    return json.loads(v)
                # fallback to object __dict__ if present
                return getattr(v, "__dict__", v)
            df["feature_snapshot"] = df["feature_snapshot"].apply(_to_dict)
        except Exception as e:
            raise ValueError(f"feature_snapshot must be dict/JSON-serializable: {e}") from e

        sql = text(f"""
            INSERT INTO {table}
              (model_id, fixture_id, p_home, p_draw, p_away,
               expected_home_goals, expected_away_goals, feature_snapshot, generated_at)
            VALUES
              (:model_id, :fixture_id, :p_home, :p_draw, :p_away,
               :ehg, :eag, :feat, :gen_at)
            ON CONFLICT (model_id, fixture_id)
            DO UPDATE SET
               p_home = EXCLUDED.p_home,
               p_draw = EXCLUDED.p_draw,
               p_away = EXCLUDED.p_away,
               expected_home_goals = EXCLUDED.expected_home_goals,
               expected_away_goals = EXCLUDED.expected_away_goals,
               feature_snapshot = EXCLUDED.feature_snapshot,
               generated_at = EXCLUDED.generated_at;
        """).bindparams(bindparam("feat", type_=JSONB))

        params: List[Dict[str, Any]] = []
        for _, row in df.iterrows():
            params.append({
                "model_id": int(row["model_id"]),
                "fixture_id": int(row["fixture_id"]),
                "p_home": float(row["p_home"]),
                "p_draw": float(row["p_draw"]),
                "p_away": float(row["p_away"]),
                "ehg": float(row["expected_home_goals"]),
                "eag": float(row["expected_away_goals"]),
                "feat": row["feature_snapshot"],
                "gen_at": row["generated_at"],
            })

        try:
            if conn is None:
                with self.db.engine().begin() as con:
                    con.execute(sql, params)   # executemany
            else:
                conn.execute(sql, params)
            return len(params)
        except SQLAlchemyError as e:
            raise RuntimeError(
                f"Failed to upsert into '{table}' (rows={len(params)}): {e}"
            ) from e
