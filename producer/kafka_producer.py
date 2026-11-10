"""
Kafka Producer Layer.
Streams validated smart-meter telemetry records to the Apache Kafka broker at configurable intervals.
"""

import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import time
import signal
import random
import logging
from typing import Optional
from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from config.settings import get_settings
from producer.data_loader import SmartMeterDataLoader

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class SmartMeterProducer:
    """
    Kafka producer that reads dataset records and publishes JSON telemetry messages
    to the smartmeter-events topic.
    """
    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        topic: Optional[str] = None,
        dataset_path: Optional[str] = None,
        interval_sec: Optional[float] = None,
        continuous: Optional[bool] = None
    ):
        settings = get_settings()
        self.bootstrap_servers = bootstrap_servers or settings.KAFKA_BOOTSTRAP_SERVERS
        self.topic = topic or settings.KAFKA_TOPIC
        self.dataset_path = dataset_path or settings.DATASET_PATH
        self.interval_sec = interval_sec if interval_sec is not None else settings.PRODUCER_INTERVAL_SEC
        self.continuous = continuous if continuous is not None else settings.CONTINUOUS_REPLAY

        self.producer = None
        self.running = False
        self.total_sent = 0
        self.total_failed = 0

        self.loader = SmartMeterDataLoader(self.dataset_path)

    def _ensure_topic_exists(self):
        """Verifies topic existence and creates topic if not present."""
        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers,
                client_id="smartmeter-admin-client",
                request_timeout_ms=5000
            )
            existing_topics = admin_client.list_topics()
            if self.topic not in existing_topics:
                logger.info(f"Topic '{self.topic}' does not exist. Creating with 1 partition, replication-factor 1...")
                new_topic = NewTopic(name=self.topic, num_partitions=1, replication_factor=1)
                admin_client.create_topics(new_topics=[new_topic], validate_only=False)
                logger.info(f"Topic '{self.topic}' created successfully.")
            else:
                logger.info(f"Kafka topic '{self.topic}' is verified and ready.")
            admin_client.close()
        except Exception as e:
            logger.warning(f"Could not verify/create topic via AdminClient (broker auto-creation may apply): {e}")

    def connect(self) -> bool:
        """Initializes connection to Kafka broker."""
        self._ensure_topic_exists()
        logger.info(f"Connecting KafkaProducer to {self.bootstrap_servers}...")
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",
                retries=3,
                request_timeout_ms=10000
            )
            logger.info("KafkaProducer successfully connected.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect KafkaProducer to {self.bootstrap_servers}: {e}")
            self.producer = None
            return False

    def start(self, max_records: Optional[int] = None):
        """
        Starts publishing events continuously.
        """
        if not self.producer and not self.connect():
            logger.error("Producer cannot start without broker connection.")
            return

        self.running = True
        logger.info(f"Starting event stream -> Topic: '{self.topic}' | Interval: {self.interval_sec}s | Replay: {self.continuous}")

        from config.stream_control import get_stream_state, get_reset_counter

        settings = get_settings()
        anom_min = getattr(settings, "ANOMALY_INTERVAL_MIN", 20)
        anom_max = getattr(settings, "ANOMALY_INTERVAL_MAX", 30)

        last_reset_version = get_reset_counter()
        readings_since_anomaly = 0
        next_anomaly_interval = random.randint(anom_min, anom_max)

        try:
            while self.running:
                for event in self.loader.stream_records(loop_continuously=self.continuous):
                    if not self.running:
                        break

                    # Check dynamic streaming controls (Pause / Delay / Reset)
                    current_reset_version = get_reset_counter()
                    if current_reset_version > last_reset_version:
                        last_reset_version = current_reset_version
                        logger.info("Demo reset detected in Producer. Resetting sent counters and replaying from record 0.")
                        self.total_sent = 0
                        self.total_failed = 0
                        readings_since_anomaly = 0
                        next_anomaly_interval = random.randint(anom_min, anom_max)
                        break  # Breaks inner loop to restart stream_records from beginning

                    state = get_stream_state()

                    # Pause handling
                    if not state.get("is_streaming", True):
                        logger.info("Stream paused by user via Streaming Controls. Awaiting resume...")
                        while self.running and not get_stream_state().get("is_streaming", True):
                            time.sleep(0.15)
                        if not self.running:
                            break
                        logger.info("Stream resumed by user via Streaming Controls.")

                    # Inject realistic anomaly surge every 20-30 readings
                    readings_since_anomaly += 1
                    raw_power = float(event.get("global_active_power", 0.0))
                    if raw_power >= 5.85:
                        readings_since_anomaly = 0
                        next_anomaly_interval = random.randint(anom_min, anom_max)
                    elif readings_since_anomaly >= next_anomaly_interval:
                        surge_power = round(random.uniform(6.20, 8.10), 3)
                        event["global_active_power"] = surge_power
                        event["global_intensity"] = round(surge_power * 1000.0 / 240.0, 1)
                        event["sub_metering_3"] = round(random.uniform(18.0, 32.0), 1)
                        readings_since_anomaly = 0
                        next_anomaly_interval = random.randint(anom_min, anom_max)
                        logger.info(
                            f"[Sent #{self.total_sent + 1}] ⚠️ [ANOMALY SURGE INJECTED] Power: {surge_power} kW (Next in {next_anomaly_interval} readings)"
                        )

                    # Send event to Kafka
                    try:
                        future = self.producer.send(self.topic, value=event)
                        self.total_sent += 1
                        
                        if self.total_sent % 20 == 0 or self.total_sent <= 5:
                            logger.info(
                                f"[Sent #{self.total_sent}] Time: {event['reading_time']} | "
                                f"Active Power: {event['global_active_power']} kW | Sub3: {event['sub_metering_3']}"
                            )
                    except Exception as e:
                        self.total_failed += 1
                        logger.error(f"Failed to publish event #{self.total_sent + 1}: {e}")

                    if max_records and self.total_sent >= max_records:
                        logger.info(f"Reached specified limit of {max_records} records.")
                        self.running = False
                        break

                    current_delay = float(get_stream_state().get("replay_delay", self.interval_sec))
                    time.sleep(current_delay)

                if not self.continuous or not self.running:
                    break

        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received in producer.")
        finally:
            self.stop()

    def stop(self):
        """Gracefully flushes and closes the Kafka producer."""
        self.running = False
        if self.producer:
            logger.info(f"Flushing remaining messages... (Total Sent: {self.total_sent}, Skipped: {self.loader.records_skipped})")
            try:
                self.producer.flush(timeout=5)
                self.producer.close()
                logger.info("KafkaProducer successfully closed.")
            except Exception as e:
                logger.warning(f"Error while closing producer: {e}")
            self.producer = None

def main():
    producer = SmartMeterProducer()

    def signal_handler(sig, frame):
        logger.info("Termination signal received. Shutting down Kafka Producer...")
        producer.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    producer.start()

if __name__ == "__main__":
    main()
