import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SharedConfig:
    logger_es_host: str
    logger_index: str

    @classmethod
    def load_env(cls) -> "SharedConfig":
        # Prefer ELASTIC_HOST, but gracefully fall back to compose variables
        es_host = (
            os.getenv("ELASTIC_HOST")
            or os.getenv("ELASTICSEARCH_HOST")
            or os.getenv("ELASTIC_URL")
            or "http://localhost:9200"
        )

        return cls(
            logger_es_host=es_host,
            logger_index=os.getenv("ELASTIC_LOG_INDEX", "playmaker-logs"),
        )


