from __future__ import annotations
from typing import Dict, Any
import pandas as pd

from services.model.data_access import upsert_predictions
from Playmaker.shared.logging.logger import Logger

log = Logger.get_logger(name="playmaker.model.predictor.writer")

class DBPredictionsWriter:
    """SRP: write/upsert predictions into DB."""
    def upsert(self, cfg: Dict[str, Any], df_pred: pd.DataFrame) -> int:
        if df_pred is None or df_pred.empty:
            log.info("writer.no_rows_to_upsert")
            return 0

        # lightweight observability
        sample_keys = {}
        for k in ("model_id", "fixture_id"):
            if k in df_pred.columns:
                sample_keys[k] = df_pred[k].iloc[0]

        log.debug("writer.upsert_start", extra={
            "rows": int(len(df_pred)),
            "cols": list(df_pred.columns),
            "sample_keys": sample_keys
        })

        try:
            written = upsert_predictions(cfg, df_pred)
            log.info("writer.upsert_success", extra={"rows_written": int(written)})
            return int(written)
        except Exception as e:
            log.exception("writer.upsert_failed", extra={"error": str(e)})
            raise
