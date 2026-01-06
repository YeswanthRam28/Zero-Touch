"""Tests for `backend.voice`.

These tests avoid requiring a microphone by using `force_stub=True` and by
validating the result shape and types.
"""
import time
from backend.voice import get_voice_output


def test_stub():
    out = get_voice_output(force_stub=True)
    assert isinstance(out, dict)
    assert "transcript" in out
    assert "intent" in out
    assert "confidence" in out
    assert "timestamp" in out
    assert out["transcript"] == ""
    assert out["intent"] == "UNKNOWN"
    assert out["confidence"] == 0.0
    assert abs(out["timestamp"] - time.time()) < 5


if __name__ == "__main__":
    test_stub()
    print("test_stub passed")
