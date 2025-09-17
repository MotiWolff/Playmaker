from __future__ import annotations
from typing import List
import numpy as np
import pandas as pd
from Playmaker.shared.logging.logger import Logger

log = Logger.get_logger(name="playmaker.model.predictor.imputer")

def _get_feature_builder():
    """
    Build a FeatureBuilder with a safe Elo adapter.
    Falls back to a zero-Elo adapter if EloRatingsAdapter isn't available.
    """
    try:
        # ✅ correct package: features (plural)
        from services.model.feature_builder import FeatureBuilder, EloRatingsAdapter  # type: ignore
        log.debug("imputer.fb_with_real_elo")
        return FeatureBuilder(elo_port=EloRatingsAdapter())
    except Exception as e:
        log.warning("imputer.fb_fallback_fake_elo", extra={"error": str(e)})
        from services.model.feature_builder import FeatureBuilder  # type: ignore
        class _FakeEloAdapter:
            def compute_elo_pre_post(self, df: pd.DataFrame) -> pd.DataFrame:
                n = len(df)
                idx = pd.RangeIndex(n)
                idx.name = "match_key"
                return pd.DataFrame({"home_elo_pre": 0.0, "away_elo_pre": 0.0}, index=idx)
        return FeatureBuilder(elo_port=_FakeEloAdapter())

def _compute_training_means(df_hist: pd.DataFrame) -> pd.Series:
    fb = _get_feature_builder()
    X, _, _ = fb.build(df_hist)
    if X is None or X.empty:
        log.error("imputer.empty_training_matrix")
        raise ValueError("Cannot compute training means: feature matrix is empty.")
    means = X.mean(numeric_only=True).astype(float)
    log.info("imputer.training_means", extra={"n_features": int(means.shape[0])})
    return means

class TrainMeansImputer:
    """Recompute training feature means and align inference matrix to model order."""
    def fit_training_means(self, df_hist_for_means: pd.DataFrame) -> pd.Series:
        return _compute_training_means(df_hist_for_means)

    def transform(self, Xf: pd.DataFrame, train_means: pd.Series, feature_order: List[str]) -> pd.DataFrame:
        Xf = Xf.copy()
        # ensure expected columns exist
        missing = [c for c in feature_order if c not in Xf.columns]
        for c in missing:
            Xf[c] = np.nan
        if missing:
            log.debug("imputer.added_missing_cols", extra={"missing": missing})

        # fill missing
        for c in feature_order:
            col = Xf[c]
            if col.isna().any():
                fill_val = train_means.get(c, float(col.mean()) if pd.api.types.is_numeric_dtype(col) else 0.0)
                Xf[c] = col.fillna(fill_val)

        # align order
        Xf = Xf[feature_order]

        # numeric dtype
        for c in feature_order:
            if not pd.api.types.is_numeric_dtype(Xf[c]):
                Xf[c] = pd.to_numeric(Xf[c], errors="coerce").fillna(train_means.get(c, 0.0))

        log.info("imputer.transformed", extra={"rows": len(Xf), "cols": len(feature_order)})
        return Xf
