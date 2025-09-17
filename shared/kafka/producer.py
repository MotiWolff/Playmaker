

import json
from typing import Any, Dict, Optional

from kafka import KafkaProducer
from Playmaker.shared.logging.logger import Logger

from .config import KafkaConfig

class JsonKafkaProducer:
    """Send JSON-serializable payloads.

    Usage:
        producer = JsonKafkaProducer()
        producer.send_json("fixtures.soccer", {"fixture_id": 1})
    """

    def __init__(self, config: Optional[KafkaConfig] = None, **overrides: Any) -> None:
        self.config = config or KafkaConfig.from_env()
        self.log = Logger.get_logger(name="playmaker.kafka.producer")

        producer_kwargs: Dict[str, Any] = {
            **self.config.common_security_kwargs(),
            "value_serializer": lambda v: json.dumps(v).encode("utf-8"),
            "key_serializer": lambda v: json.dumps(v).encode("utf-8") if v is not None else None,
            "acks": overrides.pop("acks", "all"),
            "retries": overrides.pop("retries", 5),
            "linger_ms": overrides.pop("linger_ms", 10),
        }
        producer_kwargs.update(overrides)
        self._producer = KafkaProducer(**producer_kwargs)
        self.log.info("kafka.producer.init")

    def send_json(
        self,
        topic: str,
        value: Any,
        key: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> None:
        kafka_headers = []
        if headers:
            kafka_headers = [(k, str(v).encode("utf-8")) for k, v in headers.items()]
        fut = self._producer.send(topic, key=key, value=value, headers=kafka_headers)

        # attach callbacks for observability (non-blocking)
        def _on_success(record_md):
            try:
                self.log.debug("kafka.producer.acked", extra={
                    "topic": record_md.topic, "partition": record_md.partition, "offset": record_md.offset
                })
            except Exception:
                pass

        def _on_err(excp):
            self.log.exception("kafka.producer.send_failed", extra={"topic": topic, "error": str(excp)})

        fut.add_callback(_on_success)
        fut.add_errback(_on_err)

    def flush(self) -> None:
        try:
            self._producer.flush()
            self.log.info("kafka.producer.flushed")
        except Exception:
            pass

    def close(self) -> None:
        try:
            self._producer.flush()
            self._producer.close()
            self.log.info("kafka.producer.closed")
        except Exception:
            pass
