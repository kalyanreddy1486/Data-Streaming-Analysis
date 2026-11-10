"""
Centralized Streaming & Live Demo Inter-Process Controller.
Coordinates real-time controls between the Streamlit Dashboard, Kafka Producer,
and Stream Processor via atomic file-based state synchronization.
"""

import os
import json
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

STATE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "stream_state.json"))

DEFAULT_STATE: Dict[str, Any] = {
    "is_streaming": True,
    "replay_delay": 0.20,
    "reset_requested": False,
    "reset_counter": 0,
    "last_updated": time.time()
}

def get_stream_state() -> Dict[str, Any]:
    """Reads current streaming control state."""
    if not os.path.exists(STATE_FILE):
        save_stream_state(DEFAULT_STATE)
        return dict(DEFAULT_STATE)
    
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure all default keys exist
            for k, v in DEFAULT_STATE.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception as e:
        logger.warning(f"Error reading stream state: {e}. Using defaults.")
        return dict(DEFAULT_STATE)

def save_stream_state(state: Dict[str, Any]) -> bool:
    """Safely saves stream state to disk using atomic write."""
    try:
        state["last_updated"] = time.time()
        temp_file = STATE_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        os.replace(temp_file, STATE_FILE)
        return True
    except Exception as e:
        logger.error(f"Error saving stream state: {e}")
        return False

def set_stream_active(active: bool) -> bool:
    """Sets whether the producer stream is running (True) or paused (False)."""
    state = get_stream_state()
    state["is_streaming"] = bool(active)
    logger.info(f"Stream active state updated: {state['is_streaming']}")
    return save_stream_state(state)

def set_replay_delay(delay_sec: float) -> bool:
    """Updates the pacing delay per reading in seconds."""
    state = get_stream_state()
    state["replay_delay"] = max(0.01, float(delay_sec))
    return save_stream_state(state)

def is_stream_active() -> bool:
    """Checks if streaming is currently enabled."""
    return bool(get_stream_state().get("is_streaming", True))

def get_replay_delay() -> float:
    """Returns current pacing delay."""
    return float(get_stream_state().get("replay_delay", 0.20))

def request_demo_reset() -> bool:
    """
    Triggers a full demo reset:
    1. Truncates MySQL tables and zeroes meter_metrics
    2. Signals stream processor to reset in-memory sliding window and counters
    3. Signals producer to restart from record 0
    """
    from database.db_initializer import reset_database
    db_reset = reset_database()
    
    state = get_stream_state()
    state["reset_requested"] = False
    state["reset_counter"] = state.get("reset_counter", 0) + 1
    save_stream_state(state)
    logger.info("Demo reset requested across all pipeline tiers.")
    return db_reset

def check_and_clear_reset() -> bool:
    """
    Checked by stream processor and producer:
    If a reset was requested, returns True and clears the flag.
    """
    state = get_stream_state()
    if state.get("reset_requested", False):
        state["reset_requested"] = False
        save_stream_state(state)
        return True
    return False

def get_reset_counter() -> int:
    """Returns the current reset counter version."""
    return int(get_stream_state().get("reset_counter", 0))
