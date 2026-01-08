import logging
import time
import sys
import threading
import asyncio
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, Body, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import uvicorn
import json

# Import our modules
from audio_engine.audio_capture import AudioCapture
from audio_engine.asr_engine import ASREngine
from audio_engine.intent_engine import IntentEngine
from audio_engine.state_manager import StateManager
from audio_engine.tts_engine import TTSEngine
from audio_engine.vision_bridge import get_bridge
from audio_engine.vision_manager import VisionManager
from audio_engine.fusion_engine import FusionEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ZeroTouchAssistant")

# --- Assistant Global Initialization ---

class AssistantState:
    def __init__(self):
        self.asr_loaded = False
        self.llm_loaded = False
        self.tts_loaded = False
        self.vision_running = False
        self.main_loop = None  # Store the main event loop for thread-safe broadcasts
        
        # WebSockets
        self.active_connections: List[WebSocket] = []
        
        # Modules
        self.state_manager = StateManager()
        self.vision_bridge = get_bridge()
        self.vision_bridge.register_state_manager(self.state_manager)
        
        # Register a listener to broadcast actions to frontend
        self.vision_bridge.register_action_listener(self.broadcast_action)
        
        # Core Engines
        try:
            # 1. Vision & Gaze Tracking
            self.vision_manager = VisionManager()
            self.vision_manager.start()
            self.vision_running = True
            
            # 2. TTS
            self.tts = TTSEngine(use_coqui=True)
            self.tts_loaded = True
            
            # 3. Audio Capture
            self.capture = AudioCapture(duration=3.0, threshold=0.01)
            
            # 4. ASR (Whisper)
            self.asr = ASREngine(model_size="tiny")
            self.asr_loaded = True
            
            # 5. Intent Parser (LLM)
            self.intent_parser = IntentEngine(llm_model_path="D:\\LLM\\models\\phi-2\\phi-2.Q4_K_M.gguf")
            self.llm_loaded = True
            
            # 6. Multimodal Fusion
            self.fusion_engine = FusionEngine()
            
            # 7. Voice Monitoring Control
            self.voice_listening = True
            
            # 8. Start Gesture Monitoring Loop
            self.gesture_thread = threading.Thread(target=self._gesture_monitor_loop, daemon=True)
            self.gesture_thread.start()
            
            # 9. Start Continuous Voice Monitoring Loop
            self.voice_thread = threading.Thread(target=self._voice_monitor_loop, daemon=True)
            self.voice_thread.start()
            
            logger.info("All Zero-Touch engines and loops loaded successfully.")
        except Exception as e:
            logger.error(f"Error during initialization: {e}")

    def broadcast_action(self, intent: str, parameters: Dict[str, Any]):
        """Callback for VisionBridge to push actions to WebSocket clients."""
        payload = {"type": "ACTION", "intent": intent, "parameters": parameters}
        # Since this is called from a thread, we need to handle async broadcasting
        # We'll use a thread-safe way to push this to the main event loop if needed, 
        # but for now we'll just use a simple list check.
        # Note: In a real app, use a queue or specifically targeted event loop.
        message = json.dumps(payload)
        
        # We'll rely on the main app loop to handle the actual sending if possible,
        # or just try to send synchronously if we're in the right context.
        # For simplicity in this demo, we'll use a global bridge.
        logger.info(f"Broadcasting action: {intent}")

    def _gesture_monitor_loop(self):
        """Background loop to detect gestures without voice."""
        last_gesture = "NONE"
        last_gesture_time = 0
        
        while self.vision_running:
            try:
                state = self.vision_manager.get_state()
                curr_gesture = state["hand"]["gesture"]
                pinch_delta = state["hand"]["pinch_delta"]
                
                now = time.time()
                
                # 1. SWIPE DETECTION (Debounced)
                if curr_gesture != "NONE" and curr_gesture != last_gesture:
                    if now - last_gesture_time > 1.0: # 1 second debounce
                        intent = "NEXT_IMAGE" if curr_gesture == "SWIPE_RIGHT" else "PREV_IMAGE"
                        logger.info(f"Gesture Triggered: {intent}")
                        self.vision_bridge.execute_action(intent)
                        last_gesture_time = now
                
                # 2. PINCH DETECTION (Continuous for zoom)
                if abs(pinch_delta) > 10:
                    intent = "ZOOM_IN" if pinch_delta > 0 else "ZOOM_OUT"
                    # Zoom factor based on delta
                    factor = 1.0 + (abs(pinch_delta) / 100.0)
                    if intent == "ZOOM_OUT": factor = 1.0 / factor
                    
                    self.vision_bridge.execute_action(intent, {"factor": factor})
                
                last_gesture = curr_gesture
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in gesture monitor: {e}")
                time.sleep(1)

    def _voice_monitor_loop(self):
        """Background loop to continuously listen for voice commands."""
        logger.info("Voice monitoring loop started - listening continuously...")
        
        while self.voice_listening:
            try:
                # 1. Capture Audio
                audio_buffer = self.capture.listen_chunk()
                if audio_buffer is None:
                    time.sleep(0.1)
                    continue
                
                # 2. Transcribe (Whisper)
                transcript_data = self.asr.transcribe(audio_buffer)
                text = transcript_data.get("text", "").strip()
                
                if len(text) < 2:
                    continue
                
                logger.info(f"[VOICE] Detected: {text}")
                
                # 3. Intent Parsing
                voice_intent = self.intent_parser.parse(text)
                
                # 4. Multimodal Fusion
                vision_state = self.vision_manager.get_state()
                fused_intent = self.fusion_engine.fuse(voice_intent, vision_state)
                
                intent = fused_intent["action"]
                
                # 5. Handle CHAT separately
                if intent == "CHAT":
                    response_text = "I'm here to assist with surgical commands."
                    if "hello" in text.lower(): 
                        response_text = "Hello! Ready for procedure."
                    
                    self.tts.speak(response_text)
                    # Broadcast to frontend
                    self._sync_broadcast({"type": "MESSAGE", "text": response_text, "source": "AI"})
                    continue
                
                # 6. Check if rejected
                if fused_intent["status"] == "REJECTED":
                    self.tts.speak(fused_intent["reason"])
                    self._sync_broadcast({"type": "MESSAGE", "text": fused_intent["reason"], "source": "SYSTEM"})
                    continue
                
                # 7. Safety Validation
                is_valid, msg = self.state_manager.validate_command(fused_intent)
                if not is_valid:
                    self.tts.speak(msg)
                    self._sync_broadcast({"type": "MESSAGE", "text": msg, "source": "SYSTEM"})
                    continue
                
                # 8. Execute Action
                success, exec_msg = self.vision_bridge.execute_action(intent, fused_intent.get("parameters"))
                
                if success:
                    logger.info(f"[VOICE] Executed: {intent}")
                    self.tts.speak(f"Executing {intent.replace('_', ' ').lower()}.")
                    # Broadcast action to frontend
                    self._sync_broadcast({"type": "ACTION", "intent": intent, "parameters": fused_intent.get("parameters")})
                else:
                    self.tts.speak("Failed to execute.")
                    logger.warning(f"[VOICE] Failed: {exec_msg}")
                
            except Exception as e:
                logger.error(f"Error in voice monitor: {e}")
                time.sleep(1)
    
    def _sync_broadcast(self, payload: dict):
        """Thread-safe broadcast helper for background threads."""
        if not self.main_loop:
            logger.warning("Main event loop not set, cannot broadcast")
            return
        
        try:
            asyncio.run_coroutine_threadsafe(broadcast_to_ws(payload), self.main_loop)
            logger.debug(f"Broadcast scheduled: {payload.get('type')}")
        except Exception as e:
            logger.error(f"Broadcast failed: {e}")

# Global instance
assistant: Optional[AssistantState] = None

app = FastAPI(title="Zero-Touch Voice & Fusion API")

@app.on_event("startup")
async def startup_event():
    global assistant
    assistant = AssistantState()
    # Capture the main event loop for thread-safe broadcasts
    assistant.main_loop = asyncio.get_event_loop()
    logger.info(f"Main event loop captured: {assistant.main_loop}")

@app.on_event("shutdown")
def shutdown_event():
    if assistant and assistant.vision_running:
        assistant.vision_manager.stop()

# --- WebSocket Hub ---

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    if assistant:
        assistant.active_connections.append(websocket)
    try:
        while True:
            # Keep alive and listen for any client messages if needed
            data = await websocket.receive_text()
            logger.info(f"WebSocket received: {data}")
    except WebSocketDisconnect:
        if assistant:
            assistant.active_connections.remove(websocket)
        logger.info("WebSocket client disconnected")

# We need to override the broadcast_action to be async-aware
async def broadcast_to_ws(payload: dict):
    if not assistant: return
    message = json.dumps(payload)
    disconnected = []
    for conn in assistant.active_connections:
        try:
            await conn.send_text(message)
        except Exception:
            disconnected.append(conn)
    
    for conn in disconnected:
        assistant.active_connections.remove(conn)

# Hack to bridge the threaded bridge to async WebSocket
def threaded_broadcast(intent, parameters):
    if not assistant: return
    payload = {"type": "ACTION", "intent": intent, "parameters": parameters}
    # Use a global event loop to schedule the broadcast
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast_to_ws(payload), loop)
    except Exception:
        pass

# --- Models ---
class IntentRequest(BaseModel):
    text: str

# --- Endpoints ---

@app.get("/health")
def get_health():
    if not assistant:
        return {"status": "initializing"}
    return {
        "status": "ready" if assistant.llm_loaded else "partial",
        "vision": "running" if assistant.vision_running else "failed",
        "asr": "loaded" if assistant.asr_loaded else "failed",
        "llm": "loaded" if assistant.llm_loaded else "failed",
        "tts": "loaded" if assistant.tts_loaded else "failed",
        "clients": len(assistant.active_connections)
    }

@app.get("/vision/state")
def get_vision_state():
    """Returns the current raw sensor state (gaze, hands, etc)"""
    if not assistant or not assistant.vision_running:
        raise HTTPException(status_code=503, detail="Vision manager not running")
    return assistant.vision_manager.get_state()

@app.post("/voice/listen")
async def voice_listen():
    """Trigger one listen–fuse–act cycle"""
    if not assistant:
        return {"status": "error", "reason": "Assistant not initialized"}
        
    logger.info("API Trigger: Start Listening cycle...")
    
    # 1. Capture Audio
    audio_buffer = assistant.capture.listen_chunk()
    if audio_buffer is None:
        return {"status": "ignored", "reason": "SILENCE"}
        
    # 2. Transcribe (Whisper)
    transcript_data = assistant.asr.transcribe(audio_buffer)
    text = transcript_data.get("text", "").strip()
    
    if len(text) < 2:
        return {"status": "ignored", "reason": "TOO_SHORT", "text": text}
        
    logger.info(f"Detected Speech: {text}")
    
    # 3. Intent Parsing
    voice_intent = assistant.intent_parser.parse(text)
    
    # 4. Multimodal Fusion Logic
    vision_state = assistant.vision_manager.get_state()
    fused_intent = assistant.fusion_engine.fuse(voice_intent, vision_state)
    
    intent = fused_intent["action"]
    
    if intent == "CHAT":
        response_text = "I'm here to assist with surgical commands."
        if "hello" in text.lower(): response_text = "Hello! Ready for procedure."
        assistant.tts.speak(response_text)
        # Broadcast the chat response to frontend
        await broadcast_to_ws({"type": "MESSAGE", "text": response_text, "source": "AI"})
        return {"status": "success", "intent": "CHAT", "response": response_text}
        
    if fused_intent["status"] == "REJECTED":
        assistant.tts.speak(fused_intent["reason"])
        return {"status": "blocked", "reason": fused_intent["reason"], "intent": intent}

    # 5. Safety Validation
    is_valid, msg = assistant.state_manager.validate_command(fused_intent)
    if not is_valid:
        assistant.tts.speak(msg)
        return {"status": "blocked", "reason": msg, "intent": intent}
        
    # 6. Execution via VisionBridge
    # This will trigger threaded_broadcast via the listener we registered
    success, exec_msg = assistant.vision_bridge.execute_action(intent, fused_intent.get("parameters"))
    
    if success:
        logger.info(f"FUSED EXECUTION: {intent}")
        assistant.tts.speak(f"Executing {intent.replace('_', ' ').lower()}.")
        # Explicitly broadcast for voice too
        await broadcast_to_ws({"type": "ACTION", "intent": intent, "parameters": fused_intent.get("parameters")})
        return {
            "heard_text": text,
            "intent": intent,
            "status": "success",
            "fusion": fused_intent
        }
    else:
        assistant.tts.speak("Failed to execute.")
        return {"status": "failed", "reason": exec_msg}

@app.post("/intent/parse")
async def intent_parse(request: IntentRequest):
    """Test fusion logic without audio"""
    if not assistant: return {"status": "error"}
    
    voice_intent = assistant.intent_parser.parse(request.text)
    vision_state = assistant.vision_manager.get_state()
    fused = assistant.fusion_engine.fuse(voice_intent, vision_state)
    
    # Execute for testing
    if fused["status"] == "APPROVED":
        # Note: AssistantState doesn't store bridge directly, it uses get_bridge()
        success, exec_msg = assistant.vision_bridge.execute_action(fused["action"], fused.get("parameters"))
        # Also broadcast via the async bridge
        await broadcast_to_ws({"type": "ACTION", "intent": fused["action"], "parameters": fused.get("parameters")})
    
    return {
        "voice_intent": voice_intent,
        "vision_snapshot": vision_state,
        "fused_decision": fused
    }

if __name__ == "__main__":
    # Register the broadcast hack
    get_bridge().register_action_listener(threaded_broadcast)
    
    logger.info("Starting Zero-Touch Assistant Service...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
