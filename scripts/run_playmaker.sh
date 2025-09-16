#!/usr/bin/env bash
set -euo pipefail

# Playmaker quick runner
# - Uses local Python venv for model train/predict
# - Uses psql for minimal DB setup (view + fixture seeding)
#
# Prereqs:
# - Python 3.11 installed
# - PostgreSQL client (psql) installed
# - For UI, Node 18+ (optional)

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# ----------------------
# Config (from env)
# ----------------------
# You can export these before running, or create a local .env file and source it here.
# Example:
#   export DB_HOST=...
#   export DB_USER=...
#   export DB_PASS=...
#   export DB_NAME=playmaker
#   export DB_PORT=5432

# If a project-local env file exists (not committed), source it.
if [[ -f ".env.local" ]]; then
  # shellcheck disable=SC1091
  source .env.local
fi

DB_HOST=${DB_HOST:-""}
DB_PORT=${DB_PORT:-"5432"}
DB_NAME=${DB_NAME:-"playmaker"}
DB_USER=${DB_USER:-""}
DB_PASS=${DB_PASS:-""}

if [[ -z "$DB_HOST" || -z "$DB_USER" || -z "$DB_PASS" ]]; then
  echo "Missing DB env vars. Please export DB_HOST, DB_USER, DB_PASS (and optionally DB_NAME, DB_PORT) before running." >&2
  exit 1
fi

DB_DSN="postgresql+psycopg://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

VENV_DIR=".venv"
MODEL_REQ="services/model/requirements.txt"
CFG_PATH="services/model/config/config.yaml"

echo "[1/6] Setting up Python venv..."
if [[ ! -d "$VENV_DIR" ]]; then
  python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
pip install --upgrade pip >/dev/null
pip install -r "$MODEL_REQ" >/dev/null

export PYTHONPATH="${PROJECT_ROOT}"
export DB_DSN

echo "[2/6] Ensuring match_clean view exists (mapped from matches_cleaned)..."
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 -c "\
DROP VIEW IF EXISTS match_clean; \
CREATE OR REPLACE VIEW match_clean AS \
SELECT \
  match_id, \
  utc_date::date AS match_date, \
  home_team_id, away_team_id, \
  score_full_time_home AS home_goals, \
  score_full_time_away AS away_goals, \
  winner AS result, \
  NULL::int AS hs, NULL::int AS \"as\", NULL::int AS hc, NULL::int AS ac, \
  NULL::int AS hy, NULL::int AS ay, NULL::int AS hr, NULL::int AS ar, \
  NULL::real AS b365h, NULL::real AS b365d, NULL::real AS b365a \
FROM matches_cleaned;" >/dev/null

echo "[3/6] Seeding fixtures (SCHEDULED) from raw_matches (no DB writes if already present)..."
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 -c "\
INSERT INTO fixture (fixture_id, match_utc, status, home_team_id, away_team_id, competition_id, season_id) \
SELECT \
  match_id, utc_date, \
  COALESCE(NULLIF(status,''),'SCHEDULED'), \
  home_team_id, away_team_id, competition_id, season_id \
FROM raw_matches \
WHERE home_team_id IS NOT NULL \
  AND away_team_id IS NOT NULL \
  AND (score_winner IS NULL OR status = 'SCHEDULED') \
ON CONFLICT (fixture_id) DO NOTHING; \
UPDATE fixture SET status='SCHEDULED' \
WHERE status IS NULL OR status NOT IN ('SCHEDULED','TIMED') OR (status <> 'FINISHED' AND match_utc > NOW());" >/dev/null

echo "[4/6] Training model (writes model_version)..."
TRAIN_OUT=$(python -m services.model.trainer.pipeline 2>&1 | tee /dev/stderr)
MODEL_ID=$(echo "$TRAIN_OUT" | awk '/model_id\s*:\s*/{print $3}' | tail -n1)
if [[ -z "$MODEL_ID" ]]; then
  echo "Failed to parse model_id from training output." >&2
  exit 1
fi
echo "     model_id=${MODEL_ID}"

echo "[5/6] Scoring upcoming fixtures (upsert predictions)..."
python -m services.model.predictor.pipeline --model_id "$MODEL_ID" --limit 200

echo "[6/6] Summary"
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\
SELECT 'fixtures_scheduled' AS k, count(*) AS v FROM fixture WHERE status='SCHEDULED' \
UNION ALL SELECT 'predictions_total', count(*) FROM prediction \
UNION ALL SELECT 'models_total', count(*) FROM model_version;"

echo "\nDone. Next steps:"
echo "- To view predictions: run a SELECT joining prediction + fixture + teams as shown in README/.cursorrules."
echo "- To run via Docker instead, use: docker run --rm -e DB_DSN=... playmaker-ml-model python -m services.model.predictor.pipeline --model_id ${MODEL_ID} --limit 100"

