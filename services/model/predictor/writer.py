# services/model/predictor/writer.py
from __future__ import annotations
from typing import Dict, Any
import pandas as pd
# ❌ from services.model.data_access.data_access import upsert_predictions
# ✅ use the facade:
from services.model.data_access import upsert_predictions

class DBPredictionsWriter:
    """SRP: write/upsert predictions into DB."""
    def upsert(self, cfg: Dict[str, Any], df_pred: pd.DataFrame) -> int:
        return upsert_predictions(cfg, df_pred)
