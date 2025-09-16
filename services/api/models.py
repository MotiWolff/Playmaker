from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timezone


# --- MODELS ---

class Competition(BaseModel):
    competition_id: int
    name: str
    code: str
    emblem_url: str
    country: str
    season: str
    current_matchday: int

class Team(BaseModel):
    team_id: int
    name: str
    short_name: str
    tla: str
    crest_url: str
    country: str
    recent_form: Optional[List[str]] = None
    next_fixture: Optional[Dict] = None

class Prediction(BaseModel):
    model_id: int
    p_home: float
    p_draw: float
    p_away: float
    expected_home_goals: float
    expected_away_goals: float
    feature_snapshot: Optional[Dict] = None
    generated_at: datetime

class Fixture(BaseModel):
    fixture_id: int
    match_utc: datetime
    status: str
    competition: Competition
    home: Team
    away: Team
    prediction: Optional[Prediction] = None

class Model(BaseModel):
    model_id: int
    model_name: str
    trained_on_dset: str
    metrics: Dict
    artifact_uri: str
    created_at: datetime
