# services/model/tests/test_predict_helpers.py
import numpy as np
import pandas as pd
import pytest

# Import the internal helpers directly from predict.py
from services.model.predict import _adapt_history_schema, _pre_match_rolling


# ---------- Fixtures ----------

@pytest.fixture
def team_map_df():
    # Minimal team lookup like your DB 'team' table
    return pd.DataFrame({
        "team_id": [1, 2, 3, 4, 5],
        "name":    ["Team A", "Team B", "Team C", "Team D", "Team E"],
    })


@pytest.fixture
def hist_db_minimal(team_map_df):
    # A minimal "DB-shaped" history frame with IDs and different column names.
    # No FTR column; it should be derived from goals by _adapt_history_schema.
    return pd.DataFrame({
        "match_date": pd.to_datetime([
            "2024-08-01", "2024-08-08", "2024-08-15", "2024-08-22"
        ]),
        "home_team_id": [1, 3, 4, 1],   # A, C, D, A
        "away_team_id": [2, 1, 1, 5],   # B, A, A, E
        "home_goals":   [2, 1, 0, 0],
        "away_goals":   [0, 1, 3, 1],
        # Optional stats omitted on purpose (function should handle missing)
    })


@pytest.fixture
def hist_training_like():
    """
    A training-like history frame with the columns expected *after* adaptation:
    Date, HomeTeam, AwayTeam, FTHG, FTAG, FTR, plus optional HS/AS/HC/AC/HY/AY/HR/AR.
    We'll include a few optional stats so _pre_match_rolling can compute rolling shots, etc.
    """
    return pd.DataFrame({
        "Date": pd.to_datetime([
            "2024-08-01", "2024-08-08", "2024-08-15", "2024-08-22"
        ]),
        "HomeTeam": ["Team A", "Team C", "Team D", "Team A"],
        "AwayTeam": ["Team B", "Team A", "Team A", "Team E"],
        "FTHG":     [2, 1, 0, 0],
        "FTAG":     [0, 1, 3, 1],
        "FTR":      ["H", "D", "A", "A"],
        # Optional, per-match stats:
        "HS": [10, 8, 6, 6],  # home shots
        "AS": [5,  7, 9, 4],  # away shots
        "HC": [4,  5, 3, 2],
        "AC": [2,  4, 4, 3],
        "HY": [1,  2, 1, 0],
        "AY": [2,  1, 2, 1],
        "HR": [0,  0, 0, 0],
        "AR": [0,  0, 0, 0],
    })


# ---------- Tests for _adapt_history_schema ----------

def test_adapt_history_schema_renames_and_derives_ftr(hist_db_minimal, team_map_df):
    """
    Ensures that:
      - IDs are mapped to team names (HomeTeam/AwayTeam),
      - DB column names are renamed to training names,
      - FTR is derived from goals when missing.
    """
    out = _adapt_history_schema(hist_db_minimal, team_map_df)

    # Required columns exist
    for col in ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"]:
        assert col in out.columns, f"Missing column: {col}"

    # Check some known mappings/values
    assert out.loc[0, "HomeTeam"] == "Team A"
    assert out.loc[0, "AwayTeam"] == "Team B"
    assert out.loc[0, "FTHG"] == 2 and out.loc[0, "FTAG"] == 0
    assert out.loc[0, "FTR"] == "H"   # 2-0 => home win

    # 2024-08-08: Team C (home) 1 - 1 Team A => Draw
    assert out.loc[1, "FTR"] == "D"

    # 2024-08-15: Team D (home) 0 - 3 Team A => Away win
    assert out.loc[2, "FTR"] == "A"


def test_adapt_history_schema_missing_required_columns_raises(team_map_df):
    # Remove a required column to force an error
    bad = pd.DataFrame({
        "home_team_id": [1],
        "away_team_id": [2],
        "home_goals":   [1],
        "away_goals":   [0],
        # "match_date" missing
    })
    with pytest.raises(ValueError):
        _adapt_history_schema(bad, team_map_df)


# ---------- Tests for _pre_match_rolling ----------

def test_pre_match_rolling_uses_only_past_matches(hist_training_like):
    """
    As-of 2024-08-30, Team A has four prior matches (perspective stats):
      Points per match (Team A): [3, 1, 3, 0] -> mean = 1.75
      GF per match               [2, 1, 3, 0] -> mean = 1.50
      GA per match               [0, 1, 0, 1] -> mean = 0.50
      Shots per match            [10,7,9,6]   -> mean = 8.00
      n_prior = 4
    """
    as_of = pd.to_datetime("2024-08-30")
    out = _pre_match_rolling(hist_training_like, team="Team A", as_of=as_of)

    assert out["n_prior"] == 4
    assert np.isclose(out["form5"], 1.75, atol=1e-6)
    assert np.isclose(out["gf10"],  1.50, atol=1e-6)
    assert np.isclose(out["ga10"],  0.50, atol=1e-6)
    assert np.isclose(out["shots5"], 8.00, atol=1e-6)


def test_pre_match_rolling_respects_as_of_cutoff(hist_training_like):
    """
    As-of 2024-08-16, Team A has only the first three matches:
      Points: [3,1,3] mean = 7/3 ≈ 2.3333
      GF:     [2,1,3] mean = 2.0
      GA:     [0,1,0] mean = 0.3333
      Shots:  [10,7,9] mean = 8.6667
      n_prior = 3
    """
    as_of = pd.to_datetime("2024-08-16")
    out = _pre_match_rolling(hist_training_like, team="Team A", as_of=as_of)

    assert out["n_prior"] == 3
    assert np.isclose(out["form5"], 7/3, atol=1e-6)
    assert np.isclose(out["gf10"],  2.0, atol=1e-6)
    assert np.isclose(out["ga10"],  1/3, atol=1e-6)
    assert np.isclose(out["shots5"], 26/3, atol=1e-6)  # 10+7+9 = 26


def test_pre_match_rolling_handles_no_history_gracefully(hist_training_like):
    """
    For a team with no prior matches, we expect NaNs and n_prior=0.
    """
    as_of = pd.to_datetime("2024-08-30")
    out = _pre_match_rolling(hist_training_like, team="Team Z", as_of=as_of)
    assert out["n_prior"] == 0
    for k in ["form5", "gf10", "ga10", "shots5", "corn5", "yel5", "red5"]:
        assert pd.isna(out[k])
