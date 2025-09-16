from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from mock_database import competitions_db, teams_db, fixtures_db, models_db
from models import Competition, Team, Fixture, Model, Prediction
from typing import Optional, List, Any, Dict
from datetime import datetime, timezone
from pydantic import BaseModel
import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

app = FastAPI(title="Football Predictions API")

# CORS for local development: allow all origins to avoid dev proxy issues
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    competition_name: Optional[str] = None
    home: ApiTeam
    away: ApiTeam
    home_crest_url: Optional[str] = None
    away_crest_url: Optional[str] = None
    prediction: Optional[ApiPredictionLite] = None
    odds: Optional[ApiOdds] = None

class ApiLeague(BaseModel):
    name: str
    country: str
    season: int

class ApiStats(BaseModel):
    total_fixtures: int
    confident_predictions: int
    home_wins: int
    draws: int
    away_wins: int
    high_value_bets: int
    medium_value_bets: int
    average_confidence: float



# --- ENDPOINTS ---

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/competitions")
def get_competitions(q: Optional[str] = None, limit: int = 50, offset: int = 0):
    # Define the 5 allowed leagues
    allowed_leagues = {
        'premier league', 'bundesliga', 'champions league', 'ligue 1', 'serie a',
        'premier', 'bundesl', 'champion', 'ligue', 'serie'
    }
    
    # Force DB usage if configured
    if engine is not None:
        try:
            sql = text("""
                SELECT competition_id, name, COALESCE(emblem_url, '') AS emblem_url
                FROM raw_competitions
                WHERE LOWER(name) LIKE ANY(ARRAY['%premier%', '%bundesliga%', '%uefa champions%', '%ligue%', '%serie%'])
                  AND LOWER(name) NOT LIKE '%european championship%'
                ORDER BY 
                    CASE 
                        WHEN LOWER(name) LIKE '%premier%' THEN 1
                        WHEN LOWER(name) LIKE '%uefa champions%' THEN 2
                        WHEN LOWER(name) LIKE '%bundesliga%' THEN 3
                        WHEN LOWER(name) LIKE '%serie%' THEN 4
                        WHEN LOWER(name) LIKE '%ligue%' THEN 5
                        ELSE 6
                    END,
                    name
                LIMIT :limit OFFSET :offset
            """)
            with engine.connect() as con:
                rows = con.execute(sql, {"limit": limit, "offset": offset}).mappings().all()
            if q:
                rows = [r for r in rows if q.lower() in (r["name"] or "").lower()]
            if rows:  # Only return DB data if we got results
                return [
                    {"competition_id": r["competition_id"], "name": r["name"], "emblem_url": r["emblem_url"] or None}
                    for r in rows
                ]
        except Exception as e:
            print(f"DB competitions query failed: {e}")

    # Mock fallback - filter to only the 5 leagues, exclude European Championship
    result = [c for c in competitions_db if any(league in c.name.lower() for league in allowed_leagues) and 'european championship' not in c.name.lower()]
    if q:
        result = [c for c in result if q.lower() in c.name.lower()]
    return [
        {"competition_id": c.competition_id, "name": c.name, "emblem_url": getattr(c, "emblem_url", None)}
        for c in result[offset: offset+limit]
    ]

# --- Model metrics (from DB model_version table) ---
@app.get("/model_metrics")
def get_model_metrics():
    """Return latest model metrics accuracy/brier/log_loss from model_version table.
    Expected schema: model_version(metrics JSON or TEXT, created_at TIMESTAMP).
    """
    if engine is None:
        # Fallback minimal metrics
        return {"accuracy": None, "brier": None, "log_loss": None}

    # Try to parse metrics from JSON/text column
    sql = text(
        """
        SELECT
            CASE WHEN jsonb_typeof(metrics::jsonb) IS NOT NULL
                 THEN (metrics::jsonb ->> 'accuracy')
                 ELSE NULL END AS accuracy,
            CASE WHEN jsonb_typeof(metrics::jsonb) IS NOT NULL
                 THEN (metrics::jsonb ->> 'brier')
                 ELSE NULL END AS brier,
            CASE WHEN jsonb_typeof(metrics::jsonb) IS NOT NULL
                 THEN (metrics::jsonb ->> 'log_loss')
                 ELSE NULL END AS log_loss
        FROM model_version
        ORDER BY created_at DESC
        LIMIT 1
        """
    )
    with engine.connect() as con:
        row = con.execute(sql).mappings().first()
    if not row:
        return {"accuracy": None, "brier": None, "log_loss": None}
    def to_float(val: Optional[str]):
        try:
            return float(val) if val is not None else None
        except Exception:
            return None
    return {
        "accuracy": to_float(row.get("accuracy")),
        "brier": to_float(row.get("brier")),
        "log_loss": to_float(row.get("log_loss")),
    }

# --- UI convenience endpoints ---
@app.get("/leagues")
def get_leagues():
    # Build a mapping from available competitions (mock) keyed by code when present
    out = {}
    for c in competitions_db:
        code = getattr(c, "code", None) or str(c.competition_id)
        out[code] = {
            "name": c.name,
            "country": getattr(c, "country", ""),
            "season": int(getattr(c, "season", 0) or 0),
        }
    return out

@app.get("/stats", response_model=ApiStats)
def get_stats(league: Optional[str] = None):
    # Simple mock stats derived from in-memory fixtures
    total = len(fixtures_db)
    confident = 0
    home_w = draws = away_w = 0
    max_probs: List[float] = []
    for f in fixtures_db:
        pred = getattr(f, "prediction", None)
        if pred is None:
            continue
        confident += 1
        p_home = getattr(pred, "p_home", 0.0) or 0.0
        p_draw = getattr(pred, "p_draw", 0.0) or 0.0
        p_away = getattr(pred, "p_away", 0.0) or 0.0
        if p_home >= p_draw and p_home >= p_away:
            home_w += 1
        elif p_draw >= p_home and p_draw >= p_away:
            draws += 1
        else:
            away_w += 1
        max_probs.append(max(p_home, p_draw, p_away))

    avg_conf = float(sum(max_probs) / len(max_probs)) if max_probs else 0.0
    return ApiStats(
        total_fixtures=total,
        confident_predictions=confident,
        home_wins=home_w,
        draws=draws,
        away_wins=away_w,
        high_value_bets=0,
        medium_value_bets=0,
        average_confidence=avg_conf,
    )

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
                c.name AS competition_name,
                th.team_id AS home_team_id,
                th.name     AS home_team_name,
                COALESCE(rth.crest_url, th.crest_url, '') AS home_crest_url,
                ta.team_id AS away_team_id,
                ta.name     AS away_team_name,
                COALESCE(rta.crest_url, ta.crest_url, '') AS away_crest_url
            FROM fixture f
            LEFT JOIN competitions c ON c.competition_id = f.competition_id
            JOIN teams th ON th.team_id = f.home_team_id
            JOIN teams ta ON ta.team_id = f.away_team_id
            LEFT JOIN raw_teams rth ON rth.team_id = f.home_team_id
            LEFT JOIN raw_teams rta ON rta.team_id = f.away_team_id
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
            b.competition_name,
            b.home_team_id, b.home_team_name,
            b.home_crest_url,
            b.away_team_id, b.away_team_name,
            b.away_crest_url,
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
        # graceful fallbacks for missing DB data
        comp_name = r.get("competition_name") or (f"Competition #{r['competition_id']}" if r.get("competition_id") else None)
        placeholder_logo = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Association_football.svg/48px-Association_football.svg.png"

        out.append(ApiFixtureWithOdds(
            fixture_id=r["fixture_id"],
            match_utc=r["match_utc"].isoformat() if hasattr(r["match_utc"], "isoformat") else str(r["match_utc"]),
            competition_id=r["competition_id"],
            competition_name=comp_name,
            home=ApiTeam(team_id=r["home_team_id"], name=r["home_team_name"]),
            away=ApiTeam(team_id=r["away_team_id"], name=r["away_team_name"]),
            home_crest_url=r.get("home_crest_url") or placeholder_logo,
            away_crest_url=r.get("away_crest_url") or placeholder_logo,
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
def get_teams(
    competition_id: Optional[List[int]] = Query(None),
    q: Optional[str] = None,
    league: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    # Force DB usage if configured
    if engine is not None:
        try:
            # Pull from raw_teams table
            filters = []
            params: Dict[str, Any] = {"limit": limit, "offset": offset}

            if q:
                filters.append("(LOWER(name) LIKE :q OR LOWER(short_name) LIKE :q)")
                params["q"] = f"%{q.lower()}%"

            if competition_id:
                # Join with fixture table to filter teams by competition
                sql = text(f"""
                    SELECT DISTINCT
                      rt.team_id,
                      rt.name,
                      COALESCE(rt.short_name, rt.name) AS short_name,
                      COALESCE(rt.crest_url, '') AS crest_url,
                      COALESCE(rt.area_name, '') AS country
                    FROM raw_teams rt
                    JOIN (
                        SELECT DISTINCT home_team_id AS team_id FROM fixture WHERE competition_id = ANY(:comp_ids)
                        UNION
                        SELECT DISTINCT away_team_id AS team_id FROM fixture WHERE competition_id = ANY(:comp_ids)
                    ) f ON f.team_id = rt.team_id
                    {f"AND ({' OR '.join([f'(LOWER(rt.name) LIKE :q OR LOWER(rt.short_name) LIKE :q)' for _ in range(len([f for f in filters if 'LIKE' in f]))])})" if [f for f in filters if 'LIKE' in f] else ""}
                    ORDER BY rt.name
                    LIMIT :limit OFFSET :offset
                """)
                params["comp_ids"] = competition_id
            else:
                where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
                sql = text(f"""
                    SELECT
                      team_id,
                      name,
                      COALESCE(short_name, name) AS short_name,
                      COALESCE(crest_url, '') AS crest_url,
                      COALESCE(area_name, '') AS country
                    FROM raw_teams
                    {where_clause}
                    ORDER BY name
                    LIMIT :limit OFFSET :offset
                """)

            with engine.connect() as con:
                rows = con.execute(sql, params).mappings().all()

            if rows:  # Only return DB data if we got results
                return [
                    Team(
                        team_id=r["team_id"],
                        name=r["name"],
                        short_name=r["short_name"],
                        tla=r.get("tla", r["short_name"][0:3].upper() if r["short_name"] else ""),
                        crest_url=r["crest_url"] or "",
                        country=r["country"],
                    )
                    for r in rows
                ]
        except Exception as e:
            print(f"DB teams query failed: {e}")

    # Mock fallback only if no DB or no results
    result = teams_db
    if q:
        result = [t for t in result if q.lower() in t.name.lower()]
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

@app.get("/predict")
def predict(home_team_id: int, away_team_id: int, kickoff: Optional[datetime] = None, model_id: Optional[int] = None):
    # Try to call the actual model service first
    import requests
    
    try:
        # Call the model service (assuming it runs on port 8001 or has an internal endpoint)
        model_url = os.getenv("MODEL_SERVICE_URL", "http://ml-model:8001")
        response = requests.post(
            f"{model_url}/predict",
            json={
                "home_team_id": home_team_id,
                "away_team_id": away_team_id,
                "kickoff": kickoff.isoformat() if kickoff else None
            },
            timeout=10
        )
        
        if response.status_code == 200:
            model_prediction = response.json()
            return {
                "p_home": model_prediction.get("p_home", 0.33),
                "p_draw": model_prediction.get("p_draw", 0.33),
                "p_away": model_prediction.get("p_away", 0.33),
                "home_team_id": home_team_id,
                "away_team_id": away_team_id,
                "model_id": model_prediction.get("model_id", 1),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "source": "model_service"
            }
    except Exception as e:
        print(f"Model service unavailable: {e}")
    
    # Enhanced model using team strength and home advantage (Elo-like) - PRIORITIZED
    try:
        # Get team information for better predictions
        if engine is not None:
            sql = text("""
                SELECT 
                    ht.name as home_name,
                    at.name as away_name
                FROM raw_teams ht, raw_teams at
                WHERE ht.team_id = :home_team_id 
                  AND at.team_id = :away_team_id
            """)
            with engine.connect() as con:
                result = con.execute(sql, {
                    "home_team_id": home_team_id,
                    "away_team_id": away_team_id
                }).mappings().first()
            
            if result:
                team_info = dict(result)
                
                # Enhanced Elo-based model
                def get_elo_rating(name: str) -> float:
                    name_lower = name.lower()
                    
                    # Elite Tier (1750-1800)
                    if any(team in name_lower for team in ['real madrid', 'barcelona']):
                        return 1780
                    if any(team in name_lower for team in ['manchester city', 'liverpool']):
                        return 1770
                    if any(team in name_lower for team in ['bayern', 'arsenal']):
                        return 1760
                    if any(team in name_lower for team in ['psg', 'chelsea']):
                        return 1750
                        
                    # Top Tier (1650-1740)
                    if any(team in name_lower for team in ['dortmund', 'manchester united', 'atletico']):
                        return 1720
                    if any(team in name_lower for team in ['juventus', 'tottenham', 'leipzig']):
                        return 1700
                    if any(team in name_lower for team in ['inter', 'milan', 'leverkusen']):
                        return 1680
                    if any(team in name_lower for team in ['napoli', 'roma', 'lyon']):
                        return 1660
                        
                    # Good Tier (1550-1640)
                    if any(team in name_lower for team in ['newcastle', 'aston villa', 'brighton']):
                        return 1600
                    if any(team in name_lower for team in ['west ham', 'lazio', 'marseille']):
                        return 1580
                    if any(team in name_lower for team in ['monaco', 'fiorentina', 'atalanta']):
                        return 1570
                    if any(team in name_lower for team in ['eintracht', 'union berlin', 'lille']):
                        return 1560
                        
                    # Mid Tier (1450-1540)
                    if any(team in name_lower for team in ['crystal palace', 'wolves', 'everton']):
                        return 1520
                    if any(team in name_lower for team in ['brentford', 'fulham', 'bournemouth']):
                        return 1500
                    if any(team in name_lower for team in ['hoffenheim', 'mainz', 'augsburg']):
                        return 1480
                    if any(team in name_lower for team in ['empoli', 'udinese', 'torino']):
                        return 1460
                        
                    # Lower Tier (1400-1440)
                    return 1420
                
                home_elo = get_elo_rating(team_info['home_name'])
                away_elo = get_elo_rating(team_info['away_name'])
                
                # Home advantage (60 Elo points)
                home_advantage = 60
                effective_home_elo = home_elo + home_advantage
                
                # Calculate expected probability using Elo formula
                elo_diff = effective_home_elo - away_elo
                expected_home = 1.0 / (1.0 + pow(10, (-elo_diff / 400.0)))
                expected_away = 1.0 - expected_home
                
                # Adjust for draws based on skill gap
                skill_gap = abs(elo_diff)
                if skill_gap > 200:  # Large skill gap
                    draw_prob = 0.22
                elif skill_gap > 100:  # Medium skill gap
                    draw_prob = 0.26
                else:  # Close match
                    draw_prob = 0.32
                
                # Redistribute probabilities accounting for draws
                p_home = expected_home * (1 - draw_prob)
                p_away = expected_away * (1 - draw_prob)
                p_draw = draw_prob
                
                # Normalize to ensure sum = 1
                total = p_home + p_draw + p_away
                p_home /= total
                p_draw /= total
                p_away /= total
                
                return {
                    "p_home": round(p_home, 3),
                    "p_draw": round(p_draw, 3),
                    "p_away": round(p_away, 3),
                    "home_team_id": home_team_id,
                    "away_team_id": away_team_id,
                    "model_id": 1,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "source": "enhanced_model"
                }
    except Exception as e:
        print(f"Enhanced model failed: {e}")
    
    # Check database for existing predictions as fallback
    if engine is not None:
        try:
            sql = text("""
                SELECT p.p_home, p.p_draw, p.p_away, p.model_id
                FROM prediction p
                JOIN fixture f ON f.fixture_id = p.fixture_id
                WHERE f.home_team_id = :home_team_id 
                  AND f.away_team_id = :away_team_id
                ORDER BY p.generated_at DESC
                LIMIT 1
            """)
            with engine.connect() as con:
                row = con.execute(sql, {
                    "home_team_id": home_team_id,
                    "away_team_id": away_team_id
                }).mappings().first()
            
            if row:
                return {
                    "p_home": float(row["p_home"]),
                    "p_draw": float(row["p_draw"]), 
                    "p_away": float(row["p_away"]),
                    "home_team_id": home_team_id,
                    "away_team_id": away_team_id,
                    "model_id": row["model_id"],
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "source": "database"
                }
        except Exception as e:
            print(f"Database prediction lookup failed: {e}")
    
    # Final fallback to balanced probabilities
    return {
        "p_home": 0.40,
        "p_draw": 0.30,
        "p_away": 0.30,
        "home_team_id": home_team_id,
        "away_team_id": away_team_id,
        "model_id": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "fallback"
    }

@app.get("/models", response_model=List[Model])
def get_models(limit: int = 10, offset: int = 0):
    return models_db[offset: offset+limit]

@app.get("/models/{model_id}", response_model=Model)
def get_model_detail(model_id: int):
    for m in models_db:
        if m.model_id == model_id:
            return m
    raise HTTPException(status_code=404, detail="Model not found")
