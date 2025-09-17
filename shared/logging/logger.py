import logging
from datetime import datetime, timezone
from typing import Optional, Dict

try:
    from elasticsearch import Elasticsearch
except Exception:  # pragma: no cover
    Elasticsearch = None  # type: ignore

from shared.config import SharedConfig


class Logger:
    """
    Configure handlers once on base logger 'playmaker'. Children like
    'playmaker.model.trainer' propagate to it. If a caller passes an
    underscore name (e.g. 'playmaker_data_loader'), we normalize it.
    """
    _configured: bool = False
    config = SharedConfig.load_env()

    @classmethod
    def get_logger(
        cls,
        name: str = "playmaker",
        es_host: Optional[str] = None,
        index: Optional[str] = None,
        level: int = logging.INFO,
    ) -> logging.Logger:
        base_name = "playmaker"

        # one-time base configuration
        if not cls._configured:
            root = logging.getLogger(base_name)
            root.setLevel(level)
            root.propagate = False  # don't bubble to the real root

            # Console handler
            if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
                ch = logging.StreamHandler()
                ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
                root.addHandler(ch)

            # Optional Elasticsearch handler
            es_host = es_host or cls.config.logger_es_host
            index = index or cls.config.logger_index

            if Elasticsearch is not None and es_host and index:
                try:
                    import os
                    os.environ.setdefault("ELASTIC_CLIENT_APIVERSIONING", "true")
                    es_url = es_host if str(es_host).startswith(("http://", "https://")) else f"http://{es_host}"
                    es = Elasticsearch([es_url])
                    compat_headers = {"accept": "application/json", "content-type": "application/json"}

                    # standard LogRecord fields not considered "extra"
                    _std: set[str] = {
                        "name","msg","args","levelname","levelno","pathname","filename","module",
                        "exc_info","exc_text","stack_info","lineno","funcName","created","msecs",
                        "relativeCreated","thread","threadName","processName","process"
                    }

                    class ESHandler(logging.Handler):
                        def emit(self, record: logging.LogRecord) -> None:  # type: ignore[override]
                            try:
                                extras = {k: v for k, v in record.__dict__.items() if k not in _std}
                                doc: Dict[str, object] = {
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                    "level": record.levelname,
                                    "logger": record.name,
                                    "message": record.getMessage(),
                                    **extras,
                                }
                                es.options(headers=compat_headers).index(index=index, document=doc)
                            except Exception:
                                # never crash the app because logging failed
                                pass

                    if not any(h.__class__.__name__ == "ESHandler" for h in root.handlers):
                        root.addHandler(ESHandler())
                except Exception:
                    pass

            cls._configured = True

        # ---- child logger ----
        child_name = (name or base_name).strip()
        child_name = child_name.replace("_", ".")
        if child_name != base_name and not child_name.startswith(f"{base_name}."):
            child_name = f"{base_name}.{child_name}"

        child = logging.getLogger(child_name)
        child.setLevel(level)  # child can override level if needed
        # no handlers added here; it will propagate to 'playmaker'
        return child
