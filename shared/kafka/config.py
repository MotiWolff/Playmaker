import os
from dataclasses import dataclass
from typing import Optional, Type, TypeVar


@dataclass(frozen=True)
class KafkaConfig:
    """Configuration for Kafka connectivity via environment variables.

    Variables:
      - KAFKA_BOOTSTRAP_SERVERS: comma-separated host:port list
      - KAFKA_SECURITY_PROTOCOL: PLAINTEXT (default), SASL_PLAINTEXT, SASL_SSL, SSL
      - KAFKA_SASL_MECHANISM: e.g., PLAIN
      - KAFKA_SASL_USERNAME / KAFKA_SASL_PASSWORD: for SASL auth
      - KAFKA_CLIENT_ID: client identifier
      - KAFKA_SESSION_TIMEOUT_MS: consumer session timeout
      - KAFKA_AUTO_OFFSET_RESET: earliest/latest
    """

    bootstrap_servers: str
    security_protocol: str
    sasl_mechanism: Optional[str]
    sasl_username: Optional[str]
    sasl_password: Optional[str]
    client_id: str
    session_timeout_ms: int
    auto_offset_reset: str

    @classmethod
    def from_env(cls: "Type[KafkaConfig]") -> "KafkaConfig":
        """Build KafkaConfig from environment variables.

        Prefer this constructor across the codebase to avoid importing-time env evaluation surprises.
        """
        return cls(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
            security_protocol=os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
            sasl_mechanism=os.getenv("KAFKA_SASL_MECHANISM"),
            sasl_username=os.getenv("KAFKA_SASL_USERNAME"),
            sasl_password=os.getenv("KAFKA_SASL_PASSWORD"),
            client_id=os.getenv("KAFKA_CLIENT_ID", "playmaker-client"),
            session_timeout_ms=int(os.getenv("KAFKA_SESSION_TIMEOUT_MS", "30000")),
            auto_offset_reset=os.getenv("KAFKA_AUTO_OFFSET_RESET", "earliest"),
        )


