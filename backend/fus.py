"""Fusion logic for vision + voice inputs.

Provides a single `fuse(vision, voice, ...)` function that normalizes
inputs, applies time alignment, weighted confidence scoring and
decision rules. Designed to be deterministic and easily testable.
"""
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


def _normalize_vision(vision: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "object": vision.get("object") or vision.get("object_detected"),
        "confidence": float(vision.get("confidence", 0.0)),
        "timestamp": float(vision.get("timestamp", 0.0)),
    }


def _normalize_voice(voice: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "transcript": voice.get("transcript", ""),
        "intent": voice.get("intent", "UNKNOWN"),
        "confidence": float(voice.get("confidence", 0.0)),
        "timestamp": float(voice.get("timestamp", 0.0)),
    }


def fuse(
    vision: Dict[str, Any],
    voice: Dict[str, Any],
    *,
    time_tolerance: float = 1.0,
    vision_weight: float = 0.6,
    voice_weight: float = 0.4,
    score_threshold: float = 0.8,
) -> Dict[str, Any]:
    """Fuse `vision` and `voice` packets and return a decision packet.

    Args:
        vision: dict-like with keys like `object`/`object_detected`,
            `confidence`, `timestamp`.
        voice: dict-like with keys `intent`, `transcript`, `confidence`,
            `timestamp`.
        time_tolerance: seconds allowed between timestamps.
        vision_weight: weight for vision confidence (0-1).
        voice_weight: weight for voice confidence (0-1).
        score_threshold: threshold above which allow action.

    Returns:
        Decision dict with `action`, plus optional `status` and `reason`.
    """
    v = _normalize_vision(vision or {})
    vo = _normalize_voice(voice or {})

    logger.debug("Normalized vision: %s", v)
    logger.debug("Normalized voice: %s", vo)

    # 1. Time alignment check
    if abs(v["timestamp"] - vo["timestamp"]) > time_tolerance:
        return {"action": "IGNORE", "reason": "Out of sync"}

    # 2. Weighted confidence (clamp weights)
    total = vision_weight + voice_weight
    if total <= 0:
        vision_w = 0.6
        voice_w = 0.4
    else:
        vision_w = vision_weight / total
        voice_w = voice_weight / total

    final_score = vision_w * v["confidence"] + voice_w * vo["confidence"]

    # 3. Decision rules — map voice transcripts to canonical actions
    def _voice_to_action(transcript: str):
        t = (transcript or "").lower()
        if 'open patient' in t or 'patient file' in t:
            return 'OPEN_PATIENT_FILE'
        if 'show ct' in t or ('ct' in t and 'scan' in t):
            return 'SHOW_CT_SCAN'
        if 'zoom in' in t:
            return 'ZOOM_IN'
        if 'zoom out' in t:
            return 'ZOOM_OUT'
        if 'reset view' in t or t.strip() == 'reset' or 'reset' in t:
            return 'RESET_VIEW'
        if 'highlight' in t or 'abnormal' in t:
            return 'HIGHLIGHT_ABNORMALITIES'
        if 'analyze' in t or 'what am i looking' in t:
            return 'ANALYZE_REGION'
        if 'compare' in t or 'compare with' in t or 'side-by-side' in t:
            return 'COMPARE_WITH_PREOP'
        return None

    if v.get("object") == "person" and vo.get("intent") == "COMMAND" and final_score > score_threshold:
        action = _voice_to_action(vo.get("transcript", ""))
        if action:
            return {
                "action": action,
                "status": "APPROVED",
                "reason": f"Person present + command ({action})",
                "score": final_score,
            }
        # Fallback to legacy demo behavior if transcript contains 'open'
        if 'open' in vo.get("transcript", "").lower():
            return {
                "action": "OPEN_DOOR",
                "status": "APPROVED",
                "reason": "Person present + command (fallback OPEN_DOOR)",
                "score": final_score,
            }

    return {"action": "NONE", "status": "REJECTED", "reason": "Condition not met", "score": final_score}


def compose_multimodal_action(transcript: str, gaze=None, gesture=None):
    """Compose a precise region action name when a gaze coordinate and a region-oriented voice command is present.

    Example output: 'ZOOM_REGION_450_320' for gaze (450,320) and transcript 'zoom here'.
    """
    t = (transcript or "").lower()
    if gaze and isinstance(gaze, (list, tuple)) and len(gaze) >= 2:
        x, y = int(round(gaze[0])), int(round(gaze[1]))
        if 'zoom' in t:
            return f"ZOOM_REGION_{x}_{y}"
        if 'highlight' in t or 'mark' in t:
            return f"HIGHLIGHT_REGION_{x}_{y}"
        if 'analyze' in t or 'what am i looking' in t:
            return f"ANALYZE_REGION_{x}_{y}"
    return None

__all__ = ["fuse", "compose_multimodal_action"]
