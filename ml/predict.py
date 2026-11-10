"""
Real-Time Machine Learning Inference Module.
Loads the persisted Isolation Forest model once at startup and performs low-latency scoring on incoming streaming events.
"""

import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging
from typing import Tuple, Optional
import numpy as np
import pandas as pd
import joblib
from config.settings import get_settings

logger = logging.getLogger(__name__)

class AnomalyDetector:
    """
    Inference engine that wraps the trained scikit-learn IsolationForest model.
    Loads once during startup and scores readings in microseconds.
    """
    def __init__(self, model_path: Optional[str] = None):
        settings = get_settings()
        self.model_path = model_path or settings.MODEL_PATH
        self.model = None
        self._load_model()

    def _load_model(self):
        """Loads the persisted joblib model artifact."""
        if not os.path.exists(self.model_path):
            logger.warning(f"Trained model artifact not found at '{self.model_path}'. Running in fallback mode.")
            self.model = None
            return

        try:
            self.model = joblib.load(self.model_path)
            logger.info(f"Successfully loaded IsolationForest model from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load model artifact from {self.model_path}: {e}")
            self.model = None

    def predict(self, power: float) -> Tuple[int, float]:
        """
        Scores a live power consumption reading.
        
        Returns:
            Tuple of (is_anomaly, anomaly_score):
            - is_anomaly: 1 if reading is flagged as an anomaly, 0 if normal.
            - anomaly_score: raw decision function score (negative values are more anomalous).
        """
        if self.model is None:
            # Fallback heuristic if model file is not present: flag powers > 6.0 kW as anomalous
            is_anomaly = 1 if power > 6.0 else 0
            return is_anomaly, -1.0 if is_anomaly else 0.5

        try:
            # Use DataFrame with identical feature name as fitted in training
            features = pd.DataFrame([[float(power)]], columns=["Global_active_power"])
            prediction = self.model.predict(features)[0]  # 1 = normal, -1 = anomaly
            score = float(self.model.decision_function(features)[0])
            
            is_anomaly = 1 if prediction == -1 else 0
            return is_anomaly, score
        except Exception as e:
            logger.error(f"Error during live inference on power value {power}: {e}")
            return 0, 0.0
