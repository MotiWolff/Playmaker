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

    def common_security_kwargs(self) -> dict:
        """Return kwargs dict for kafka-python clients based on config.

        Note: `bootstrap_servers` is returned as a list as expected by kafka-python.
        """
        kwargs: dict = {
            "bootstrap_servers": [s.strip() for s in self.bootstrap_servers.split(",") if s.strip()],
            "client_id": self.client_id,
            "security_protocol": self.security_protocol,
        }
        if self.security_protocol.startswith("SASL"):
            if self.sasl_mechanism:
                kwargs["sasl_mechanism"] = self.sasl_mechanism
            if self.sasl_username is not None and self.sasl_password is not None:
                kwargs["sasl_plain_username"] = self.sasl_username
                kwargs["sasl_plain_password"] = self.sasl_password
        return kwargs


