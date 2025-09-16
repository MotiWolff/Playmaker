from __future__ import annotations
from pathlib import Path
from typing import Tuple, Dict, Any
import joblib
from sklearn.base import BaseEstimator


class JoblibArtifactLoader:
    """SRP: load model artifacts; find latest when path not provided."""
    def __init__(self, models_dir: str = "services/model/models", pattern: str = "*.joblib"):
        self.models_dir = Path(models_dir)
        self.pattern = pattern

    def _latest(self) -> str:
        files = sorted(self.models_dir.glob(self.pattern))
        if not files:
            raise FileNotFoundError(f"No model artifacts found in '{self.models_dir}'.")
        return str(files[-1])

    def load(self, artifact_path: str | None = None) -> Tuple[BaseEstimator, Dict[str, Any]]:
        path = artifact_path or self._latest()
        payload = joblib.load(path)
        model: BaseEstimator = payload["model"]
        meta: Dict[str, Any] = payload.get("meta", {})
        if "feature_cols" not in meta:
            raise RuntimeError("Artifact missing 'feature_cols' in meta; cannot align input features.")
        return model, meta
