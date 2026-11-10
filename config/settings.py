"""
Centralized Application Configuration loaded from environment variables (.env).
Provides typed access and default values for all pipeline layers.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env file from root directory if present
load_dotenv(override=False)

@dataclass(frozen=True)
class Settings:
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:9092")
    KAFKA_TOPIC: str = os.getenv("KAFKA_TOPIC", "smartmeter-events")
    KAFKA_CONSUMER_GROUP: str = os.getenv("KAFKA_CONSUMER_GROUP", "smartmeter-processor-group")
    
    # MySQL Database Configuration
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "smartmeter")
    
    # Dataset and Producer Configuration
    DATASET_PATH: str = os.getenv("DATASET_PATH", os.path.join("data", "sample_data.csv"))
    PRODUCER_INTERVAL_SEC: float = float(os.getenv("PRODUCER_INTERVAL_SEC", "0.2"))  # 5 readings/sec
    CONTINUOUS_REPLAY: bool = os.getenv("CONTINUOUS_REPLAY", "True").lower() in ("true", "1", "yes")
    ANOMALY_INTERVAL_MIN: int = int(os.getenv("ANOMALY_INTERVAL_MIN", "20"))
    ANOMALY_INTERVAL_MAX: int = int(os.getenv("ANOMALY_INTERVAL_MAX", "30"))
    
    # Stream Processor and Machine Learning Configuration
    WINDOW_SIZE: int = int(os.getenv("WINDOW_SIZE", "30"))
    MODEL_PATH: str = os.getenv("MODEL_PATH", os.path.join("ml", "anomaly_model.pkl"))
    MODEL_METADATA_PATH: str = os.getenv("MODEL_METADATA_PATH", os.path.join("ml", "model_metadata.json"))
    IFOREST_CONTAMINATION: float = float(os.getenv("IFOREST_CONTAMINATION", "0.01"))
    IFOREST_RANDOM_STATE: int = int(os.getenv("IFOREST_RANDOM_STATE", "42"))
    
    # Dashboard Configuration
    DASHBOARD_REFRESH_INTERVAL_SEC: int = int(os.getenv("DASHBOARD_REFRESH_INTERVAL_SEC", "2"))
    DASHBOARD_QUERY_LIMIT: int = int(os.getenv("DASHBOARD_QUERY_LIMIT", "120"))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", os.path.join("logs", "pipeline.log"))

# Singleton instance
_settings_instance = None

def get_settings() -> Settings:
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
