# services/model/data_access.py
from __future__ import annotations
from pathlib import Path

import os
import json
from typing import Any, Dict, Iterable, Optional, Tuple

import pandas as pd
import yaml
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert as pg_insert


# ------------- Config loading -------------

def load_cfg(path: str = "services/model/config/config.yaml") -> Dict[str, Any]:
    """
    Load YAML config. Env var DB_DSN overrides db_dsn.
    Searches a few sensible locations so tests run no matter the CWD.
    """
    candidates = []
    # 1) what the caller passed
    candidates.append(Path(path))
    # 2) next to this file: services/model/config/config.yaml
    candidates.append(Path(__file__).resolve().parent / "config" / "config.yaml")
    # 3) project-root style: <cwd>/services/model/config/config.yaml
    candidates.append(Path.cwd() / "services" / "model" / "config" / "config.yaml")

    last_err = None
    for cand in candidates:
        try:
            with open(cand, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            # Allow env override for DSN
            env_dsn = os.getenv("DB_DSN")
            if env_dsn:
                cfg["db_dsn"] = env_dsn
            # Basic validation
            if "db_dsn" not in cfg or not cfg["db_dsn"]:
                raise ValueError("db_dsn missing in config and DB_DSN not set.")
            if "tables" not in cfg:
                raise ValueError("tables section missing in config.")
            return cfg
        except FileNotFoundError as e:
            last_err = e
            continue
        except Exception as e:
            raise RuntimeError(f"Failed to parse config at '{cand}': {e}") from e

    tried = ", ".join(str(c) for c in candidates)
    raise FileNotFoundError(f"Config file not found. Tried: {tried}") from last_err

def get_engine(cfg: Dict[str, Any]) -> Engine:
    """
    Create a SQLAlchemy engine with pre_ping so stale connections auto-recover.
    """
    try:
        engine = create_engine(cfg["db_dsn"], pool_pre_ping=True, future=True)
        # quick connectivity check
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except SQLAlchemyError as e:
        raise ConnectionError(f"Failed to connect to database: {e}") from e


# ------------- Readers -------------

def read_match_clean(cfg: Dict[str, Any], columns: Optional[Iterable[str]] = None) -> pd.DataFrame:
    """
    Read the full match_clean table (historical finished matches).
    """
    table = cfg["tables"]["train"]
    cols = "*" if not columns else ", ".join(columns)
    sql = f"SELECT {cols} FROM {table} ORDER BY match_date;"
    eng = get_engine(cfg)
    try:
        return pd.read_sql(sql, eng)
    except SQLAlchemyError as e:
        raise RuntimeError(f"Failed to read table '{table}': {e}") from e


def read_fixtures_scheduled(cfg: Dict[str, Any]) -> pd.DataFrame:
    """
    Read upcoming fixtures with status='SCHEDULED'.
    """
    table = cfg["tables"]["fixtures"]
    sql = f"""
        SELECT *
        FROM {table}
        WHERE status = 'SCHEDULED'
        ORDER BY match_utc;
    """
    eng = get_engine(cfg)
    try:
        return pd.read_sql(sql, eng)
    except SQLAlchemyError as e:
        raise RuntimeError(f"Failed to read scheduled fixtures from '{table}': {e}") from e


# ------------- Writers -------------

from sqlalchemy import text, bindparam
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import SQLAlchemyError

def write_model_version(
    cfg: Dict[str, Any],
    model_name: str,
    trained_on_dset: str,
    metrics: Dict[str, Any],
    artifact_uri: str,
) -> int:
    """
    Insert a row into model_version and return model_id.
    Uses a proper bound JSONB parameter for `metrics`.
    """
    eng = get_engine(cfg)
    sql = text("""
        INSERT INTO model_version (model_name, trained_on_dset, metrics, artifact_uri)
        VALUES (:model_name, :trained_on_dset, :metrics, :artifact_uri)
        RETURNING model_id;
    """).bindparams(bindparam("metrics", type_=JSONB))

    try:
        with eng.begin() as con:
            res = con.execute(sql, {
                "model_name": model_name,
                "trained_on_dset": trained_on_dset,
                "metrics": metrics,          # pass the dict; driver adapts to JSONB
                "artifact_uri": artifact_uri,
            })
            return int(res.scalar_one())
    except SQLAlchemyError as e:
        raise RuntimeError(f"Failed to insert model_version: {e}") from e

def upsert_predictions(
    cfg: Dict[str, Any],
    df: pd.DataFrame,
) -> int:
    """
    Upsert rows into prediction on unique (model_id, fixture_id).
    Expected df columns (align to your schema):
      model_id, fixture_id, p_home, p_draw, p_away,
      expected_home_goals, expected_away_goals,
      feature_snapshot (dict or JSON string), generated_at (timestamp)
    Returns number of rows written.
    """
    table = cfg["tables"]["predictions"]
    required = [
        "model_id", "fixture_id", "p_home", "p_draw", "p_away",
        "expected_home_goals", "expected_away_goals",
        "feature_snapshot", "generated_at",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Predictions upsert missing columns: {missing}")

    # Normalize feature_snapshot to JSON strings for safety
    df = df.copy()
    try:
        df["feature_snapshot"] = df["feature_snapshot"].apply(
            lambda v: json.dumps(v) if not isinstance(v, str) else v
        )
    except Exception as e:
        raise ValueError(f"feature_snapshot must be dict/JSON-serializable or string: {e}") from e

    eng = get_engine(cfg)

    # Use PostgreSQL ON CONFLICT (model_id, fixture_id)
    # If your table uses a named unique constraint different from the pair, adjust accordingly.
    try:
        with eng.begin() as con:
            for _, row in df.iterrows():
                ins = pg_insert(text(table)).values(
                    model_id=row["model_id"],
                    fixture_id=row["fixture_id"],
                    p_home=row["p_home"],
                    p_draw=row["p_draw"],
                    p_away=row["p_away"],
                    expected_home_goals=row["expected_home_goals"],
                    expected_away_goals=row["expected_away_goals"],
                    feature_snapshot=text(f"{row['feature_snapshot']}::jsonb"),
                    generated_at=row["generated_at"],
                )
                # Because pg_insert(text(table)) is tricky, we'll do it with plain SQL text instead for portability:
                sql = text(f"""
                    INSERT INTO {table}
                      (model_id, fixture_id, p_home, p_draw, p_away,
                       expected_home_goals, expected_away_goals, feature_snapshot, generated_at)
                    VALUES
                      (:model_id, :fixture_id, :p_home, :p_draw, :p_away,
                       :ehg, :eag, :feat::jsonb, :gen_at)
                    ON CONFLICT (model_id, fixture_id)
                    DO UPDATE SET
                       p_home = EXCLUDED.p_home,
                       p_draw = EXCLUDED.p_draw,
                       p_away = EXCLUDED.p_away,
                       expected_home_goals = EXCLUDED.expected_home_goals,
                       expected_away_goals = EXCLUDED.expected_away_goals,
                       feature_snapshot = EXCLUDED.feature_snapshot,
                       generated_at = EXCLUDED.generated_at;
                """)
                con.execute(sql, {
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
        return len(df)
    except SQLAlchemyError as e:
        raise RuntimeError(f"Failed to upsert into '{table}': {e}") from e


# ------------- Convenience API for training/prediction scripts -------------

def read_training_frame(cfg: Dict[str, Any]) -> pd.DataFrame:
    """
    Return a DataFrame already shaped for feature_builder.build_features:
    Columns: Date, HomeTeam, AwayTeam, FTHG, FTAG, FTR, HS, AS, HC, AC, HY, AY, HR, AR, B365H, B365D, B365A
    """
    eng = get_engine(cfg)
    t_train = cfg["tables"]["train"]
    sql = f"""
        SELECT
            mc.match_date AS "Date",
            th.name       AS "HomeTeam",
            ta.name       AS "AwayTeam",
            mc.home_goals AS "FTHG",
            mc.away_goals AS "FTAG",
            mc.result     AS "FTR",
            mc.hs         AS "HS",
            mc."as"       AS "AS",
            mc.hc         AS "HC",
            mc.ac         AS "AC",
            mc.hy         AS "HY",
            mc.ay         AS "AY",
            mc.hr         AS "HR",
            mc.ar         AS "AR",
            mc.b365h      AS "B365H",
            mc.b365d      AS "B365D",
            mc.b365a      AS "B365A"
        FROM {t_train} mc
        JOIN team th ON th.team_id = mc.home_team_id
        JOIN team ta ON ta.team_id = mc.away_team_id
        ORDER BY mc.match_date;
    """
    try:
        return pd.read_sql(sql, eng)
    except SQLAlchemyError as e:
        raise RuntimeError(f"Failed to read/shape training frame: {e}") from e



def read_upcoming_fixtures(cfg: Dict[str, Any]) -> pd.DataFrame:
    """
    Return fixtures (SCHEDULED). You will feature-ize them in predict.py
    by joining with historicals (via feature_builder and your own logic).
    """
    return read_fixtures_scheduled(cfg)
