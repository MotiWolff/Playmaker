from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from dotenv import load_dotenv
load_dotenv()

DB_URL = os.getenv("POSTGRES_URL")


engine = create_engine(
    DB_URL,
    pool_size=int(os.getenv('POOL_SIZE')), # permanent connections
    max_overflow=int(os.getenv('MAX_OVERFLOW')), # max connections
    pool_pre_ping=True # check for active connection before use
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# return a new session for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
