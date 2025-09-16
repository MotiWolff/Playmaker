import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env automatically
load_dotenv()

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
