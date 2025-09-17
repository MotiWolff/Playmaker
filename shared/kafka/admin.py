from typing import Iterable, List, Optional

from kafka import KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError

from .config import KafkaConfig
from Playmaker.shared.logging.logger import Logger

class KafkaAdmin:
    """Admin client to ensure topics exist."""

    def __init__(self, config: Optional[KafkaConfig] = None) -> None:
        self.config = config or KafkaConfig.from_env()
        self.log = Logger.get_logger(name="playmaker.kafka.admin")
        self._admin = KafkaAdminClient(**self.config.common_security_kwargs())
        self.log.info("kafka.admin.init")

    def create_topics_if_missing(
        self,
        topics: Iterable[str],
        num_partitions: int = 3,
        replication_factor: int = 1,
    ) -> List[str]:
        # NOTE: kafka-python's list_topics() returns a set of topic names (strings)
        existing = set(self._admin.list_topics())
        to_create = [
            NewTopic(name=t, num_partitions=num_partitions, replication_factor=replication_factor)
            for t in topics
            if t not in existing
        ]
        if not to_create:
            self.log.info("kafka.admin.noop", extra={"existing": len(existing)})
            return []

        created: List[str] = []
        try:
            self._admin.create_topics(new_topics=to_create, validate_only=False)
            created = [t.name for t in to_create]
            self.log.info("kafka.admin.created", extra={"topics": created})
        except TopicAlreadyExistsError:
            # Benign race
            self.log.warning("kafka.admin.race_already_exists")
        except Exception as e:
            self.log.exception("kafka.admin.create_failed", extra={"error": str(e)})
            raise
        return created

    def close(self) -> None:
        try:
            self._admin.close()
            self.log.info("kafka.admin.closed")
        except Exception:
            pass
