from __future__ import annotations
from typing import Dict, List
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, log_loss
from Playmaker.shared.logging.logger import Logger

log = Logger.get_logger(name="playmaker.model.trainer.metrics")

def brier_multiclass(y_true: np.ndarray, proba: np.ndarray, n_classes: int = 3) -> float:
    y_true = np.asarray(y_true).astype(int)
    Y = np.eye(n_classes)[y_true]
    return float(np.mean(np.sum((proba - Y) ** 2, axis=1)))

def ensure_three_class_proba(y_proba: np.ndarray, classes: List[int]) -> np.ndarray:
    # Fast path when already [0,1,2]
    if set(classes) == {0, 1, 2}:
        return y_proba
    out = np.zeros((y_proba.shape[0], 3))
    for col_idx, cls in enumerate(classes):
        out[:, int(cls)] = y_proba[:, col_idx]
    # Log only meta, not arrays
    try:
        log.debug("metrics.reindexed_proba", extra={"classes": list(map(int, classes)), "rows": int(out.shape[0])})
    except Exception:
        pass
    return out

def evaluate_multiclass(y_true: pd.Series, y_pred: np.ndarray, y_proba: np.ndarray) -> Dict[str, float]:
    acc = float(accuracy_score(y_true, y_pred))
    try:
        ll = float(log_loss(y_true, y_proba, labels=[0, 1, 2]))
    except Exception:
        ll = float("nan")
    brier = brier_multiclass(y_true.to_numpy(), y_proba, n_classes=3)
    metrics = {"accuracy": acc, "log_loss": ll, "brier": brier}
    # Safe, compact metrics log
    try:
        log.info("metrics.eval", extra=metrics | {"n": int(len(y_true))})
    except Exception:
        pass
    return metrics
