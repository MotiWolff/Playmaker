from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import time
import joblib
from Playmaker.shared.logging.logger import Logger

log = Logger.get_logger(name="playmaker.model.trainer.artifact_store")

@dataclass(frozen=True)
class ArtifactInfo:
    path: str
    metadata: Dict[str, Any]

class LocalArtifactStore:
    """Persist model artifacts + metadata to disk."""
    def __init__(self, base_dir: str = "services/model/models"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        log.debug("artifact_store.init", extra={"base_dir": str(self.base_dir)})

    def save(
        self,
        model: Any,
        feature_cols: List[str],
        split_info: Dict[str, str],
        random_state: int,
        algo_name: str = "RandomForestClassifier",
        classes: List[int] = [0, 1, 2],
    ) -> ArtifactInfo:
        ts = int(time.time())
        artifact_path = str(self.base_dir / f"rf_model_{ts}.joblib")
        metadata = {
            "algo": algo_name,
            "feature_cols": list(feature_cols),
            "classes": classes,
            "split_date": split_info.get("split_date"),
            "train_range": split_info.get("train_range"),
            "valid_range": split_info.get("valid_range"),
            "created_utc": datetime.utcnow().isoformat(),
            "random_state": random_state,
            "params": getattr(model, "get_params", lambda: {})(),
        }
        joblib.dump({"model": model, "meta": metadata}, artifact_path)
        log.info("artifact_store.saved", extra={
            "path": artifact_path,
            "n_features": len(feature_cols),
            "algo": algo_name
        })
        return ArtifactInfo(path=artifact_path, metadata=metadata)
