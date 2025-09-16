"""
Database connection module for PostgreSQL using SQLAlchemy.

This module:
    - Loads the database URL and pool settings from environment variables.
    - Creates a SQLAlchemy engine with connection pooling.
    - Provides a `SessionLocal` factory for database sessions.
    - Defines a `get_db` dependency for FastAPI to handle DB sessions safely.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from dotenv import load_dotenv
load_dotenv()

DB_URL = os.getenv("POSTGRES_URL")
if not DB_URL:
    raise ValueError("POSTGRES_URL environment variable is not set. Check your .env file or environment settings.")


engine = create_engine(
    DB_URL,
    pool_size=int(os.getenv('POOL_SIZE', 5)), # permanent connections
    max_overflow=int(os.getenv('MAX_OVERFLOW', 10)), # max connections
    pool_pre_ping=True # check for active connection before use
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# return a new session for each request
def get_db():
    """
    Dependency that provides a database session for each request.

    Yields:
        Session: A SQLAlchemy session bound to the configured engine.

    Ensures the session is closed after the request is completed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
