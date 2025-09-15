import logging
from datetime import datetime, timezone
from typing import Optional

try:
    from elasticsearch import Elasticsearch
except Exception:  # pragma: no cover
    Elasticsearch = None  # type: ignore

from shared.config import SharedConfig


class Logger:
    _logger: Optional[logging.Logger] = None

    config = SharedConfig.load_env()

    @classmethod
    def get_logger(
        cls,
        name: str = "playmaker_logger",
        es_host: str = config.logger_es_host,
        index: str = config.logger_index,
        level: int = logging.INFO,
    ) -> logging.Logger:
        if cls._logger:
            return cls._logger

        logger = logging.getLogger(name)
        logger.setLevel(level)

        if not logger.handlers:
            # Initialize Elasticsearch connection
            try:
                es_url = es_host
                if not str(es_host).startswith(("http://", "https://")):
                    es_url = f"http://{es_host}"

                if Elasticsearch is not None:
                    # Ensure compatibility headers for clusters expecting v7/v8
                    import os
                    os.environ.setdefault("ELASTIC_CLIENT_APIVERSIONING", "true")
                    # Use ES 8-compatible media-type headers for clusters < v9
                    es = Elasticsearch([es_url])
                    compat_headers = {
                        # Fallback to plain JSON to avoid versioned media-type negotiation issues
                        "accept": "application/json",
                        "content-type": "application/json",
                    }

                    class ESHandler(logging.Handler):
                        def emit(self, record: logging.LogRecord) -> None:  # type: ignore[override]
                            try:
                                es.options(headers=compat_headers).index(
                                    index=index,
                                    document={
                                        "timestamp": datetime.now(timezone.utc).isoformat(),
                                        "level": record.levelname,
                                        "logger": record.name,
                                        "message": record.getMessage(),
                                    },
                                )
                            except Exception as e:  # noqa: BLE001
                                print(f"ES log failed: {e}")

                    logger.addHandler(ESHandler())
            except Exception as e:  # noqa: BLE001
                print(f"Failed to initialize Elasticsearch handler: {e}")

            # Console handler for development
            logger.addHandler(logging.StreamHandler())

        cls._logger = logger
        return logger


