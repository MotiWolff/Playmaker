import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SharedConfig:
    logger_es_host: str
    logger_index: str

    @classmethod
    def load_env(cls) -> "SharedConfig":
        return cls(
            logger_es_host=os.getenv("ELASTIC_HOST", "http://localhost:9200"),
            logger_index=os.getenv("ELASTIC_LOG_INDEX", "playmaker-logs"),
        )


