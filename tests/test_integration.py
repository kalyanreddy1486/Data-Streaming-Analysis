"""
End-to-End Pipeline Integration Test.
Verifies the complete flow across all six layers:
Producer -> Kafka Broker -> Consumer -> Stream Processor -> ML Model -> MySQL -> Repository.
"""

import time
import pytest
from datetime import datetime
from config.settings import get_settings
from producer.kafka_producer import SmartMeterProducer
from processor.stream_processor import StreamProcessor
from database.repository import MeterRepository
from database.db_initializer import reset_database

def test_end_to_end_pipeline():
    settings = get_settings()
    repo = MeterRepository()
    
    # 1. Reset tables to test fresh ingestion
    assert reset_database() is True

    # 2. Check initial count in MySQL
    initial_metrics = repo.get_latest_metrics()
    assert int(initial_metrics["total_readings"]) == 0

    # 3. Instantiate Producer and send 5 events
    producer = SmartMeterProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        topic=settings.KAFKA_TOPIC,
        dataset_path="data/sample_data.csv",
        interval_sec=0.01,
        continuous=False
    )
    assert producer.connect() is True
    producer.start(max_records=5)

    # 4. Instantiate Stream Processor with isolated test consumer group
    processor = StreamProcessor(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        topic=settings.KAFKA_TOPIC,
        window_size=30
    )
    # Assign unique group id to ensure reading from earliest offset in test
    processor.consumer.group_id = f"test-group-{int(time.time())}"
    processor.consumer.auto_offset_reset = "earliest"
    processor.start(max_events=5)

    # 5. Verify records reached MySQL
    updated_metrics = repo.get_latest_metrics()
    assert int(updated_metrics["total_readings"]) >= 5
    assert float(updated_metrics["current_power"]) > 0.0
    assert float(updated_metrics["total_energy_kwh"]) > 0.0

    # 6. Verify dashboard serving layer DataFrame
    df = repo.get_recent_readings(limit=10)
    assert len(df) >= 5
    assert "is_anomaly" in df.columns
    assert "rolling_avg_30" in df.columns
