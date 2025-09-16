from fastapi import FastAPI, HTTPException, Query
from .mock_database import competitions_db, teams_db, fixtures_db, models_db
from .models import Competition, Team, Fixture, Model, Prediction
from typing import Optional, List, Any, Dict
from datetime import datetime, timezone
from pydantic import BaseModel
import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

app = FastAPI(title="Football Predictions API")

# --- DB engine for real queries (predictions + odds) ---
DB_DSN = os.getenv("DB_DSN") or os.getenv("DATABASE_URL")
engine: Optional[Engine] = None
if DB_DSN:
    engine = create_engine(DB_DSN, pool_pre_ping=True, future=True)

# --- Lightweight response models for the DB-backed endpoint ---
class ApiTeam(BaseModel):
    team_id: int
    name: str

class ApiOdds(BaseModel):
    home_odds: Optional[float] = None
    draw_odds: Optional[float] = None
    away_odds: Optional[float] = None

class ApiPredictionLite(BaseModel):
    p_home: float
    p_draw: float
    p_away: float

class ApiFixtureWithOdds(BaseModel):
    fixture_id: int
    match_utc: str
    competition_id: Optional[int] = None
    home: ApiTeam
    away: ApiTeam
    prediction: Optional[ApiPredictionLite] = None
    odds: Optional[ApiOdds] = None



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

# --- DB-backed endpoint to join predictions with latest scraped odds ---
@app.get("/fixtures/upcoming_with_odds", response_model=List[ApiFixtureWithOdds])
def upcoming_with_odds(
    competition_id: Optional[List[int]] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    if engine is None:
        raise HTTPException(status_code=503, detail="DB not configured (set DB_DSN or DATABASE_URL)")

    comp_filter = ""
    params: Dict[str, Any] = {"limit": limit, "offset": offset}
    if competition_id:
        comp_filter = "AND f.competition_id = ANY(:comp_ids)"
        params["comp_ids"] = competition_id

    sql = text(f"""
        WITH base AS (
            SELECT
                f.fixture_id,
                f.match_utc,
                f.competition_id,
                th.team_id AS home_team_id,
                th.name     AS home_team_name,
                ta.team_id AS away_team_id,
                ta.name     AS away_team_name
            FROM fixture f
            JOIN teams th ON th.team_id = f.home_team_id
            JOIN teams ta ON ta.team_id = f.away_team_id
            WHERE f.status = 'SCHEDULED'
            {comp_filter}
            ORDER BY f.match_utc
            LIMIT :limit OFFSET :offset
        ),
        pred AS (
            SELECT p.fixture_id, p.p_home, p.p_draw, p.p_away,
                   ROW_NUMBER() OVER (PARTITION BY p.fixture_id ORDER BY p.generated_at DESC) AS rn
            FROM prediction p
        ),
        odds AS (
            SELECT fixture_id,
                   MAX(CASE WHEN sel = 'H' THEN price END) AS home_odds,
                   MAX(CASE WHEN sel = 'D' THEN price END) AS draw_odds,
                   MAX(CASE WHEN sel = 'A' THEN price END) AS away_odds
            FROM (
                SELECT o.fixture_id, o.market, o.sel, o.price, o.captured_at,
                       ROW_NUMBER() OVER (
                           PARTITION BY o.fixture_id, o.market, o.sel
                           ORDER BY o.captured_at DESC
                       ) AS rn
                FROM odds_offer o
                WHERE o.market = '1X2' AND o.fixture_id IS NOT NULL
            ) t
            WHERE rn = 1
            GROUP BY fixture_id
        )
        SELECT
            b.fixture_id,
            b.match_utc,
            b.competition_id,
            b.home_team_id, b.home_team_name,
            b.away_team_id, b.away_team_name,
            pr.p_home, pr.p_draw, pr.p_away,
            COALESCE(oo.home_odds, so.home_odds) AS home_odds,
            COALESCE(oo.draw_odds, so.draw_odds) AS draw_odds,
            COALESCE(oo.away_odds, so.away_odds) AS away_odds
        FROM base b
        LEFT JOIN pred pr ON pr.fixture_id = b.fixture_id AND pr.rn = 1
        LEFT JOIN odds oo ON oo.fixture_id = b.fixture_id
        LEFT JOIN LATERAL (
          SELECT s.home_odds, s.draw_odds, s.away_odds
          FROM soccer_odds s
          WHERE s.home_team = b.home_team_name
            AND s.away_team = b.away_team_name
            AND s.date = to_char(b.match_utc::date, 'DD.MM.YYYY')
          ORDER BY s.date DESC
          LIMIT 1
        ) so ON TRUE;
    """)

    with engine.connect() as con:
        rows = con.execute(sql, params).mappings().all()

    out: List[ApiFixtureWithOdds] = []
    for r in rows:
        out.append(ApiFixtureWithOdds(
            fixture_id=r["fixture_id"],
            match_utc=r["match_utc"].isoformat() if hasattr(r["match_utc"], "isoformat") else str(r["match_utc"]),
            competition_id=r["competition_id"],
            home=ApiTeam(team_id=r["home_team_id"], name=r["home_team_name"]),
            away=ApiTeam(team_id=r["away_team_id"], name=r["away_team_name"]),
            prediction=(ApiPredictionLite(p_home=r["p_home"], p_draw=r["p_draw"], p_away=r["p_away"]) if r["p_home"] is not None else None),
            odds=(ApiOdds(home_odds=r["home_odds"], draw_odds=r["draw_odds"], away_odds=r["away_odds"]) if any(v is not None for v in (r["home_odds"], r["draw_odds"], r["away_odds"])) else None),
        ))
    return out

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
