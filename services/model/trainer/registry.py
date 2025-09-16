from __future__ import annotations
from typing import Dict, Any
from services.model.data_access import write_model_version


class DBModelRegistry:
    """Register a trained model in the DB-based registry."""

    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg

    def register(self, model_name: str, trained_on_dset: str, metrics: Dict[str, float], artifact_uri: str) -> int:
        return write_model_version(
            cfg=self.cfg,
            model_name=model_name,
            trained_on_dset=trained_on_dset,
            metrics=metrics,
            artifact_uri=artifact_uri,
        )
