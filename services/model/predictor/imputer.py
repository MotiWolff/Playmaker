# services/model/predictor/imputer.py
from __future__ import annotations
from typing import List
import numpy as np
import pandas as pd

def _get_feature_builder():
    """
    Build a FeatureBuilder with a safe Elo adapter.
    Falls back to a zero-Elo adapter if EloRatingsAdapter isn't available.
    """
    try:
        # ✅ correct package: features (plural)
        from services.model.feature_builder import FeatureBuilder, EloRatingsAdapter
        return FeatureBuilder(elo_port=EloRatingsAdapter())
    except Exception:
        from services.model.feature_builder import FeatureBuilder
        class _FakeEloAdapter:
            def compute_elo_pre_post(self, df: pd.DataFrame) -> pd.DataFrame:
                n = len(df)
                idx = pd.RangeIndex(n)
                idx.name = "match_key"
                return pd.DataFrame(
                    {"home_elo_pre": 0.0, "away_elo_pre": 0.0},
                    index=idx,
                )
        return FeatureBuilder(elo_port=_FakeEloAdapter())

def _compute_training_means(df_hist: pd.DataFrame) -> pd.Series:
    fb = _get_feature_builder()
    X, _, _ = fb.build(df_hist)
    if X is None or X.empty:
        raise ValueError("Cannot compute training means: feature matrix is empty.")
    # numeric-only mean; cast to float for safety
    return X.mean(numeric_only=True).astype(float)

class TrainMeansImputer:
    """Recompute training feature means and align inference matrix to model order."""
    def fit_training_means(self, df_hist_for_means: pd.DataFrame) -> pd.Series:
        return _compute_training_means(df_hist_for_means)

    def transform(self, Xf: pd.DataFrame, train_means: pd.Series, feature_order: List[str]) -> pd.DataFrame:
        Xf = Xf.copy()

        # ensure all expected columns exist
        for c in feature_order:
            if c not in Xf.columns:
                Xf[c] = np.nan

        # fill missing by training means (fallback to column mean if absent)
        for c in feature_order:
            col = Xf[c]
            if col.isna().any():
                fill_val = train_means.get(c, float(col.mean()) if pd.api.types.is_numeric_dtype(col) else 0.0)
                Xf[c] = col.fillna(fill_val)

        # align column order exactly to the model
        Xf = Xf[feature_order]

        # ensure numeric dtype (model expects numeric features)
        for c in feature_order:
            if not pd.api.types.is_numeric_dtype(Xf[c]):
                Xf[c] = pd.to_numeric(Xf[c], errors="coerce").fillna(train_means.get(c, 0.0))

        return Xf
