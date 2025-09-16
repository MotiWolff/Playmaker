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
        self.validator.validate(df_matches)
        df = self.dateprep.ensure_datetime(df_matches).sort_values("Date").reset_index(drop=True)
        if df.empty:
            raise ValueError("Input DataFrame is empty after sorting.")

        long = self.longfmt.to_long(df)
        pre = self.roller.compute(long)
        m = self.merger.merge(df, pre)

        elo = self.elo_port.compute_elo_pre_post(df)
        if elo.index.name is None:
            elo.index.name = "match_key"
        if len(elo) != len(df) or not (elo.index.values == pd.RangeIndex(len(df)).values).all():
            raise RuntimeError("compute_elo_pre_post must be indexed by match_key (0..N-1).")
        m = m.join(elo[["home_elo_pre","away_elo_pre"]])
        m = m.rename(columns={"home_elo_pre":"home_elo","away_elo_pre":"away_elo"})
        m["elo_diff"] = m["home_elo"] - m["away_elo"]

        try:
            m = self.odds.convert(m)
        except Exception as e:
            print(f"[Warning] Odds conversion failed; continuing without odds: {e}")

        label_map = {"H":0, "D":1, "A":2}
        if "FTR" not in m.columns:
            m["FTR"] = df["FTR"].values
        y = m["FTR"].map(label_map).astype("Int64")

        feature_cols = [
            "home_form5","home_gf10","home_ga10","home_shots5","home_corn5","home_yel5","home_red5",
            "away_form5","away_gf10","away_ga10","away_shots5","away_corn5","away_yel5","away_red5",
            "b365_ph","b365_pd","b365_pa",
            "home_rest_days","away_rest_days",
            "home_elo","away_elo","elo_diff",
        ]
        for c in feature_cols:
            if c not in m.columns: m[c] = np.nan

        for needed in ["home_n_prior","away_n_prior"]:
            if needed not in m.columns:
                raise RuntimeError(f"Internal error: missing {needed} after merge.")

        mh = self.cfg.min_history_games
        hist_ok = (m["home_n_prior"] >= mh) & (m["away_n_prior"] >= mh)
        if not hist_ok.any() and mh > 0:
            print(f"[Warning] No rows pass both-team history >= {mh}. Relaxing to either-team.")
            hist_ok = (m["home_n_prior"] >= mh) | (m["away_n_prior"] >= mh)
        if not hist_ok.any():
            print("[Warning] Still empty after relaxation. Using no history filter (demo mode).")
            hist_ok = pd.Series(True, index=m.index)

        X = m.loc[hist_ok, feature_cols].copy()
        y = y.loc[hist_ok].copy()

        X = X.apply(lambda col: col.fillna(col.mean()), axis=0)
        if X.isna().any().any():
            X = X.fillna(0.0)

        meta = df.loc[X.index, ["Date","HomeTeam","AwayTeam"]].reset_index(drop=True)
        return X.reset_index(drop=True), y.reset_index(drop=True), meta
