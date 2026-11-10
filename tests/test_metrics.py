"""
Unit tests for Stream Processing Metrics (metrics.py).
Tests sliding window, rolling average, running peak, and energy calculation.
"""

import pytest
from processor.metrics import StreamMetricsCalculator

def test_metrics_sliding_window_rolling_average():
    calc = StreamMetricsCalculator(window_size=3)
    
    # 1st reading: 3.0 -> window [3.0] -> avg = 3.0
    s1 = calc.update(3.0)
    assert s1["rolling_avg_30"] == 3.0
    assert s1["window_fill"] == 1

    # 2nd reading: 5.0 -> window [3.0, 5.0] -> avg = 4.0
    s2 = calc.update(5.0)
    assert s2["rolling_avg_30"] == 4.0
    assert s2["window_fill"] == 2

    # 3rd reading: 7.0 -> window [3.0, 5.0, 7.0] -> avg = 5.0
    s3 = calc.update(7.0)
    assert s3["rolling_avg_30"] == 5.0
    assert s3["window_fill"] == 3

    # 4th reading: 9.0 -> window [5.0, 7.0, 9.0] (3.0 dropped) -> avg = 7.0
    s4 = calc.update(9.0)
    assert s4["rolling_avg_30"] == 7.0
    assert s4["window_fill"] == 3

def test_metrics_running_peak():
    calc = StreamMetricsCalculator(window_size=10)
    calc.update(2.5)
    calc.update(4.8)
    calc.update(1.2)
    s = calc.update(3.9)
    assert s["running_peak"] == 4.8

def test_metrics_energy_calculation():
    # Energy in kWh = sum(power in kW) / 60
    calc = StreamMetricsCalculator(window_size=30)
    # 60 readings of 2.0 kW should equal exactly 2.0 kWh
    for _ in range(60):
        s = calc.update(2.0)
    assert round(s["total_energy_kwh"], 2) == 2.00
    assert s["total_readings"] == 60
