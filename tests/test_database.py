"""
Unit and integration tests for MySQL Database Layer (db_connection.py, repository.py).
Tests database connection, parameterized insertions, snapshot updates, and DataFrame queries.
"""

import pytest
from datetime import datetime
from database.db_connection import check_db_connection
from database.repository import MeterRepository
from database.db_initializer import initialize_database

def test_database_connectivity():
    assert check_db_connection() is True

def test_database_initialization():
    assert initialize_database() is True

def test_database_insert_and_retrieve():
    repo = MeterRepository()
    test_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Insert a test reading
    inserted = repo.insert_reading({
        "reading_time": test_time,
        "global_active_power": 4.123,
        "global_reactive_power": 0.250,
        "global_intensity": 18.0,
        "sub_metering_1": 0.0,
        "sub_metering_2": 1.0,
        "sub_metering_3": 17.0,
        "rolling_avg_30": 3.850,
        "is_anomaly": 1
    })
    assert inserted is True

    # 2. Update metrics snapshot
    updated = repo.update_metrics_snapshot({
        "current_power": 4.123,
        "rolling_avg_30": 3.850,
        "running_peak": 5.200,
        "total_energy_kwh": 12.3456,
        "total_readings": 150,
        "total_anomalies": 3,
        "last_updated": test_time
    })
    assert updated is True

    # 3. Retrieve latest metrics
    latest = repo.get_latest_metrics()
    assert latest is not None
    assert float(latest["current_power"]) == 4.123
    assert int(latest["total_readings"]) == 150
    assert int(latest["total_anomalies"]) == 3

    # 4. Retrieve recent readings DataFrame
    df = repo.get_recent_readings(limit=10)
    assert not df.empty
    assert "global_active_power" in df.columns
    assert "rolling_avg_30" in df.columns
