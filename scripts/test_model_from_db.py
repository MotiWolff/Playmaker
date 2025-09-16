import os
import sys
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine, text

from services.model.ratings import compute_elo_pre_post


def map_winner_to_ftr(row: pd.Series) -> str:
    """Map full-time result to Elo FTR label using scores, else winner string."""
    h = row.get("score_full_time_home")
    a = row.get("score_full_time_away")
    if pd.notnull(h) and pd.notnull(a):
        if h > a:
            return "H"
        if h < a:
            return "A"
        return "D"
    # fallback to winner column if present (values like 'HOME','AWAY','DRAW')
    w: Optional[str] = row.get("winner")
    if isinstance(w, str):
        w_upper = w.upper()
        if w_upper.startswith("HOME"):
            return "H"
        if w_upper.startswith("AWAY"):
            return "A"
        return "D"
    return "D"


def main() -> None:
    database_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if not database_url:
        print("ERROR: Set DATABASE_URL or POSTGRES_URL", file=sys.stderr)
        sys.exit(1)

    engine = create_engine(database_url)

    # Adjust table if you have a cleaned table (e.g., clean_matches)
    sql = text(
        """
        SELECT
          match_id,
          utc_date::timestamp AS Date,
          home_team_id AS HomeTeam,
          away_team_id AS AwayTeam,
          score_full_time_home,
          score_full_time_away,
          winner
        FROM raw_matches
        WHERE utc_date IS NOT NULL
        ORDER BY utc_date
        LIMIT 5000
        """
    )

    df = pd.read_sql(sql, engine)
    if df.empty:
        print("No matches found in raw_matches.")
        return

    df["FTR"] = df.apply(map_winner_to_ftr, axis=1)

    # Run Elo
    elo = compute_elo_pre_post(
        df_matches=df[["Date", "HomeTeam", "AwayTeam", "FTR"]].copy()
    )

    print("Elo results (head):")
    print(elo.head())
    print("\nTotal rows:", len(elo))


if __name__ == "__main__":
    main()


