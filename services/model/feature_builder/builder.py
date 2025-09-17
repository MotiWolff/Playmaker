from typing import Tuple, Optional
import numpy as np, pandas as pd

from .ports import EloRatingsPort
from .config import FeatureBuilderConfig
from .validators import ColumnValidator
from .dates import DatePreprocessor
from .long_format import LongFormatter
from .rolling import RollingTeamFeatures
from .merge import PreMatchMerger
from .odds import OddsConverter

# NEW: project logger
from Playmaker.shared.logging.logger import Logger
log = Logger.get_logger(name="playmaker.model.features.feature_builder")

class FeatureBuilder:
    def __init__(
        self,
        elo_port: EloRatingsPort,
        cfg: Optional[FeatureBuilderConfig] = None,
        validator: Optional[ColumnValidator] = None,
        dateprep: Optional[DatePreprocessor] = None,
        longfmt: Optional[LongFormatter] = None,
        roller: Optional[RollingTeamFeatures] = None,
        merger: Optional[PreMatchMerger] = None,
        odds: Optional[OddsConverter] = None,
    ):
        self.elo_port = elo_port
        self.cfg = cfg or FeatureBuilderConfig()
        self.validator = validator or ColumnValidator()
        self.dateprep = dateprep or DatePreprocessor()
        self.longfmt = longfmt or LongFormatter()
        self.roller = roller or RollingTeamFeatures(
            form_window=self.cfg.form_window,
            goal_window=self.cfg.goal_window,
            min_periods_form=max(1, self.cfg.min_history_games),
            min_periods_goal=max(1, self.cfg.min_history_games),
        )
        self.merger = merger or PreMatchMerger()
        self.odds = odds or OddsConverter()

    def build(self, df_matches: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
        log.debug("feature_builder.start", extra={"rows": len(df_matches), "cols": list(df_matches.columns)})

        # Validate schema
        self.validator.validate(df_matches)

        # Dates + basic ordering
        df = self.dateprep.ensure_datetime(df_matches).sort_values("Date").reset_index(drop=True)
        if df.empty:
            log.error("feature_builder.empty_after_sort")
            raise ValueError("Input DataFrame is empty after sorting.")

        # Long -> rolling -> merge
        long = self.longfmt.to_long(df)
        log.debug("feature_builder.long_done", extra={"rows": len(long)})

        pre = self.roller.compute(long)
        log.debug("feature_builder.rolling_done", extra={"rows": len(pre)})

        m = self.merger.merge(df, pre)
        log.debug("feature_builder.merge_done", extra={"rows": len(m), "cols": list(m.columns)})

        # ELO
        elo = self.elo_port.compute_elo_pre_post(df)
        if elo.index.name is None:
            elo.index.name = "match_key"
        if len(elo) != len(df) or not (elo.index.values == pd.RangeIndex(len(df)).values).all():
            log.error("feature_builder.elo_index_mismatch",
                      extra={"elo_len": len(elo), "df_len": len(df), "elo_index_name": elo.index.name})
            raise RuntimeError("compute_elo_pre_post must be indexed by match_key (0..N-1).")

        m = m.join(elo[["home_elo_pre","away_elo_pre"]])
        m = m.rename(columns={"home_elo_pre":"home_elo","away_elo_pre":"away_elo"})
        m["elo_diff"] = m["home_elo"] - m["away_elo"]

        # Odds (non-fatal)
        try:
            m = self.odds.convert(m)
        except Exception as e:
            log.exception("feature_builder.odds_convert_failed", extra={"error": str(e)})
            # continue without odds

        # Label
        label_map = {"H":0, "D":1, "A":2}
        if "FTR" not in m.columns:
            m["FTR"] = df["FTR"].values
        y = m["FTR"].map(label_map).astype("Int64")

        # Feature columns
        feature_cols = [
            "home_form5","home_gf10","home_ga10","home_shots5","home_corn5","home_yel5","home_red5",
            "away_form5","away_gf10","away_ga10","away_shots5","away_corn5","away_yel5","away_red5",
            "b365_ph","b365_pd","b365_pa",
            "home_rest_days","away_rest_days",
            "home_elo","away_elo","elo_diff",
        ]
        for c in feature_cols:
            if c not in m.columns:
                m[c] = np.nan

        # Sanity columns
        for needed in ["home_n_prior","away_n_prior"]:
            if needed not in m.columns:
                log.error("feature_builder.missing_prior_counts", extra={"missing": needed})
                raise RuntimeError(f"Internal error: missing {needed} after merge.")

        # History filter
        mh = self.cfg.min_history_games
        hist_ok = (m["home_n_prior"] >= mh) & (m["away_n_prior"] >= mh)
        if not hist_ok.any() and mh > 0:
            log.warning("feature_builder.relax_history_filter_both_to_either", extra={"min_history_games": mh})
            hist_ok = (m["home_n_prior"] >= mh) | (m["away_n_prior"] >= mh)
        if not hist_ok.any():
            log.warning("feature_builder.relax_history_filter_to_none_demo")
            hist_ok = pd.Series(True, index=m.index)

        # Final X/y/meta
        X = m.loc[hist_ok, feature_cols].copy()
        y = y.loc[hist_ok].copy()

        # Impute
        X = X.apply(lambda col: col.fillna(col.mean()), axis=0)
        if X.isna().any().any():
            log.warning("feature_builder.fallback_fillna_zero_after_mean")
            X = X.fillna(0.0)

        meta = df.loc[X.index, ["Date","HomeTeam","AwayTeam"]].reset_index(drop=True)

        log.info("feature_builder.success",
                 extra={"X_rows": len(X), "y_rows": len(y), "meta_rows": len(meta), "features": feature_cols})
        return X.reset_index(drop=True), y.reset_index(drop=True), meta
