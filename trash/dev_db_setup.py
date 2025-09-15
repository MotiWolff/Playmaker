# services/model/dev_db_setup.py
from __future__ import annotations
from pathlib import Path
import os
from sqlalchemy import text
from services.model.data_access.data_access import load_cfg, get_engine

# ---- Tables (idempotent) ----
SCHEMA_STMTS = [
    # Teams
    """
    CREATE TABLE IF NOT EXISTS team (
      team_id SERIAL PRIMARY KEY,
      name    TEXT NOT NULL UNIQUE
    );
    """,
    # Cleaned historical matches (fits our adapters; note the quoted "as" column)
    """
    CREATE TABLE IF NOT EXISTS match_clean (
      match_id      BIGSERIAL PRIMARY KEY,
      match_date    DATE NOT NULL,
      home_team_id  INT NOT NULL REFERENCES team(team_id),
      away_team_id  INT NOT NULL REFERENCES team(team_id),
      home_goals    INT,
      away_goals    INT,
      result        CHAR(1) CHECK (result IN ('H','D','A')),
      hs INT, "as" INT, hc INT, ac INT, hy INT, ay INT, hr INT, ar INT,
      b365h NUMERIC(8,3), b365d NUMERIC(8,3), b365a NUMERIC(8,3)
    );
    """,
    # Upcoming fixtures to score
    """
    CREATE TABLE IF NOT EXISTS fixture (
      fixture_id        BIGSERIAL PRIMARY KEY,
      provider_match_id TEXT,
      competition_code  TEXT,
      matchday          INT,
      match_utc         TIMESTAMPTZ,
      home_team_id      INT REFERENCES team(team_id),
      away_team_id      INT REFERENCES team(team_id),
      status            TEXT
    );
    """,
    # Model registry
    """
    CREATE TABLE IF NOT EXISTS model_version (
      model_id        SERIAL PRIMARY KEY,
      model_name      TEXT NOT NULL,
      trained_on_dset TEXT,
      metrics         JSONB,
      artifact_uri    TEXT,
      created_at      TIMESTAMPTZ DEFAULT now()
    );
    """,
    # Predictions (unique per model_id + fixture_id)
    """
    CREATE TABLE IF NOT EXISTS prediction (
      pred_id             BIGSERIAL PRIMARY KEY,
      model_id            INT NOT NULL REFERENCES model_version(model_id),
      fixture_id          BIGINT NOT NULL REFERENCES fixture(fixture_id),
      p_home              REAL,
      p_draw              REAL,
      p_away              REAL,
      expected_home_goals REAL,
      expected_away_goals REAL,
      feature_snapshot    JSONB DEFAULT '{}'::jsonb,
      generated_at        TIMESTAMPTZ DEFAULT now(),
      CONSTRAINT unique_pred UNIQUE (model_id, fixture_id)
    );
    """
]

# ---- Seed data (small, re-runnable) ----
SEED_STMTS = [
    # Teams (ON CONFLICT to avoid duplicates)
    """
    INSERT INTO team (name) VALUES
      ('Team A'), ('Team B'), ('Team C')
    ON CONFLICT (name) DO NOTHING;
    """,
    # Clear previous demo rows (optional — keeps the demo idempotent)
    "DELETE FROM match_clean;",
    "ALTER SEQUENCE match_clean_match_id_seq RESTART WITH 1;",
    "DELETE FROM fixture;",
    "ALTER SEQUENCE fixture_fixture_id_seq RESTART WITH 1;",
    # 4 historical matches among A,B,C with some stats & odds
    """
    INSERT INTO match_clean (match_date, home_team_id, away_team_id, home_goals, away_goals, result,
                             hs, "as", hc, ac, hy, ay, hr, ar, b365h, b365d, b365a)
    SELECT '2024-08-01', th.team_id, ta.team_id, 2, 0, 'H',
           10, 5, 4, 2, 1, 2, 0, 0, 1.90, 3.40, 4.00
    FROM team th, team ta WHERE th.name='Team A' AND ta.name='Team B';
    """,
    """
    INSERT INTO match_clean (match_date, home_team_id, away_team_id, home_goals, away_goals, result,
                             hs, "as", hc, ac, hy, ay, hr, ar, b365h, b365d, b365a)
    SELECT '2024-08-08', th.team_id, ta.team_id, 1, 1, 'D',
           8, 7, 5, 4, 2, 1, 0, 0, 2.70, 3.10, 2.80
    FROM team th, team ta WHERE th.name='Team C' AND ta.name='Team A';
    """,
    """
    INSERT INTO match_clean (match_date, home_team_id, away_team_id, home_goals, away_goals, result,
                             hs, "as", hc, ac, hy, ay, hr, ar, b365h, b365d, b365a)
    SELECT '2024-08-15', th.team_id, ta.team_id, 0, 1, 'A',
           6, 9, 3, 4, 1, 2, 0, 0, 3.60, 3.30, 2.00
    FROM team th, team ta WHERE th.name='Team B' AND ta.name='Team A';
    """,
    """
    INSERT INTO match_clean (match_date, home_team_id, away_team_id, home_goals, away_goals, result,
                             hs, "as", hc, ac, hy, ay, hr, ar, b365h, b365d, b365a)
    SELECT '2024-08-22', th.team_id, ta.team_id, 0, 1, 'A',
           6, 4, 2, 3, 0, 1, 0, 0, 2.20, 3.20, 3.20
    FROM team th, team ta WHERE th.name='Team A' AND ta.name='Team C';
    """,
    # One upcoming fixture to score (UTC time)
    """
    INSERT INTO fixture (provider_match_id, competition_code, matchday, match_utc, home_team_id, away_team_id, status)
    SELECT 'demo-001','X',1,'2025-09-20 18:00:00+00', th.team_id, ta.team_id, 'SCHEDULED'
    FROM team th, team ta WHERE th.name='Team A' AND ta.name='Team C';
    """
]

def main():
    # Resolve YAML relative to THIS file so working dir never matters
    cfg_path = Path(__file__).resolve().parent / "config" / "config.yaml"
    try:
        cfg = load_cfg(str(cfg_path))
    except FileNotFoundError:
        # Fallback: use inline config so you can run even without the YAML
        cfg = {
            "db_dsn": os.getenv("DB_DSN", "postgresql+psycopg://postgres:postgres@localhost:5432/soccer"),
            "tables": {
                "train": "match_clean",
                "fixtures": "fixture",
                "predictions": "prediction",
                "versions": "model_version",
            },
            "seed": 42,
        }
        print(f"[Info] YAML not found at {cfg_path}. Using inline fallback config.")
    eng = get_engine(cfg)

    print(">> Creating tables (if not exist)…")
    with eng.begin() as con:
        for stmt in SCHEMA_STMTS:
            con.execute(text(stmt))

    print(">> Seeding tiny demo data…")
    with eng.begin() as con:
        for stmt in SEED_STMTS:
            con.execute(text(stmt))

    # Quick counts so you can see it worked
    counts = {}
    with eng.connect() as con:
        for t in ["team", "match_clean", "fixture", "model_version", "prediction"]:
            res = con.execute(text(f"SELECT COUNT(*) FROM {t};"))
            counts[t] = res.scalar_one()
    print(">> Row counts:", counts)
    print("✅ DB ready for training.")

if __name__ == "__main__":
    main()