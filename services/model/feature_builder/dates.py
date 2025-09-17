
import pandas as pd
from Playmaker.shared.logging.logger import Logger
log = Logger.get_logger(name="playmaker.model.features.dates")

class DatePreprocessor:
    def ensure_datetime(self, df: pd.DataFrame) -> pd.DataFrame:
        if "Date" not in df.columns:
            log.error("dates.missing_column_date")
            raise ValueError("Column 'Date' is missing.")

        df = df.copy()
        parsed = pd.to_datetime(df["Date"], errors="coerce", utc=True)
        before = len(parsed)
        n_nat = parsed.isna().sum()

        # Normalize to naive UTC
        df["Date"] = parsed.dt.tz_convert("UTC").dt.tz_localize(None)

        if before:
            frac_bad = n_nat / before
        else:
            frac_bad = 0.0

        if n_nat > 0:
            log.warning("dates.unparseable_dates", extra={"n_nat": int(n_nat), "total": int(before), "frac": float(frac_bad)})

        if frac_bad > 0.05:
            log.error("dates.too_many_unparseable", extra={"n_nat": int(n_nat), "total": int(before), "threshold": 0.05})
            raise ValueError(f"Too many unparseable dates: {n_nat}/{before}")

        log.debug("dates.parsed", extra={"rows": int(before)})
        return df
