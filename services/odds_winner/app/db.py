from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
from Playmaker.shared.logging.logger import Logger

log = Logger.get_logger(name="playmaker.odds_winner.db")

engine = create_engine(settings.DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Create all tables."""
    try:
        from app import models  # noqa: F401
        Base.metadata.create_all(bind=engine)
        log.info("db.init_ok")
    except Exception as e:
        log.exception("db.init_failed", extra={"error": str(e)})
        raise
