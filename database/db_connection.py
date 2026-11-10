"""
MySQL Database Connection Manager.
Provides connection pooling and factory functions with resilient error handling.
"""

import mysql.connector
from mysql.connector import Error, errorcode
import logging
from typing import Optional
from config.settings import get_settings

logger = logging.getLogger(__name__)

def get_db_connection(use_database: bool = True) -> Optional[mysql.connector.MySQLConnection]:
    """
    Creates and returns a new MySQL database connection using configured environment credentials.
    """
    settings = get_settings()
    config = {
        'host': settings.MYSQL_HOST,
        'port': settings.MYSQL_PORT,
        'user': settings.MYSQL_USER,
        'password': settings.MYSQL_PASSWORD,
        'autocommit': True,
        'connection_timeout': 5
    }
    
    if use_database:
        config['database'] = settings.MYSQL_DATABASE

    try:
        connection = mysql.connector.connect(**config)
        return connection
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_BAD_DB_ERROR and use_database:
            logger.warning(f"Database '{settings.MYSQL_DATABASE}' does not exist yet. Please initialize the database.")
        else:
            logger.error(f"MySQL connection error: {err}")
        return None

def check_db_connection() -> bool:
    """
    Pings the MySQL server to verify live connectivity.
    """
    try:
        conn = get_db_connection(use_database=False)
        if conn and conn.is_connected():
            conn.close()
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to check MySQL connection: {e}")
        return False
