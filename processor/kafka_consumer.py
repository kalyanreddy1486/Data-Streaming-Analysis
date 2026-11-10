"""
Kafka Consumer Layer.
Consumes JSON telemetry events from the Apache Kafka broker with resilience and manual offset commit support.
"""

import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import logging
from typing import Iterator, Optional, Dict, Any
from kafka import KafkaConsumer
from config.settings import get_settings

logger = logging.getLogger(__name__)

class SmartMeterConsumer:
    """
    Subscribes to smartmeter-events topic and yields valid parsed dictionaries.
    """
    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        topic: Optional[str] = None,
        group_id: Optional[str] = None,
        auto_offset_reset: str = "earliest"
    ):
        settings = get_settings()
        self.bootstrap_servers = bootstrap_servers or settings.KAFKA_BOOTSTRAP_SERVERS
        self.topic = topic or settings.KAFKA_TOPIC
        self.group_id = group_id or settings.KAFKA_CONSUMER_GROUP
        self.auto_offset_reset = auto_offset_reset
        self.consumer: Optional[KafkaConsumer] = None

    def connect(self) -> bool:
        """Establishes connection and subscription to the Kafka topic."""
        logger.info(f"Connecting KafkaConsumer to {self.bootstrap_servers} [Topic: {self.topic}, Group: {self.group_id}]...")
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset=self.auto_offset_reset,
                enable_auto_commit=False,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                consumer_timeout_ms=3000
            )
            logger.info("KafkaConsumer connected successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect KafkaConsumer: {e}")
            self.consumer = None
            return False

    def poll_messages(self) -> Iterator[Any]:
        """
        Polls and yields messages. Safely handles malformed messages and empty poll cycles.
        """
        if not self.consumer and not self.connect():
            return

        while True:
            try:
                for message in self.consumer:
                    yield message
            except StopIteration:
                # Polling timeout, yield control
                break
            except Exception as e:
                logger.error(f"Error while polling Kafka messages: {e}")
                break

    def commit(self):
        """Commits the current offset to prevent reprocessing."""
        if self.consumer:
            try:
                self.consumer.commit()
            except Exception as e:
                logger.warning(f"Error committing Kafka offset: {e}")

    def close(self):
        """Closes the Kafka consumer connection."""
        if self.consumer:
            try:
                self.consumer.close()
                logger.info("KafkaConsumer closed.")
            except Exception as e:
                logger.warning(f"Error closing consumer: {e}")
            self.consumer = None
