"""
Stream Processor Metrics Module.
Maintains stateful rolling window calculations, running peak, cumulative energy, and processing counters.
"""

from collections import deque
from datetime import datetime
from typing import Dict, Any, Optional

class StreamMetricsCalculator:
    """
    Stateful streaming aggregator.
    Maintains a sliding window of the latest N readings (default: 30)
    and computes rolling averages, peaks, and energy consumption.
    """
    def __init__(
        self,
        window_size: int = 30,
        initial_peak: float = 0.0,
        initial_energy_kwh: float = 0.0,
        initial_readings_count: int = 0,
        initial_anomalies_count: int = 0
    ):
        self.window_size = window_size
        self.window = deque(maxlen=window_size)
        self.running_peak = float(initial_peak)
        self.total_energy_kwh = float(initial_energy_kwh)
        self.total_readings = int(initial_readings_count)
        self.total_anomalies = int(initial_anomalies_count)
        self.min_power: Optional[float] = None
        self.sum_all_power: float = 0.0

    def update(self, power: float, is_anomaly: int = 0, reading_time: Optional[str] = None) -> Dict[str, Any]:
        """
        Updates internal window and metrics with a newly arrived power reading.
        
        Args:
            power: Household global active power in kW.
            is_anomaly: 1 if flagged as an anomaly, 0 if normal.
            reading_time: ISO string timestamp.
            
        Returns:
            Dictionary containing updated streaming metrics.
        """
        power = float(power)
        
        # 1. Update sliding window
        self.window.append(power)
        
        # 2. Compute 30-reading rolling average
        rolling_avg = sum(self.window) / len(self.window) if self.window else 0.0
        
        # 3. Update running peak
        if power > self.running_peak:
            self.running_peak = power
            
        # 4. Update running min power
        if self.min_power is None or power < self.min_power:
            self.min_power = power

        # 5. Update cumulative energy in kWh (Power in kW * 1/60 hr per minute)
        # Formula: Energy (kWh) = Sum of per-minute kW / 60
        self.total_energy_kwh += (power / 60.0)
        
        # 6. Increment counters
        self.total_readings += 1
        self.sum_all_power += power
        if is_anomaly:
            self.total_anomalies += 1

        cumulative_avg = self.sum_all_power / self.total_readings if self.total_readings > 0 else 0.0

        return {
            "current_power": round(power, 3),
            "rolling_avg_30": round(rolling_avg, 3),
            "running_peak": round(self.running_peak, 3),
            "total_energy_kwh": round(self.total_energy_kwh, 4),
            "total_readings": self.total_readings,
            "total_anomalies": self.total_anomalies,
            "cumulative_avg": round(cumulative_avg, 3),
            "min_power": round(self.min_power, 3) if self.min_power is not None else 0.0,
            "window_fill": len(self.window),
            "last_updated": reading_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def get_snapshot(self) -> Dict[str, Any]:
        """Returns the current state snapshot."""
        current_val = self.window[-1] if self.window else 0.0
        rolling_avg = sum(self.window) / len(self.window) if self.window else 0.0
        return {
            "current_power": round(current_val, 3),
            "rolling_avg_30": round(rolling_avg, 3),
            "running_peak": round(self.running_peak, 3),
            "total_energy_kwh": round(self.total_energy_kwh, 4),
            "total_readings": self.total_readings,
            "total_anomalies": self.total_anomalies,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def reset(self):
        """Resets sliding window and all running counters to zero for live demo resets."""
        self.window.clear()
        self.running_peak = 0.0
        self.total_energy_kwh = 0.0
        self.total_readings = 0
        self.total_anomalies = 0
        self.min_power = None
        self.sum_all_power = 0.0
