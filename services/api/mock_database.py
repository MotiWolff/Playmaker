from .models import *



# --- MOCK DATABASE ---

competitions_db = [
    Competition(competition_id=1, name="Premier League", code="PL",
                emblem_url="https://example.com/pl.png", country="England", season="2025", current_matchday=5)
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
