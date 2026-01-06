"""Simple vision interface for the backend.

Provides `get_vision_output()` so `backend/app.py` can import `vision`.
This is a lightweight stub returning a safe default for development.
"""
import time
from typing import Dict


def get_vision_output() -> Dict:
    """Return a minimal vision output packet.

    Fields align with `backend/fus.py` expectations:
    - object: detected object label
    - confidence: float in [0.0, 1.0]
    - timestamp: unix epoch seconds (float)
    """
    return {
        "object": "person",
        "confidence": 0.9,
        "timestamp": time.time(),
    }


__all__ = ["get_vision_output"]
