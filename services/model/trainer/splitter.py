from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
from .interfaces import TimeSplitResult

class TimeBasedSplitter:
    """Compute an 80/20 time split and summarize date ranges."""

    def __init__(self, pct: float = 0.8):
        if not (0.0 < pct < 1.0):
            raise ValueError("pct must be in (0,1)")
        self.pct = pct

    def split(self, meta: pd.DataFrame) -> TimeSplitResult:
        if "Date" not in meta.columns:
            raise ValueError("meta must contain a 'Date' column for time-based split.")
        dates = pd.to_datetime(meta["Date"])
        if dates.isna().all():
            raise ValueError("All 'Date' values are NaT; cannot time-split.")

        split_date = dates.quantile(self.pct)
        idx_all = np.arange(len(meta))
        # services/model/trainer/splitter.py
        train_idx = idx_all[dates < split_date]  # strictly before
        valid_idx = idx_all[dates >= split_date]  # on/after

        # if still empty, peel one off the end for valid
        if len(valid_idx) == 0 and len(train_idx) > 1:
            train_idx, valid_idx = train_idx[:-1], train_idx[-1:]

        t_min, t_max = dates.iloc[train_idx].min(), dates.iloc[train_idx].max()
        if len(valid_idx) > 0:
            v_min, v_max = dates.iloc[valid_idx].min(), dates.iloc[valid_idx].max()
            valid_range = f"{v_min.date()} → {v_max.date()}"
        else:
            valid_range = "—"

        return TimeSplitResult(
            train_idx=train_idx,
            valid_idx=valid_idx,
            split_date=pd.to_datetime(split_date),
            train_range=f"{t_min.date()} → {t_max.date()}",
            valid_range=valid_range,
        )
