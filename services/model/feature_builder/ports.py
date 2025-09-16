from typing import Protocol
import pandas as pd

class EloRatingsPort(Protocol):
    def compute_elo_pre_post(self, df_matches: pd.DataFrame) -> pd.DataFrame: ...