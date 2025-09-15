import json
import logging
from typing import Any, Callable, Iterable, List, Optional

from kafka import KafkaConsumer

from .config import KafkaConfig


logger = logging.getLogger(__name__)


class JsonKafkaConsumer:
    """Kafka consumer to poll JSON messages and hand them to a handler function.

    handler signature: Callable[[dict], None]
    """

    def __init__(
        self,
        topics: Iterable[str],
        group_id: str,
        config: Optional[KafkaConfig] = None,
        **overrides: Any,
    ) -> None:
        self.config = config or KafkaConfig.from_env()
        consumer_kwargs = {
            **self.config.common_security_kwargs(),
            "group_id": group_id,
            "auto_offset_reset": self.config.auto_offset_reset,
            "enable_auto_commit": overrides.pop("enable_auto_commit", True),
            "value_deserializer": lambda v: json.loads(v.decode("utf-8")) if v is not None else None,
            "key_deserializer": lambda v: json.loads(v.decode("utf-8")) if v is not None else None,
            "session_timeout_ms": self.config.session_timeout_ms,
            "max_poll_records": overrides.pop("max_poll_records", 100),
        }
        consumer_kwargs.update(overrides)

        self._consumer = KafkaConsumer(**consumer_kwargs)
        if isinstance(topics, (list, tuple, set)):
            self._consumer.subscribe(list(topics))
        else:
            self._consumer.subscribe([topics])

    def poll_forever(self, handler: Callable[[dict], None]) -> None:
        for message in self._consumer:
            try:
                handler(message.value)
            except Exception as exc:  # pylint: disable=broad-except
                logger.exception("Handler error for topic %s: %s", message.topic, exc)

    def close(self) -> None:
        self._consumer.close()


