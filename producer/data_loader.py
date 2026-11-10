"""
Data Source Layer.
Reads smart meter electricity consumption records from CSV/JSONL,
validates schemas, filters invalid/missing values, and generates normalized event dictionaries.
"""

import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import csv
import logging
from datetime import datetime
from typing import Iterator, Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class SmartMeterDataLoader:
    """
    Loads, cleans, and yields valid event records from dataset files.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.records_read = 0
        self.records_valid = 0
        self.records_skipped = 0

    def validate_and_clean_row(self, row: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Validates row fields, checks for missing/corrupted values, and parses data types.
        
        Returns:
            Tuple of (cleaned_event, error_reason)
        """
        self.records_read += 1
        
        # 1. Validate Reading Time / Timestamp
        raw_time = row.get("Date_Time") or row.get("reading_time")
        if not raw_time or str(raw_time).strip() in ("?", "", "nan", "NaN"):
            self.records_skipped += 1
            return None, "Missing timestamp field"

        try:
            # Validate ISO timestamp or common date formats
            raw_time_str = str(raw_time).strip()
            if len(raw_time_str) == 19:
                datetime.strptime(raw_time_str, "%Y-%m-%d %H:%M:%S")
                cleaned_time = raw_time_str
            else:
                dt = datetime.fromisoformat(raw_time_str)
                cleaned_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            self.records_skipped += 1
            return None, f"Invalid timestamp format '{raw_time}': {e}"

        # 2. Validate Primary Metric: Global_active_power
        raw_active_power = row.get("Global_active_power") or row.get("global_active_power")
        if raw_active_power is None or str(raw_active_power).strip() in ("?", "", "nan", "NaN"):
            self.records_skipped += 1
            return None, "Missing mandatory Global_active_power value"

        try:
            active_power = float(raw_active_power)
            if active_power < 0:
                self.records_skipped += 1
                return None, f"Negative power reading ({active_power}) is physically invalid"
        except (ValueError, TypeError) as e:
            self.records_skipped += 1
            return None, f"Non-numeric Global_active_power '{raw_active_power}': {e}"

        # 3. Clean and parse optional numerical telemetry
        def parse_float(key_variants, default=0.0) -> float:
            for k in key_variants:
                val = row.get(k)
                if val is not None and str(val).strip() not in ("?", "", "nan", "NaN"):
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        pass
            return default

        reactive_power = parse_float(["Global_reactive_power", "global_reactive_power"], 0.0)
        intensity = parse_float(["Global_intensity", "global_intensity"], 0.0)
        sub1 = parse_float(["Sub_metering_1", "sub_metering_1"], 0.0)
        sub2 = parse_float(["Sub_metering_2", "sub_metering_2"], 0.0)
        sub3 = parse_float(["Sub_metering_3", "sub_metering_3"], 0.0)

        cleaned_event = {
            "reading_time": cleaned_time,
            "global_active_power": round(active_power, 3),
            "global_reactive_power": round(reactive_power, 3),
            "global_intensity": round(intensity, 3),
            "sub_metering_1": round(sub1, 3),
            "sub_metering_2": round(sub2, 3),
            "sub_metering_3": round(sub3, 3),
        }
        self.records_valid += 1
        return cleaned_event, None

    def stream_records(self, loop_continuously: bool = False) -> Iterator[Dict[str, Any]]:
        """
        Generator yielding validated event dictionaries from the CSV file.
        If loop_continuously is True, replays the file seamlessly once end-of-file is reached.
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Dataset file not found at: {self.file_path}")

        from datetime import timedelta

        loop_count = 0
        while True:
            with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    event, err = self.validate_and_clean_row(row)
                    if event:
                        if loop_count > 0:
                            # Advance timestamp monotonically for replay loops
                            try:
                                base_dt = datetime.strptime(event["reading_time"], "%Y-%m-%d %H:%M:%S")
                                new_dt = base_dt + timedelta(minutes=loop_count * 15000)
                                event["reading_time"] = new_dt.strftime("%Y-%m-%d %H:%M:%S")
                            except Exception:
                                pass
                        yield event
                    else:
                        logger.debug(f"Row validation skipped: {err}")

            if not loop_continuously:
                break
            loop_count += 1
            logger.info(f"Reached end of dataset file. Advancing loop #{loop_count} replay stream...")
