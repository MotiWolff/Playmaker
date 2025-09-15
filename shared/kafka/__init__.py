"""
Shared Kafka utilities for Playmaker services.

Modules:
- config: Environment-driven configuration helpers
- producer: JSON KafkaProducer wrapper
- consumer: JSON KafkaConsumer base with loop helper
- admin: Topic management (create-if-missing)

Usage example:
    from shared.kafka.producer import JsonKafkaProducer
    producer = JsonKafkaProducer()
    producer.send_json("fixtures.soccer", {"fixture_id": 123, "team_home": "RMA"})

    from shared.kafka.consumer import JsonKafkaConsumer
    def handle(msg):
        print(msg)
    consumer = JsonKafkaConsumer(topics=["fixtures.soccer"], group_id="playmaker-loader")
    consumer.poll_forever(handle)
"""

from .config import KafkaConfig
from .producer import JsonKafkaProducer
from .consumer import JsonKafkaConsumer
from .admin import KafkaAdmin

__all__ = [
  "KafkaConfig",
  "JsonKafkaProducer",
  "JsonKafkaConsumer",
  "KafkaAdmin",
]


