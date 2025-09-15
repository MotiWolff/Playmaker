import pandas as pd
import numpy as np
import pytest
from services.model.feature_builder import FeatureBuilder, FeatureBuilderConfig, EloRatingsAdapter

def test_builder_shapes_and_meta(small_df):
    fb = FeatureBuilder(EloRatingsAdapter(), FeatureBuilderConfig(min_history_games=1, form_window=2, goal_window=2))
    X, y, meta = fb.build(small_df)
    assert len(X) == len(y) == len(meta)
    assert {"Date","HomeTeam","AwayTeam"}.issubset(meta.columns)
    # יש לפחות עמודת Elo והסתברויות מהיחסים
    for col in ["home_elo","away_elo","elo_diff","b365_ph","b365_pd","b365_pa"]:
        assert col in X.columns

def test_odds_sum_close_to_one(small_df):
    fb = FeatureBuilder(EloRatingsAdapter(), FeatureBuilderConfig(min_history_games=1))
    X, y, meta = fb.build(small_df)
    mask = X[["b365_ph","b365_pd","b365_pa"]].notna().all(axis=1)
    if mask.any():
        s = X.loc[mask, ["b365_ph","b365_pd","b365_pa"]].sum(axis=1)
        assert np.allclose(s.values, 1.0, atol=1e-6)

def test_history_filter_effect(small_df):
    fb1 = FeatureBuilder(EloRatingsAdapter(), FeatureBuilderConfig(min_history_games=0))
    X0, y0, _ = fb1.build(small_df)
    fb2 = FeatureBuilder(EloRatingsAdapter(), FeatureBuilderConfig(min_history_games=2))
    X2, y2, _ = fb2.build(small_df)
    assert len(X2) <= len(X0)  # יותר היסטוריה => פחות שורות

def test_elo_alignment_guard_raises(small_df, monkeypatch):
    # מחקה Elo לא מיושר באורך – צריך להרים חריגה
    from services.model.feature_builder.builder import FeatureBuilder as FBInternal
    class BadEloPort:
        def compute_elo_pre_post(self, df):
            # מחזיר df קצר ב-1
            idx = pd.RangeIndex(len(df)-1)
            return pd.DataFrame({"home_elo_pre":0.0,"away_elo_pre":0.0}, index=idx)
    fb = FBInternal(BadEloPort())
    with pytest.raises(RuntimeError):
        fb.build(small_df)
