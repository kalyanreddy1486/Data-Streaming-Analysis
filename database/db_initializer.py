"""
Database Schema Initializer.
Executes schema.sql statements to create the smartmeter database and all required tables.
"""

import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging
from database.db_connection import get_db_connection
from config.settings import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def initialize_database(schema_path: str = None) -> bool:
    """
    Initializes the MySQL database and creates tables from schema.sql.
    """
    settings = get_settings()
    if schema_path is None:
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")

    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found at {schema_path}")
        return False

    logger.info(f"Connecting to MySQL server at {settings.MYSQL_HOST}:{settings.MYSQL_PORT}...")
    conn = get_db_connection(use_database=False)
    if not conn:
        logger.error("Could not establish initial connection to MySQL server. Ensure MySQL is running.")
        return False

    try:
        cursor = conn.cursor()
        with open(schema_path, "r", encoding="utf-8") as f:
            sql_content = f.read()

        # Split commands on semicolons
        statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]

        for stmt in statements:
            try:
                cursor.execute(stmt)
            except Exception as e:
                logger.error(f"Error executing statement: {stmt[:60]}... -> {e}")
                raise

        logger.info(f"Successfully initialized database '{settings.MYSQL_DATABASE}' and tables.")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        if conn and conn.is_connected():
            conn.close()
        return False

def reset_database() -> bool:
    """
    Truncates tables to allow a clean presentation demonstration starting from count 0.
    """
    conn = get_db_connection(use_database=True)
    if not conn:
        logger.error("Could not connect to database to reset tables.")
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE meter_readings;")
        cursor.execute("""
            UPDATE meter_metrics 
            SET current_power=0.000, rolling_avg_30=0.000, running_peak=0.000,
                total_energy_kwh=0.0000, total_readings=0, total_anomalies=0,
                last_updated=NOW()
            WHERE metric_id=1;
        """)
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Successfully reset meter_readings and meter_metrics for demonstration.")
        return True
    except Exception as e:
        logger.error(f"Failed to reset tables: {e}")
        if conn and conn.is_connected():
            conn.close()
        return False

if __name__ == "__main__":
    success = initialize_database()
    sys.exit(0 if success else 1)
