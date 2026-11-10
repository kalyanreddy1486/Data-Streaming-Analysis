"""
Data Access Layer (Repository Pattern).
Provides safe parameterized queries for inserting processed readings,
updating the metrics snapshot, and querying historical records for the dashboard.
"""

import logging
from typing import Optional, Dict, Any
import pandas as pd
from database.db_connection import get_db_connection

logger = logging.getLogger(__name__)

class MeterRepository:
    def __init__(self):
        pass

    def insert_reading(self, reading_data: Dict[str, Any]) -> bool:
        """
        Inserts a single processed reading into the meter_readings table.
        Uses parameterized SQL to prevent injection vulnerabilities.
        """
        query = """
            INSERT INTO meter_readings (
                reading_time, global_active_power, global_reactive_power,
                global_intensity, sub_metering_1, sub_metering_2, sub_metering_3,
                rolling_avg_30, is_anomaly
            ) VALUES (
                %(reading_time)s, %(global_active_power)s, %(global_reactive_power)s,
                %(global_intensity)s, %(sub_metering_1)s, %(sub_metering_2)s, %(sub_metering_3)s,
                %(rolling_avg_30)s, %(is_anomaly)s
            )
        """
        conn = get_db_connection(use_database=True)
        if not conn:
            logger.error("Database connection unavailable for inserting reading.")
            return False

        try:
            cursor = conn.cursor()
            cursor.execute(query, {
                "reading_time": reading_data.get("reading_time"),
                "global_active_power": float(reading_data.get("global_active_power", 0.0)),
                "global_reactive_power": float(reading_data.get("global_reactive_power", 0.0)),
                "global_intensity": float(reading_data.get("global_intensity", 0.0)),
                "sub_metering_1": float(reading_data.get("sub_metering_1", 0.0)),
                "sub_metering_2": float(reading_data.get("sub_metering_2", 0.0)),
                "sub_metering_3": float(reading_data.get("sub_metering_3", 0.0)),
                "rolling_avg_30": float(reading_data.get("rolling_avg_30", 0.0)),
                "is_anomaly": int(reading_data.get("is_anomaly", 0)),
            })
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to insert reading into meter_readings: {e}")
            if conn and conn.is_connected():
                conn.close()
            return False

    def update_metrics_snapshot(self, metrics: Dict[str, Any]) -> bool:
        """
        Updates the singleton snapshot row in meter_metrics with the latest calculations.
        """
        query = """
            INSERT INTO meter_metrics (
                metric_id, current_power, rolling_avg_30, running_peak,
                total_energy_kwh, total_readings, total_anomalies, last_updated
            ) VALUES (
                1, %(current_power)s, %(rolling_avg_30)s, %(running_peak)s,
                %(total_energy_kwh)s, %(total_readings)s, %(total_anomalies)s, %(last_updated)s
            ) ON DUPLICATE KEY UPDATE
                current_power = VALUES(current_power),
                rolling_avg_30 = VALUES(rolling_avg_30),
                running_peak = VALUES(running_peak),
                total_energy_kwh = VALUES(total_energy_kwh),
                total_readings = VALUES(total_readings),
                total_anomalies = VALUES(total_anomalies),
                last_updated = VALUES(last_updated);
        """
        conn = get_db_connection(use_database=True)
        if not conn:
            logger.error("Database connection unavailable for updating metrics snapshot.")
            return False

        try:
            cursor = conn.cursor()
            cursor.execute(query, {
                "current_power": float(metrics.get("current_power", 0.0)),
                "rolling_avg_30": float(metrics.get("rolling_avg_30", 0.0)),
                "running_peak": float(metrics.get("running_peak", 0.0)),
                "total_energy_kwh": float(metrics.get("total_energy_kwh", 0.0)),
                "total_readings": int(metrics.get("total_readings", 0)),
                "total_anomalies": int(metrics.get("total_anomalies", 0)),
                "last_updated": metrics.get("last_updated")
            })
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to update meter_metrics snapshot: {e}")
            if conn and conn.is_connected():
                conn.close()
            return False

    def get_latest_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Retrieves the latest KPI snapshot row from meter_metrics.
        """
        query = """
            SELECT current_power, rolling_avg_30, running_peak,
                   total_energy_kwh, total_readings, total_anomalies, last_updated
            FROM meter_metrics
            WHERE metric_id = 1;
        """
        conn = get_db_connection(use_database=True)
        if not conn:
            return None

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            return row
        except Exception as e:
            logger.error(f"Error fetching latest metrics: {e}")
            if conn and conn.is_connected():
                conn.close()
            return None

    def get_recent_readings(self, limit: int = 120) -> pd.DataFrame:
        """
        Fetches the latest N readings ordered chronologically (oldest to newest among the last N)
        for real-time time-series rendering.
        """
        query = f"""
            SELECT reading_pk, reading_time, global_active_power,
                   rolling_avg_30, is_anomaly, global_reactive_power,
                   global_intensity, sub_metering_1, sub_metering_2, sub_metering_3
            FROM (
                SELECT * FROM meter_readings
                ORDER BY reading_pk DESC
                LIMIT {limit}
            ) AS recent
            ORDER BY reading_pk ASC;
        """
        conn = get_db_connection(use_database=True)
        if not conn:
            return pd.DataFrame()

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return pd.DataFrame(rows) if rows else pd.DataFrame(columns=[
                "reading_pk", "reading_time", "global_active_power", "rolling_avg_30",
                "is_anomaly", "global_reactive_power", "global_intensity",
                "sub_metering_1", "sub_metering_2", "sub_metering_3"
            ])
        except Exception as e:
            logger.error(f"Error fetching recent readings DataFrame: {e}")
            if conn and conn.is_connected():
                conn.close()
            return pd.DataFrame()

    def get_recent_anomalies(self, limit: int = 20) -> pd.DataFrame:
        """
        Fetches the latest N anomalous events from meter_readings.
        """
        query = f"""
            SELECT reading_pk, reading_time, global_active_power,
                   rolling_avg_30, is_anomaly, global_intensity,
                   sub_metering_1, sub_metering_2, sub_metering_3
            FROM meter_readings
            WHERE is_anomaly = 1
            ORDER BY reading_pk DESC
            LIMIT {limit};
        """
        conn = get_db_connection(use_database=True)
        if not conn:
            return pd.DataFrame()

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return pd.DataFrame(rows) if rows else pd.DataFrame(columns=[
                "reading_pk", "reading_time", "global_active_power", "rolling_avg_30",
                "is_anomaly", "global_intensity", "sub_metering_1", "sub_metering_2", "sub_metering_3"
            ])
        except Exception as e:
            logger.error(f"Error fetching recent anomalies DataFrame: {e}")
            if conn and conn.is_connected():
                conn.close()
            return pd.DataFrame()
