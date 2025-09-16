from fastapi import FastAPI, HTTPException, Query
from mock_database import *
from models import *

app = FastAPI(title="Football Predictions API")



# --- ENDPOINTS ---

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/competitions", response_model=List[Competition])
def get_competitions(q: Optional[str] = None, limit: int = 10, offset: int = 0):
    result = competitions_db
    if q:
        result = [c for c in result if q.lower() in c.name.lower()]
    return result[offset: offset+limit]

@app.get("/competitions/{competition_id}", response_model=Competition)
def get_competition_detail(competition_id: int):
    for c in competitions_db:
        if c.competition_id == competition_id:
            return c
    raise HTTPException(status_code=404, detail="Competition not found")

@app.get("/teams", response_model=List[Team])
def get_teams(competition_id: Optional[List[int]] = Query(None), q: Optional[str] = None, limit: int = 10, offset: int = 0):
    result = teams_db
    if q:
        result = [t for t in result if q.lower() in t.name.lower()]
    # For simplicity, competition_id filter is ignored in mock
    return result[offset: offset+limit]

@app.get("/teams/{team_id}", response_model=Team)
def get_team_detail(team_id: int):
    for t in teams_db:
        if t.team_id == team_id:
            return t
    raise HTTPException(status_code=404, detail="Team not found")

@app.get("/fixtures/upcoming", response_model=List[Fixture])
def get_upcoming_fixtures(competition_id: Optional[List[int]] = Query(None),
                          from_date: Optional[datetime] = None,
                          to_date: Optional[datetime] = None,
                          limit: int = 10, offset: int = 0):
    result = fixtures_db
    if from_date:
        result = [f for f in result if f.match_utc >= from_date]
    if to_date:
        result = [f for f in result if f.match_utc <= to_date]
    # For simplicity, competition_id filter is ignored in mock
    return result[offset: offset+limit]

@app.get("/predictions", response_model=List[Fixture])
def get_predictions(fixture_id: Optional[int] = None, competition_id: Optional[int] = None,
                    limit: int = 10, offset: int = 0):
    result = [f for f in fixtures_db if f.prediction is not None]
    if fixture_id:
        result = [f for f in result if f.fixture_id == fixture_id]
    # competition_id filter ignored in mock
    return result[offset: offset+limit]

@app.get("/predict", response_model=Prediction)
def predict(home_team_id: int, away_team_id: int, kickoff: Optional[datetime] = None, model_id: Optional[int] = None):
    # Simple dummy prediction
    model = models_db[-1] if not model_id else next((m for m in models_db if m.model_id == model_id), None)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    now = datetime.now(timezone.utc)
    prediction = Prediction(
        model_id=model.model_id,
        p_home=0.45,
        p_draw=0.30,
        p_away=0.25,
        expected_home_goals=1.8,
        expected_away_goals=1.2,
        feature_snapshot={"home_team_id": home_team_id, "away_team_id": away_team_id},
        generated_at=now
    )
    return prediction

@app.get("/models", response_model=List[Model])
def get_models(limit: int = 10, offset: int = 0):
    return models_db[offset: offset+limit]

@app.get("/models/{model_id}", response_model=Model)
def get_model_detail(model_id: int):
    for m in models_db:
        if m.model_id == model_id:
            return m
    raise HTTPException(status_code=404, detail="Model not found")
