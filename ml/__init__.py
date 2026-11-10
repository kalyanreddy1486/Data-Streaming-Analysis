"""
Machine learning package for offline training and real-time anomaly inference.
"""
from .train_model import train_anomaly_model
from .predict import AnomalyDetector

__all__ = ["train_anomaly_model", "AnomalyDetector"]
