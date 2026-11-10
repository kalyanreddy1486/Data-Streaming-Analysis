"""
Unit tests for Machine Learning Layer (train_model.py, predict.py).
Tests Isolation Forest offline training, model persistence, loading, and live anomaly scoring.
"""

import os
import pytest
from ml.train_model import train_anomaly_model
from ml.predict import AnomalyDetector

def test_ml_model_training_and_persistence(tmp_path):
    model_path = str(tmp_path / "test_model.pkl")
    meta_path = str(tmp_path / "test_meta.json")

    model, meta = train_anomaly_model(
        dataset_path="data/sample_data.csv",
        model_output_path=model_path,
        metadata_output_path=meta_path,
        contamination=0.01,
        random_state=42
    )

    assert os.path.exists(model_path)
    assert os.path.exists(meta_path)
    assert meta["model_type"] == "IsolationForest"
    assert meta["total_training_samples"] > 0

def test_ml_live_inference():
    # Use existing persisted model
    detector = AnomalyDetector(model_path="ml/anomaly_model.pkl")
    
    # Normal low/typical power consumption reading
    is_anomaly_normal, score_normal = detector.predict(1.5)
    assert is_anomaly_normal == 0

    # Extreme power spike reading (> 8 kW)
    is_anomaly_spike, score_spike = detector.predict(8.5)
    assert is_anomaly_spike == 1
    assert score_spike < score_normal
