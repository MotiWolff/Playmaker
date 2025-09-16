from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, List
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier


@dataclass(frozen=True)
class RFConfig:
    n_estimators: int = 400
    max_depth: int | None = 6
    min_samples_leaf: int = 3
    class_weight: str | None = "balanced"
    random_state: int = 42
    n_jobs: int = -1


class RandomForestMulticlassTrainer:
    """Own RF construction, training and inference."""

    def __init__(self, cfg: RFConfig):
        self.cfg = cfg
        self._clf: RandomForestClassifier | None = None

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series) -> None:
        self._clf = RandomForestClassifier(
            n_estimators=self.cfg.n_estimators,
            max_depth=self.cfg.max_depth,
            min_samples_leaf=self.cfg.min_samples_leaf,
            class_weight=self.cfg.class_weight,
            random_state=self.cfg.random_state,
            n_jobs=self.cfg.n_jobs,
        )
        self._clf.fit(X_train, y_train)

    def predict(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[int]]:
        if self._clf is None:
            raise RuntimeError("Model not trained. Call fit() first.")
        y_pred = self._clf.predict(X)
        y_proba = self._clf.predict_proba(X)
        classes = list(getattr(self._clf, "classes_", [0, 1, 2]))
        return y_pred, y_proba, classes

    @property
    def model(self) -> RandomForestClassifier:
        if self._clf is None:
            raise RuntimeError("Model not trained. Call fit() first.")
        return self._clf
