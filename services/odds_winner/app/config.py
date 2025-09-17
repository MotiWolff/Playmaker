
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from Playmaker.shared.logging.logger import Logger

load_dotenv()
log = Logger.get_logger(name="playmaker.odds_winner.config")

class Settings(BaseSettings):
    # Database
    DB_DSN: str | None = os.getenv("DB_DSN")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "winner")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "db")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")

    # Selenium / Scraper
    SELENIUM_URL: str = os.getenv("SELENIUM_URL", "http://localhost:4444/wd/hub")
    SCRAPE_URL: str = os.getenv("SCRAPE_URL", "https://www.winner.co.il/משחקים/ווינר-ליין/כדורגל")
    SCRAPE_DATE_FORMAT: str = os.getenv("SCRAPE_DATE_FORMAT", "%d.%m.%Y")

    # Misc
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def DATABASE_URL(self) -> str:
        if self.DB_DSN:
            return self.DB_DSN
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

settings = Settings()

# Log once (mask pwd)
try:
    masked = settings.DATABASE_URL.replace(settings.POSTGRES_PASSWORD, "****") if settings.POSTGRES_PASSWORD else settings.DATABASE_URL
    log.debug("config.database_url", extra={"url": masked})
except Exception:
    pass
log.debug("config.scraper", extra={"selenium_url": settings.SELENIUM_URL, "scrape_url": settings.SCRAPE_URL})

