from typing import Iterable, List, Optional

from kafka import KafkaAdminClient
from kafka.admin import NewTopic

from .config import KafkaConfig
from shared.logging.logger import Logger


class KafkaAdmin:
    """Admin client to ensure topics exist."""

    def __init__(self, config: Optional[KafkaConfig] = None) -> None:
        self.config = config or KafkaConfig.from_env()
        # Initialize reusable logger
        self.logger = Logger.get_logger(name="playmaker_kafka_admin")
        self._admin = KafkaAdminClient(**self.config.common_security_kwargs())

    def create_topics_if_missing(
        self,
        topics: Iterable[str],
        num_partitions: int = 3,
        replication_factor: int = 1,
    ) -> List[str]:
        existing = set(t.topic for t in self._admin.list_topics())
        to_create = [
            NewTopic(name=t, num_partitions=num_partitions, replication_factor=replication_factor)
            for t in topics
            if t not in existing
        ]
        if not to_create:
            return []
        self._admin.create_topics(new_topics=to_create, validate_only=False)
        return [t.name for t in to_create]

    def close(self) -> None:
        self._admin.close()


