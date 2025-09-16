from app.db import init_db
from app.scraper import WinnerScraper
from app.repositories.odds_repository import OddsRepository
from app.config import settings
import logging

def main():
    logging.basicConfig(level=settings.LOG_LEVEL)
    logging.info(f"Connecting to DB: {settings.DATABASE_URL}")

    # Initialize DB tables
    init_db()

    # Scrape
    scraper = WinnerScraper()
    df = scraper.scrape()

    # Store in DB
    repo = OddsRepository()
    for _, row in df.iterrows():
        repo.upsert(row.to_dict())

    logging.info("✅ Data saved to PostgreSQL")

if __name__ == "__main__":
    main()