from app.db import init_db
from app.scraper import WinnerScraper
from app.repositories.odds_repository import OddsRepository
from app.config import settings
from Playmaker.shared.logging.logger import Logger

log = Logger.get_logger(name="playmaker.odds_winner.main")

def main():
    log.info("main.start")

    # Initialize DB tables
    init_db()

    # Scrape
    scraper = WinnerScraper()
    df = scraper.scrape()
    log.info("main.scrape_done", extra={"rows": int(len(df))})

    # Store in DB
    repo = OddsRepository()
    written = 0
    for _, row in df.iterrows():
        try:
            repo.upsert(row.to_dict())
            written += 1
        except Exception as e:
            log.exception("main.upsert_row_failed", extra={"row": row.to_dict(), "error": str(e)})

    log.info("main.saved", extra={"rows_written": written})

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.exception("main.failed", extra={"error": str(e)})
        raise
