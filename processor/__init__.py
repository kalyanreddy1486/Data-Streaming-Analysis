"""
Stream processing package for windowed computations and Kafka consumption.
"""
from .metrics import StreamMetricsCalculator
from .kafka_consumer import SmartMeterConsumer
from .stream_processor import StreamProcessor

__all__ = ["StreamMetricsCalculator", "SmartMeterConsumer", "StreamProcessor"]
