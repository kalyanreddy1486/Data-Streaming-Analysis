"""
Stream Processing Engine.
Consumes events from Apache Kafka, executes stateful sliding window aggregations,
scores each reading with the trained Isolation Forest ML model,
persists enriched readings to MySQL, and updates the real-time metrics snapshot.
"""

import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
import signal
import logging
from typing import Optional
from config.settings import get_settings
from processor.metrics import StreamMetricsCalculator
from processor.kafka_consumer import SmartMeterConsumer
from ml.predict import AnomalyDetector
from database.repository import MeterRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class StreamProcessor:
    """
    Core stream processing coordinator uniting Kafka ingestion,
    windowed metrics aggregation, machine learning inference, and database persistence.
    """
    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        topic: Optional[str] = None,
        window_size: Optional[int] = None
    ):
        settings = get_settings()
        self.bootstrap_servers = bootstrap_servers or settings.KAFKA_BOOTSTRAP_SERVERS
        self.topic = topic or settings.KAFKA_TOPIC
        self.window_size = window_size or settings.WINDOW_SIZE
        
        self.repository = MeterRepository()
        self.anomaly_detector = AnomalyDetector()
        self.consumer = SmartMeterConsumer(
            bootstrap_servers=self.bootstrap_servers,
            topic=self.topic
        )

        # Restore initial state from database to preserve cumulative statistics across restarts
        initial_metrics = self.repository.get_latest_metrics() or {}
        self.metrics_calc = StreamMetricsCalculator(
            window_size=self.window_size,
            initial_peak=float(initial_metrics.get("running_peak", 0.0)),
            initial_energy_kwh=float(initial_metrics.get("total_energy_kwh", 0.0)),
            initial_readings_count=int(initial_metrics.get("total_readings", 0)),
            initial_anomalies_count=int(initial_metrics.get("total_anomalies", 0))
        )

        self.running = False
        self.events_processed = 0

    def start(self, max_events: Optional[int] = None):
        """
        Runs the continuous streaming event loop.
        """
        logger.info("Initializing Stream Processor...")
        if not self.consumer.connect():
            logger.error("Stream Processor could not connect to Kafka consumer. Retrying...")
            # Retry connection loop
            connected = False
            for attempt in range(1, 6):
                time.sleep(2)
                logger.info(f"Retrying Kafka connection (attempt {attempt}/5)...")
                if self.consumer.connect():
                    connected = True
                    break
            if not connected:
                logger.error("Could not connect to Kafka. Processor exiting.")
                return

        self.running = True
        logger.info(f"Stream Processor active. Listening for events on topic '{self.topic}' (Window: {self.window_size})...")

        from config.stream_control import get_reset_counter

        last_reset_version = get_reset_counter()

        try:
            while self.running:
                # Check for live demo reset signal
                current_reset_version = get_reset_counter()
                if current_reset_version > last_reset_version:
                    last_reset_version = current_reset_version
                    logger.info("Live Demo Reset signal received! Clearing sliding window and zeroing metrics.")
                    self.metrics_calc.reset()
                    self.events_processed = 0

                for message in self.consumer.poll_messages():
                    if not self.running:
                        break

                    # Check reset again in message batch
                    current_reset_version = get_reset_counter()
                    if current_reset_version > last_reset_version:
                        last_reset_version = current_reset_version
                        logger.info("Live Demo Reset signal received in message batch! Resetting metrics.")
                        self.metrics_calc.reset()
                        self.events_processed = 0

                    event = message.value
                    if not event or not isinstance(event, dict):
                        logger.warning(f"Skipping malformed or empty message: {event}")
                        continue

                    try:
                        self.process_single_event(event)
                        self.consumer.commit()
                        self.events_processed += 1

                        if max_events and self.events_processed >= max_events:
                            logger.info(f"Reached processing limit of {max_events} events.")
                            self.running = False
                            break
                    except Exception as e:
                        logger.error(f"Error processing event {event}: {e}", exc_info=True)
                        # Continue processing subsequent events without crashing

                time.sleep(0.05)  # Brief yield for CPU hygiene

        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received in Stream Processor.")
        finally:
            self.stop()

    def process_single_event(self, event: dict):
        """
        Executes end-to-end processing pipeline for a single event:
        1. Parse and extract active power
        2. Score with ML Isolation Forest
        3. Update rolling window and stream metrics
        4. Insert into MySQL meter_readings
        5. Update MySQL meter_metrics snapshot
        """
        power = float(event.get("global_active_power", 0.0))
        reading_time = event.get("reading_time")

        # Layer 4: ML Anomaly Inference
        is_anomaly, anomaly_score = self.anomaly_detector.predict(power)

        # Layer 3: Sliding Window & Metrics Calculation
        metric_snapshot = self.metrics_calc.update(
            power=power,
            is_anomaly=is_anomaly,
            reading_time=reading_time
        )

        # Prepare record for MySQL
        db_record = {
            "reading_time": reading_time,
            "global_active_power": power,
            "global_reactive_power": event.get("global_reactive_power", 0.0),
            "global_intensity": event.get("global_intensity", 0.0),
            "sub_metering_1": event.get("sub_metering_1", 0.0),
            "sub_metering_2": event.get("sub_metering_2", 0.0),
            "sub_metering_3": event.get("sub_metering_3", 0.0),
            "rolling_avg_30": metric_snapshot["rolling_avg_30"],
            "is_anomaly": is_anomaly
        }

        # Layer 5: Database Persistence
        self.repository.insert_reading(db_record)
        self.repository.update_metrics_snapshot(metric_snapshot)

        # Logging output
        anomaly_flag_str = " [ANOMALY DETECTED!]" if is_anomaly else ""
        if self.events_processed % 10 == 0 or is_anomaly:
            logger.info(
                f"[Processed #{metric_snapshot['total_readings']}] Time: {reading_time} | "
                f"Power: {power:.3f} kW | Rolling Avg(30): {metric_snapshot['rolling_avg_30']:.3f} kW | "
                f"Peak: {metric_snapshot['running_peak']:.3f} kW | Energy: {metric_snapshot['total_energy_kwh']:.4f} kWh | "
                f"Anomalies: {metric_snapshot['total_anomalies']}{anomaly_flag_str}"
            )

    def stop(self):
        """Stops the processor and closes consumer connections."""
        self.running = False
        if self.consumer:
            self.consumer.close()
        logger.info(f"Stream Processor stopped. (Total events processed this session: {self.events_processed})")

def main():
    processor = StreamProcessor()

    def signal_handler(sig, frame):
        logger.info("Termination signal received. Shutting down Stream Processor...")
        processor.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    processor.start()

if __name__ == "__main__":
    main()
