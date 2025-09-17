from services.api.models import *



# --- MOCK DATABASE ---

competitions_db = [
    Competition(competition_id=2021, name="Premier League", code="PL",
                emblem_url="https://crests.football-data.org/PL.svg", country="England", season="2025", current_matchday=5),
    Competition(competition_id=2002, name="Bundesliga", code="BL1",
                emblem_url="https://crests.football-data.org/BL1.svg", country="Germany", season="2025", current_matchday=4),
    Competition(competition_id=2019, name="Serie A", code="SA",
                emblem_url="https://crests.football-data.org/SA.svg", country="Italy", season="2025", current_matchday=3),
    Competition(competition_id=2015, name="Ligue 1", code="FL1",
                emblem_url="https://crests.football-data.org/FL1.svg", country="France", season="2025", current_matchday=3),
    Competition(competition_id=2001, name="UEFA Champions League", code="CL",
                emblem_url="https://crests.football-data.org/CL.svg", country="Europe", season="2025", current_matchday=1),
]

teams_db = [
    Team(team_id=10, name="Manchester United", short_name="Man Utd", tla="MUN",
         crest_url="https://example.com/manu.png", country="England"),
    Team(team_id=20, name="Liverpool", short_name="Liverpool", tla="LIV",
         crest_url="https://example.com/liv.png", country="England")
]

models_db = [
    Model(model_id=5, model_name="ELO v2", trained_on_dset="2023_dataset",
          metrics={"accuracy": 0.67}, artifact_uri="s3://models/elo_v2", created_at=datetime.now(timezone.utc))
]

predictions_db = []

fixtures_db = [
    Fixture(
        fixture_id=123,
        match_utc=datetime(2025, 9, 20, 15, 0, tzinfo=timezone.utc),
        status="scheduled",
        competition=competitions_db[0],
        home=teams_db[0],
        away=teams_db[1],
        prediction=None
    )
]
