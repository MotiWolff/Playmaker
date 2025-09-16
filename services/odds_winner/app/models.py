from sqlalchemy import Column, String, Float
from app.db import Base

class SoccerOdds(Base):
    __tablename__ = "soccer_odds"

    home_team = Column(String, primary_key=True)
    away_team = Column(String, primary_key=True)
    date = Column(String, primary_key=True)

    home_odds = Column(Float)
    draw_odds = Column(Float)
    away_odds = Column(Float)
    league = Column(String)