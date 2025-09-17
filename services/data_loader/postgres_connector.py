import psycopg2
from Playmaker.shared.logging.logger import Logger

class PostgresConnector:
    def __init__(self, postgres_url:str):
        self.postgres_url = postgres_url
        self.conn = None
        self.logger = Logger.get_logger("playmaker.data_loader.db")

    def connect(self):
        try:
            self.conn = psycopg2.connect(self.postgres_url)
            self.logger.info("Connected to Postgres")
            return self.conn
        except Exception as e:
            self.logger.error("Failed to connect to Postgres", extra={"error": str(e)})
            raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            try:
                self.conn.close()
                self.logger.info("Closed Postgres connection")
            except Exception as e:
                self.logger.warning("Error closing Postgres connection", extra={"error": str(e)})
