import numpy as np, pandas as pd

class OddsConverter:
    def convert(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        for col in ("B365H","B365D","B365A"):
            if col not in out.columns: out[col] = np.nan
        out["B365H"] = pd.to_numeric(out["B365H"], errors="coerce")
        out["B365D"] = pd.to_numeric(out["B365D"], errors="coerce")
        out["B365A"] = pd.to_numeric(out["B365A"], errors="coerce")

        H, D, A = out["B365H"].to_numpy(), out["B365D"].to_numpy(), out["B365A"].to_numpy()
        pH_raw = np.where(H>0, 1.0/H, np.nan)
        pD_raw = np.where(D>0, 1.0/D, np.nan)
        pA_raw = np.where(A>0, 1.0/A, np.nan)
        s = pH_raw + pD_raw + pA_raw
        with np.errstate(divide="ignore", invalid="ignore"):
            out["b365_ph"] = np.where(s>0, pH_raw/s, np.nan)
            out["b365_pd"] = np.where(s>0, pD_raw/s, np.nan)
            out["b365_pa"] = np.where(s>0, pA_raw/s, np.nan)
        return out
