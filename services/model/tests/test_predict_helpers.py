# services/model/tests/test_predict_helpers.py
import numpy as np
import pandas as pd
import pytest

# Import the internal helpers directly from predict.py
from trash.predict import _adapt_history_schema, _pre_match_rolling

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
    # Minimal "DB-shaped" history with IDs (no FTR column)
    return pd.DataFrame({
        "match_date": pd.to_datetime([
            "2024-08-01", "2024-08-08", "2024-08-15", "2024-08-22"
        ]),
        "home_team_id": [1, 3, 4, 1],   # A, C, D, A
        "away_team_id": [2, 1, 1, 5],   # B, A, A, E
        "home_goals":   [2, 1, 0, 0],
        "away_goals":   [0, 1, 3, 1],
        # Optional stats omitted intentionally
    })

@pytest.fixture
def hist_training_like():
    # Training-like history (already in training schema)
    return pd.DataFrame({
        "Date": pd.to_datetime([
            "2024-08-01", "2024-08-08", "2024-08-15", "2024-08-22"
        ]),
        "HomeTeam": ["Team A", "Team C", "Team D", "Team A"],
        "AwayTeam": ["Team B", "Team A", "Team A", "Team E"],
        "FTHG":     [2, 1, 0, 0],
        "FTAG":     [0, 1, 3, 1],
        "FTR":      ["H", "D", "A", "A"],
        "HS": [10, 8, 6, 6],
        "AS": [5,  7, 9, 4],
        "HC": [4,  5, 3, 2],
        "AC": [2,  4, 4, 3],
        "HY": [1,  2, 1, 0],
        "AY": [2,  1, 2, 1],
        "HR": [0,  0, 0, 0],
        "AR": [0,  0, 0, 0],
    })

# ---------- Tests for _adapt_history_schema ----------

def test_adapt_history_schema_renames_and_derives_ftr(hist_db_minimal, team_map_df):
    out = _adapt_history_schema(hist_db_minimal, team_map_df)
    for col in ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"]:
        assert col in out.columns
    assert out.loc[0, "HomeTeam"] == "Team A"
    assert out.loc[0, "AwayTeam"] == "Team B"
    assert out.loc[0, "FTHG"] == 2 and out.loc[0, "FTAG"] == 0
    assert out.loc[0, "FTR"] == "H"   # 2-0 => home win
    assert out.loc[1, "FTR"] == "D"   # 1-1 => draw
    assert out.loc[2, "FTR"] == "A"   # 0-3 => away win

def test_adapt_history_schema_missing_required_columns_raises(team_map_df):
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
    as_of = pd.to_datetime("2024-08-30")
    out = _pre_match_rolling(hist_training_like, team="Team A", as_of=as_of)
    assert out["n_prior"] == 4
    assert np.isclose(out["form5"], 1.75, atol=1e-6)
    assert np.isclose(out["gf10"],  1.50, atol=1e-6)
    assert np.isclose(out["ga10"],  0.50, atol=1e-6)
    assert np.isclose(out["shots5"], 8.00, atol=1e-6)

def test_pre_match_rolling_respects_as_of_cutoff(hist_training_like):
    as_of = pd.to_datetime("2024-08-16")
    out = _pre_match_rolling(hist_training_like, team="Team A", as_of=as_of)
    assert out["n_prior"] == 3
    assert np.isclose(out["form5"], 7/3, atol=1e-6)
    assert np.isclose(out["gf10"],  2.0, atol=1e-6)
    assert np.isclose(out["ga10"],  1/3, atol=1e-6)
    assert np.isclose(out["shots5"], 26/3, atol=1e-6)

def test_pre_match_rolling_handles_no_history_gracefully(hist_training_like):
    as_of = pd.to_datetime("2024-08-30")
    out = _pre_match_rolling(hist_training_like, team="Team Z", as_of=as_of)
    assert out["n_prior"] == 0
    for k in ["form5", "gf10", "ga10", "shots5", "corn5", "yel5", "red5"]:
        assert pd.isna(out[k])

from services.model.data_access.data_access import load_cfg, read_training_frame, read_upcoming_fixtures
cfg = load_cfg("services/model/config/config.yaml")

df_train = read_training_frame(cfg)
print(df_train.shape, df_train.columns.tolist())
print(df_train.head(2))

df_fix = read_upcoming_fixtures(cfg)
print(df_fix.shape)
print(df_fix.head(2))