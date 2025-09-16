#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Load local env if present (not committed)
if [[ -f ".env.local" ]]; then
  # shellcheck disable=SC1091
  source .env.local
fi

if [[ -z "${DB_DSN:-}" ]]; then
  echo "DB_DSN not set. Export DB_DSN before running (postgresql+psycopg://user:pass@host:port/db)." >&2
  exit 1
fi

# Ensure deps (odds_winner) are installed in current Python env
REQS="services/odds_winner/requirements.txt"
if command -v python >/dev/null 2>&1; then
  python -m pip install --upgrade pip >/dev/null 2>&1 || true
  python -m pip install -r "$REQS" >/dev/null 2>&1 || true
elif command -v python3 >/dev/null 2>&1; then
  python3 -m pip install --upgrade pip >/dev/null 2>&1 || true
  python3 -m pip install -r "$REQS" >/dev/null 2>&1 || true
else
  echo "Python not found. Activate your venv or install Python 3.11+ and re-run." >&2
  exit 1
fi

# Make project importable as a package root
export PYTHONPATH="$PROJECT_ROOT"

echo "[odds-winner] Running scraper once..."
if command -v python >/dev/null 2>&1; then
  python -m services.odds_winner.app.main
else
  python3 -m services.odds_winner.app.main
fi

echo "Done. Check tables 'soccer_odds' (existing) or your target odds tables if you extend models."

