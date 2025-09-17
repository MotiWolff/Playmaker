from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from Playmaker.shared.logging.logger import Logger

log = Logger.get_logger(name="playmaker.model.predictor.predictor")

class ThreeClassPredictor:
    """SRP: produce [H,D,A] probability matrix (0,1,2) with safe class alignment."""
    def predict_proba(self, model: BaseEstimator, X: pd.DataFrame) -> np.ndarray:
        y_proba = model.predict_proba(X)
        classes_ = getattr(model, "classes_", np.array([0, 1, 2]))
        if set(classes_) == {0, 1, 2}:
            log.debug("predictor.direct_alignment", extra={"rows": y_proba.shape[0]})
            return y_proba
        proba_full = np.zeros((y_proba.shape[0], 3))
        for col_idx, cls in enumerate(classes_):
            proba_full[:, int(cls)] = y_proba[:, col_idx]
        log.debug("predictor.reindexed_alignment", extra={"rows": proba_full.shape[0], "classes": classes_.tolist()})
        return proba_full
