"""
Unit tests for Data Source Layer (data_loader.py).
Tests CSV reading, row cleaning, handling missing values, and timestamp validation.
"""

import pytest
import os
from producer.data_loader import SmartMeterDataLoader

def test_data_loader_valid_row():
    loader = SmartMeterDataLoader("data/sample_data.csv")
    raw_row = {
        "Date_Time": "2006-12-16 17:24:00",
        "Global_active_power": "4.216",
        "Global_reactive_power": "0.418",
        "Global_intensity": "18.4",
        "Sub_metering_1": "0.0",
        "Sub_metering_2": "1.0",
        "Sub_metering_3": "17.0"
    }
    event, err = loader.validate_and_clean_row(raw_row)
    assert err is None
    assert event is not None
    assert event["reading_time"] == "2006-12-16 17:24:00"
    assert event["global_active_power"] == 4.216
    assert event["sub_metering_3"] == 17.0

def test_data_loader_missing_values():
    loader = SmartMeterDataLoader("data/sample_data.csv")
    
    # Missing Global_active_power
    bad_row_1 = {
        "Date_Time": "2006-12-16 17:24:00",
        "Global_active_power": "?",
        "Global_reactive_power": "0.418"
    }
    event1, err1 = loader.validate_and_clean_row(bad_row_1)
    assert event1 is None
    assert "Missing mandatory" in err1

    # Missing Timestamp
    bad_row_2 = {
        "Date_Time": "",
        "Global_active_power": "3.5"
    }
    event2, err2 = loader.validate_and_clean_row(bad_row_2)
    assert event2 is None
    assert "Missing timestamp" in err2

def test_data_loader_invalid_numbers():
    loader = SmartMeterDataLoader("data/sample_data.csv")
    
    bad_row = {
        "Date_Time": "2006-12-16 17:24:00",
        "Global_active_power": "abc_not_a_number"
    }
    event, err = loader.validate_and_clean_row(bad_row)
    assert event is None
    assert "Non-numeric" in err

def test_data_loader_sample_file_streaming():
    if os.path.exists("data/sample_data.csv"):
        loader = SmartMeterDataLoader("data/sample_data.csv")
        records = []
        for i, record in enumerate(loader.stream_records(loop_continuously=False)):
            records.append(record)
            if i >= 10:
                break
        assert len(records) > 0
        assert "global_active_power" in records[0]
