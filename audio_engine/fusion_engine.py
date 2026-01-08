import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("FusionEngine")

class FusionEngine:
    """
    Multimodal Fusion: Combines synchronous voice intents with asynchronous vision state.
    Resolves ambiguities like 'this', 'here', and aligns gestures with speech.
    """
    def __init__(self):
        self.context = {
            "current_patient": "John Doe",
            "active_modality": "CT SCAN",
            "last_action": None,
            "last_target": None
        }

    def fuse(self, voice_intent: Dict[str, Any], vision_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Produce a fused 'Factual Intent' packet.
        """
        intent = voice_intent.get("intent", "UNKNOWN")
        target = voice_intent.get("target", "NONE")
        
        fused_packet = {
            "action": intent,
            "status": "APPROVED",
            "reason": "Clear intent detected",
            "confidence": voice_intent.get("confidence", 0.0),
            "parameters": {},
            "timestamp": time.time()
        }

        # 1. Spatial Resolution (Gaze/Point)
        # If the user says "here" or "this", or uses a specific command that needs a target
        needs_target = target in ["HERE", "THIS", "GAZE_REGION", "SELECTED_REGION"]
        
        if needs_target:
            if vision_state.get("user_present"):
                # Use Gaze if no specific pointing gesture
                gaze_eye = vision_state["gaze"]["eye"]
                gaze_head = vision_state["gaze"]["head"]
                
                # Simple mapping of gaze to region
                region = "CENTER"
                if gaze_eye == "LEFT" or gaze_head == "LEFT": region = "LEFT_REGION"
                elif gaze_eye == "RIGHT" or gaze_head == "RIGHT": region = "RIGHT_REGION"
                
                fused_packet["parameters"]["region"] = region
                fused_packet["reason"] = f"Action bound to {region} via Gaze"
            else:
                fused_packet["status"] = "REJECTED"
                fused_packet["reason"] = "Target required but no user/gaze detected"

        # 2. Gesture Alignment
        # If a gesture matches the intent, or if the gesture ALONE should trigger something
        current_gesture = vision_state["hand"]["gesture"]
        current_pose = vision_state["hand"]["pose"]

        if intent == "ZOOM_IN" and vision_state["hand"]["pinch_delta"] > 5:
            fused_packet["reason"] += " (Reinforced by Pinch)"
            fused_packet["confidence"] = min(1.0, fused_packet["confidence"] + 0.1)

        # 3. Handle specific compound actions
        if intent == "HIGHLIGHT":
            fused_packet["action"] = "HIGHLIGHT_REGION"
            fused_packet["parameters"]["coordinates"] = vision_state["hand"]["cursor"]
            fused_packet["reason"] = "Highlighting region indicated by hand"

        # 4. Contextual lookup
        if intent == "PREVIOUS_PATIENT":
            fused_packet["parameters"]["target_patient"] = "Jane Smith" # Example context
            
        return fused_packet

    def update_context(self, key: str, value: Any):
        self.context[key] = value
