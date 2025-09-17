import json
from typing import Any, Callable, Iterable, Optional

from kafka import KafkaConsumer
from Playmaker.shared.logging.logger import Logger

from .config import KafkaConfig

class JsonKafkaConsumer:
    """Poll JSON messages and hand them to a handler.

    handler: Callable[[dict], None]
    """

    def __init__(
        self,
        topics: Iterable[str] | str,
        group_id: str,
        config: Optional[KafkaConfig] = None,
        **overrides: Any,
    ) -> None:
        self.config = config or KafkaConfig.from_env()
        self.log = Logger.get_logger(name="playmaker.kafka.consumer")

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
            topics_list = list(topics)
        else:
            topics_list = [topics]
        self._consumer.subscribe(topics_list)
        self.log.info("kafka.consumer.init", extra={"topics": topics_list, "group_id": group_id})

    def poll_forever(self, handler: Callable[[dict], None]) -> None:
        count = 0
        try:
            for message in self._consumer:
                try:
                    handler(message.value)
                    count += 1
                    if count % 100 == 0:
                        self.log.debug("kafka.consumer.progress", extra={"handled": count})
                except Exception as exc:  # keep consuming
                    self.log.exception(
                        "kafka.consumer.handler_error",
                        extra={"topic": message.topic, "partition": message.partition, "offset": message.offset, "error": str(exc)}
                    )
        except KeyboardInterrupt:
            self.log.info("kafka.consumer.interrupted")
        finally:
            self.close()

    def close(self) -> None:
        try:
            self._consumer.close()
            self.log.info("kafka.consumer.closed")
        except Exception:
            pass
