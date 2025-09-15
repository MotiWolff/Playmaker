# services/model/trainer/interfaces.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Dict, Any, Tuple, List
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class TimeSplitResult:
    train_idx: np.ndarray
    valid_idx: np.ndarray
    split_date: pd.Timestamp
    train_range: str
    valid_range: str


class Splitter(Protocol):
    def split(self, meta: pd.DataFrame) -> TimeSplitResult: ...


class MulticlassTrainer(Protocol):
    def fit(self, X_train: pd.DataFrame, y_train: pd.Series) -> None: ...
    def predict(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[int]]: ...


# Use the ArtifactInfo defined in artifact_store.py to avoid duplicate types
from .artifact_store import ArtifactInfo

class ArtifactStore(Protocol):
    def save(
        self,
        model: Any,
        feature_cols: List[str],
        split_info: Dict[str, str],
        random_state: int,
        algo_name: str,
        classes: List[int],
    ) -> ArtifactInfo: ...


class ModelRegistry(Protocol):
    def register(
        self,
        model_name: str,
        trained_on_dset: str,
        metrics: Dict[str, float],
        artifact_uri: str,
    ) -> int: ...
