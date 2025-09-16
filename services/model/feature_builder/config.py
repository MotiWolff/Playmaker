from dataclasses import dataclass

@dataclass
class FeatureBuilderConfig:
    min_history_games: int = 3
    form_window: int = 5
    goal_window: int = 10