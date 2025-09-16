from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Dict, Any, List, Tuple
import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator


class ArtifactLoader(Protocol):
    def load(self, artifact_path: str | None = None) -> Tuple[BaseEstimator, Dict[str, Any]]: ...


class HistoryAdapter(Protocol):
    def adapt(self, df_hist_db: pd.DataFrame, team_map: pd.DataFrame) -> pd.DataFrame: ...


class EloTimelineBuilder(Protocol):
    def build(self, df_hist: pd.DataFrame) -> Dict[str, pd.DataFrame]: ...


class FixturesRepository(Protocol):
    def list_scheduled(self, limit: int | None = None) -> pd.DataFrame: ...


class FeatureRowsBuilder(Protocol):
    def build_rows(
        self,
        fixtures: pd.DataFrame,
        history: pd.DataFrame,
        elo_timeline: Dict[str, pd.DataFrame] | None = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]: ...


class ImputerAligner(Protocol):
    def fit_training_means(self, df_hist_for_means: pd.DataFrame) -> pd.Series: ...
    def transform(self, Xf: pd.DataFrame, train_means: pd.Series, feature_order: List[str]) -> pd.DataFrame: ...


class ProbabilityPredictor(Protocol):
    def predict_proba(self, model: BaseEstimator, X: pd.DataFrame) -> np.ndarray: ...


class PredictionsWriter(Protocol):
    def upsert(self, cfg: Dict[str, Any], df_pred: pd.DataFrame) -> int: ...
