from __future__ import annotations
from pathlib import Path
from typing import Tuple, Dict, Any
import joblib
from sklearn.base import BaseEstimator
from Playmaker.shared.logging.logger import Logger

log = Logger.get_logger(name="playmaker.model.predictor.artifact_loader")

class JoblibArtifactLoader:
    """SRP: load model artifacts; find latest when path not provided."""
    def __init__(self, models_dir: str = "services/model/models", pattern: str = "*.joblib"):
        self.models_dir = Path(models_dir)
        self.pattern = pattern

    def _latest(self) -> str:
        files = sorted(self.models_dir.glob(self.pattern))
        if not files:
            log.error("artifact_loader.no_artifacts", extra={"dir": str(self.models_dir), "pattern": self.pattern})
            raise FileNotFoundError(f"No model artifacts found in '{self.models_dir}'.")
        latest = str(files[-1])
        log.debug("artifact_loader.latest", extra={"path": latest})
        return latest

    def load(self, artifact_path: str | None = None) -> Tuple[BaseEstimator, Dict[str, Any]]:
        path = artifact_path or self._latest()
        log.info("artifact_loader.loading", extra={"path": path})
        payload = joblib.load(path)
        model: BaseEstimator = payload["model"]
        meta: Dict[str, Any] = payload.get("meta", {})
        if "feature_cols" not in meta:
            log.error("artifact_loader.missing_feature_cols", extra={"keys": list(meta.keys())})
            raise RuntimeError("Artifact missing 'feature_cols' in meta; cannot align input features.")
        log.debug("artifact_loader.loaded", extra={"n_features": len(meta["feature_cols"])})
        return model, meta
