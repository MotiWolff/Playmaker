# data_cleaner/db/postgres.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from dotenv import load_dotenv
load_dotenv()

# 🔽 add: shared logger
from Playmaker.shared.logging.logger import Logger
logger = Logger.get_logger(name="playmaker.data_cleaner.db")

DB_URL = os.getenv("POSTGRES_URL")

# (optional visibility) log what we’re about to use — no secrets
logger.info(
    "Creating SQLAlchemy engine",
    extra={"pool_size": os.getenv("POOL_SIZE"), "max_overflow": os.getenv("MAX_OVERFLOW")}
)

engine = create_engine(
    DB_URL,
    pool_size=int(os.getenv('POOL_SIZE')),  # permanent connections
    max_overflow=int(os.getenv('MAX_OVERFLOW')),  # max connections
    pool_pre_ping=True  # check for active connection before use
)

logger.info("Engine created")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# return a new session for each request
def get_db():
    db = SessionLocal()
    logger.debug("DB session opened")
    try:
        yield db
    finally:
        try:
            db.close()
            logger.debug("DB session closed")
        except Exception:
            # preserve original behavior (re-raise), just log it too
            logger.warning("Error closing DB session", exc_info=True)
            raise
