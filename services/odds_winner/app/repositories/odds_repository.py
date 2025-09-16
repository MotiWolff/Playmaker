from app.db import SessionLocal
from app.models import SoccerOdds

class OddsRepository:
    def __init__(self):
        self.db = SessionLocal()

    def upsert(self, record: dict):
        obj = self.db.query(SoccerOdds).filter_by(
            home_team=record["home_team"],
            away_team=record["away_team"],
            date=record["date"]
        ).first()

        if obj:
            obj.home_odds = record["home_odds"]
            obj.draw_odds = record["draw_odds"]
            obj.away_odds = record["away_odds"]
            obj.league = record["league"]
        else:
            obj = SoccerOdds(**record)
            self.db.add(obj)

        self.db.commit()