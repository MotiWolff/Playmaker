#!/usr/bin/env python3
"""
Refresh job:
1) Run data_loader to fetch new fixtures and update DB tables
2) Optionally run data_cleaner (if needed by pipeline)
3) Call API admin endpoint to regenerate predictions for future fixtures

Environment:
- DATABASE_URL (required)
- API_BASE_URL (default http://localhost:8000)
- FOOTBALL_API_KEY (if loader needs it)
"""

import os
import sys
import subprocess
import time
import requests


def run_loader() -> None:
    print("[refresh] Running data_loader...")
    env = os.environ.copy()
    cmd = [sys.executable, "-m", "services.data_loader.main"]
    # Execute in project root so relative imports work
    result = subprocess.run(cmd, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"data_loader failed with code {result.returncode}")


def regenerate_predictions() -> None:
    api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
    url = f"{api_base.rstrip('/')}/admin/regenerate_predictions"
    print(f"[refresh] Regenerating predictions via {url} ...")
    resp = requests.post(url, timeout=60)
    resp.raise_for_status()
    print(f"[refresh] {resp.text}")


def main() -> None:
    if not os.getenv("DATABASE_URL"):
        print("ERROR: DATABASE_URL is required in environment", file=sys.stderr)
        sys.exit(2)

    start = time.time()
    run_loader()
    regenerate_predictions()
    took = time.time() - start
    print(f"[refresh] Completed in {took:.1f}s")


if __name__ == "__main__":
    main()


