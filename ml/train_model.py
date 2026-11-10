"""
Offline Machine Learning Model Training Module.
Trains an Isolation Forest anomaly detector on historical smart meter power readings
and persists the model and metadata artifacts.
"""

import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import logging
from datetime import datetime
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib
from config.settings import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def train_anomaly_model(
    dataset_path: str = None,
    model_output_path: str = None,
    metadata_output_path: str = None,
    contamination: float = None,
    random_state: int = None
):
    """
    Loads historical power consumption data, cleans missing values,
    fits an Isolation Forest model, and exports model artifacts and metadata.
    """
    settings = get_settings()
    dataset_path = dataset_path or settings.DATASET_PATH
    model_output_path = model_output_path or settings.MODEL_PATH
    metadata_output_path = metadata_output_path or settings.MODEL_METADATA_PATH
    contamination = contamination if contamination is not None else settings.IFOREST_CONTAMINATION
    random_state = random_state if random_state is not None else settings.IFOREST_RANDOM_STATE

    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)

    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Training dataset not found at {dataset_path}. Please check data path.")

    logger.info(f"Loading historical dataset from {dataset_path}...")
    df = pd.read_csv(dataset_path)
    
    # Validate column existence
    target_column = "Global_active_power"
    if target_column not in df.columns:
        raise ValueError(f"Required target column '{target_column}' missing from dataset.")

    # Drop missing / invalid numeric records
    initial_count = len(df)
    clean_series = pd.to_numeric(df[target_column], errors="coerce").dropna()
    valid_count = len(clean_series)
    logger.info(f"Processed {valid_count} valid samples (dropped {initial_count - valid_count} invalid/empty rows).")

    X = clean_series.to_frame(name=target_column)

    logger.info(f"Training IsolationForest (contamination={contamination}, random_state={random_state})...")
    model = IsolationForest(
        contamination=contamination,
        random_state=random_state,
        n_estimators=100,
        n_jobs=-1
    )
    model.fit(X)

    # In-sample evaluation
    train_predictions = model.predict(X)
    anomaly_indices = np.where(train_predictions == -1)[0]
    total_anomalies = len(anomaly_indices)
    anomaly_ratio = total_anomalies / valid_count
    
    anomalous_powers = clean_series.iloc[anomaly_indices]
    min_anom = float(anomalous_powers.min()) if not anomalous_powers.empty else 0.0
    max_anom = float(anomalous_powers.max()) if not anomalous_powers.empty else 0.0
    mean_normal = float(clean_series.iloc[np.where(train_predictions == 1)[0]].mean())

    logger.info(f"Training completed. Detected {total_anomalies} anomalies ({anomaly_ratio:.2%}) in historical set.")
    logger.info(f"Normal mean power: {mean_normal:.3f} kW | Anomalous power range: [{min_anom:.3f} kW, {max_anom:.3f} kW]")

    # Persist the model artifact
    joblib.dump(model, model_output_path)
    logger.info(f"Saved trained IsolationForest model artifact to: {model_output_path}")

    # Generate metadata
    metadata = {
        "model_type": "IsolationForest",
        "algorithm": "sklearn.ensemble.IsolationForest",
        "features": [target_column],
        "contamination": contamination,
        "random_state": random_state,
        "n_estimators": 100,
        "trained_at": datetime.now().isoformat(),
        "total_training_samples": valid_count,
        "training_anomalies_detected": int(total_anomalies),
        "anomaly_percentage": round(float(anomaly_ratio * 100), 2),
        "normal_mean_power_kw": round(mean_normal, 4),
        "anomaly_min_power_kw": round(min_anom, 4),
        "anomaly_max_power_kw": round(max_anom, 4),
        "decision_threshold_offset": float(model.offset_)
    }

    with open(metadata_output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
    logger.info(f"Saved model training metadata to: {metadata_output_path}")

    return model, metadata

if __name__ == "__main__":
    train_anomaly_model()
