"""Voice interface for the backend.

This module attempts to use the local `audio_engine` pipeline (capture ->
ASR -> intent) to produce a `get_voice_output()` packet compatible with
`backend/fus.fuse`. If the audio stack or hardware is unavailable, a
safe stub result is returned (or forced via `force_stub=True`).
"""
import time
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Lazy imports / singletons
_asr = None
_intent_engine = None
_capture = None


def _init_audio_stack():
    global _asr, _intent_engine, _capture
    if _asr is not None and _intent_engine is not None and _capture is not None:
        return
    try:
        from audio_engine.asr_engine import ASREngine
        from audio_engine.intent_engine import IntentEngine
        from audio_engine.audio_capture import AudioCapture
    except Exception as e:
        logger.info("audio_engine not available: %s", e)
        _asr = _intent_engine = _capture = None
        return

    # Initialize with safe defaults; these may be heavy but are lazily created
    try:
        _asr = ASREngine()
    except Exception as e:
        logger.warning("Failed to init ASR engine: %s", e)
        _asr = None

    try:
        _intent_engine = IntentEngine()
    except Exception as e:
        logger.warning("Failed to init Intent engine: %s", e)
        _intent_engine = None

    try:
        _capture = AudioCapture()
    except Exception as e:
        logger.warning("Failed to init AudioCapture: %s", e)
        _capture = None


def _stub_voice_output() -> Dict[str, Any]:
    return {
        "transcript": "",
        "intent": "UNKNOWN",
        "confidence": 0.0,
        "timestamp": time.time(),
    }


def get_voice_output(force_stub: bool = False, duration: float = 2.0) -> Dict[str, Any]:
    """Return a voice packet, using real audio pipeline when available.

    Args:
        force_stub: if True, skip audio pipeline and return a stub result.
        duration: seconds of audio to capture (only used if audio stack present).

    Returns:
        dict with keys: `transcript`, `intent`, `confidence`, `timestamp`.
    """
    if force_stub:
        return _stub_voice_output()

    _init_audio_stack()

    if _capture is None or _asr is None or _intent_engine is None:
        # Missing components -> fallback
        return _stub_voice_output()

    # Try to capture a short chunk
    try:
        # Allow temporary override of duration if AudioCapture supports it
        _capture.duration = duration
        audio = _capture.listen_chunk()
    except Exception as e:
        logger.error("Audio capture failed: %s", e)
        return _stub_voice_output()

    if audio is None:
        # Silence or capture failure
        return _stub_voice_output()

    # Transcribe
    try:
        asr_result = _asr.transcribe(audio)
        transcript = asr_result.get("text", "").strip()
        asr_conf = float(asr_result.get("confidence", 0.0))
    except Exception as e:
        logger.error("ASR transcribe failed: %s", e)
        return _stub_voice_output()

    # Intent parsing
    try:
        intent_pkt = _intent_engine.parse(transcript)
        intent = intent_pkt.get("intent", "UNKNOWN")
        intent_conf = float(intent_pkt.get("confidence", 0.0))
    except Exception as e:
        logger.error("Intent parse failed: %s", e)
        intent = "UNKNOWN"
        intent_conf = 0.0

    # Combine confidences (simple average)
    combined_conf = (asr_conf + intent_conf) / 2.0

    return {
        "transcript": transcript,
        "intent": intent,
        "confidence": combined_conf,
        "timestamp": time.time(),
    }


__all__ = ["get_voice_output"]
