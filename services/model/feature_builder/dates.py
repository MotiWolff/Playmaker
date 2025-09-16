import pandas as pd

class DatePreprocessor:
    def ensure_datetime(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        if "Date" not in df.columns:
            raise ValueError("Column 'Date' is missing.")
        parsed = pd.to_datetime(df["Date"], errors="coerce", utc=True)
        before = len(parsed)
        df["Date"] = parsed.dt.tz_convert("UTC").dt.tz_localize(None)
        n_nat = df["Date"].isna().sum()
        if n_nat > 0 and n_nat / before > 0.05:
            raise ValueError(f"Too many unparseable dates: {n_nat}/{before}")
        return df
