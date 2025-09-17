from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
from .interfaces import TimeSplitResult
from Playmaker.shared.logging.logger import Logger

log = Logger.get_logger(name="playmaker.model.trainer.splitter")

class TimeBasedSplitter:
    """Compute an 80/20 time split and summarize date ranges."""
    def __init__(self, pct: float = 0.8):
        if not (0.0 < pct < 1.0):
            log.error("splitter.bad_pct", extra={"pct": pct})
            raise ValueError("pct must be in (0,1)")
        self.pct = pct

    def split(self, meta: pd.DataFrame) -> TimeSplitResult:
        if "Date" not in meta.columns:
            log.error("splitter.missing_date_col")
            raise ValueError("meta must contain a 'Date' column for time-based split.")
        dates = pd.to_datetime(meta["Date"])
        if dates.isna().all():
            log.error("splitter.all_nat_dates")
            raise ValueError("All 'Date' values are NaT; cannot time-split.")

        split_date = dates.quantile(self.pct)
        idx_all = np.arange(len(meta))
        train_idx = idx_all[dates < split_date]
        valid_idx = idx_all[dates >= split_date]

        if len(valid_idx) == 0 and len(train_idx) > 1:
            train_idx, valid_idx = train_idx[:-1], train_idx[-1:]

        t_min, t_max = dates.iloc[train_idx].min(), dates.iloc[train_idx].max()
        if len(valid_idx) > 0:
            v_min, v_max = dates.iloc[valid_idx].min(), dates.iloc[valid_idx].max()
            valid_range = f"{v_min.date()} → {v_max.date()}"
        else:
            valid_range = "—"

        log.info("splitter.split_done", extra={
            "pct": float(self.pct),
            "split_date": str(pd.to_datetime(split_date)),
            "n_train": int(len(train_idx)),
            "n_valid": int(len(valid_idx)),
            "train_range": f"{t_min.date()} → {t_max.date()}",
            "valid_range": valid_range
        })

        return TimeSplitResult(
            train_idx=train_idx,
            valid_idx=valid_idx,
            split_date=pd.to_datetime(split_date),
            train_range=f"{t_min.date()} → {t_max.date()}",
            valid_range=valid_range,
        )
