import warnings, pandas as pd

class RollingTeamFeatures:
    def __init__(self, form_window=5, goal_window=10, min_periods_form=1, min_periods_goal=1):
        self.form_window=form_window; self.goal_window=goal_window
        self.min_periods_form=min_periods_form; self.min_periods_goal=min_periods_goal

    def compute(self, long: pd.DataFrame) -> pd.DataFrame:
        def _roll(grp: pd.DataFrame) -> pd.DataFrame:
            grp = grp.sort_values("date")
            grp["rest_days"] = grp["date"].diff().dt.days
            # shift(1) to avoid leakage
            grp["form5"]  = grp["points"].rolling(self.form_window,  min_periods=self.min_periods_form).mean().shift(1)
            grp["gf10"]   = grp["gf"].rolling(self.goal_window,      min_periods=self.min_periods_goal).mean().shift(1)
            grp["ga10"]   = grp["ga"].rolling(self.goal_window,      min_periods=self.min_periods_goal).mean().shift(1)
            grp["shots5"] = grp["shots"].rolling(self.form_window,   min_periods=self.min_periods_form).mean().shift(1)
            grp["corn5"]  = grp["corners"].rolling(self.form_window, min_periods=self.min_periods_form).mean().shift(1)
            grp["yel5"]   = grp["yellows"].rolling(self.form_window, min_periods=self.min_periods_form).mean().shift(1)
            grp["red5"]   = grp["reds"].rolling(self.form_window,    min_periods=self.min_periods_form).mean().shift(1)
            grp["n_prior"]= grp["n_played"].shift(1)
            return grp
        g = long.groupby("team", group_keys=False)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            rolled = g.apply(_roll)
        if "team" not in rolled.columns:
            if isinstance(rolled.index, pd.MultiIndex) and "team" in rolled.index.names:
                rolled = rolled.reset_index(level="team")
            else:
                rolled = rolled.merge(long[["match_key","team"]], on="match_key", how="left")
        return rolled[["match_key","team","is_home","form5","gf10","ga10","shots5","corn5","yel5","red5","n_prior","rest_days"]]
