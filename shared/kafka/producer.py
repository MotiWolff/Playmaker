import json
from typing import Any, Dict, Optional

from kafka import KafkaProducer

from .config import KafkaConfig


class JsonKafkaProducer:
    """Kafka producer that sends JSON-serializable payloads.

    Usage:
        producer = JsonKafkaProducer()
        producer.send_json("fixtures.soccer", {"fixture_id": 1})
    """

    def __init__(self, config: Optional[KafkaConfig] = None, **overrides: Any) -> None:
        self.config = config or KafkaConfig.from_env()
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

    def send_json(self, topic: str, value: Any, key: Optional[Any] = None, headers: Optional[Dict[str, str]] = None) -> None:
        kafka_headers = []
        if headers:
            kafka_headers = [(k, str(v).encode("utf-8")) for k, v in headers.items()]
        self._producer.send(topic, key=key, value=value, headers=kafka_headers)

    def flush(self) -> None:
        self._producer.flush()

    def close(self) -> None:
        self._producer.flush()
        self._producer.close()


