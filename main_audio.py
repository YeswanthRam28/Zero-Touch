import logging
import time
import sys
import threading
import asyncio
import re
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
from audio_engine.scribe import AIScribe
from fastapi.middleware.cors import CORSMiddleware
import sounddevice as sd
import cv2

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
        # Flags
        self.asr_loaded = False
        self.llm_loaded = False
        self.tts_loaded = False
        self.vision_running = False
        self.main_loop = None 
        self.active_connections: List[WebSocket] = []

        # Initialize attributes to None to avoid AttributeErrors if init fails
        self.vision_manager = None
        self.tts = None
        self.capture = None
        self.asr = None
        self.intent_parser = None
        self.fusion_engine = None
        self.voice_listening = False
        self.gesture_thread = None
        self.voice_thread = None

        # Modules
        self.state_manager = StateManager()
        self.vision_bridge = get_bridge()
        self.vision_bridge.register_state_manager(self.state_manager)
        self.vision_bridge.register_action_listener(self.broadcast_action)
        self.latest_dashboard_frame = None # Storage for incoming dashboard images

        # Core Engines
        try:
            # 1. Vision & Gaze Tracking
            self.vision_manager = VisionManager()
            self.vision_manager.start()
            self.vision_running = True
            
            # 2. TTS
            self.tts = TTSEngine(use_coqui=False)
            self.tts_loaded = True
            
            # 3. Audio Capture
            self.capture = AudioCapture(duration=5, threshold=0.005)
            
            # 4. ASR (Whisper)
            self.asr = ASREngine(model_size="tiny")
            self.asr_loaded = True
            
            # 5. Intent Parser (Ollama)
            self.intent_parser = IntentEngine(model_name="phi2-local")
            self.llm_loaded = True
            # Pre-warm vision model on startup
            threading.Thread(target=self.intent_parser.ensure_vision_model, daemon=True).start()
            
            # 6. Multimodal Fusion
            self.fusion_engine = FusionEngine()
            
            # 7. Voice Monitoring Control
            self.voice_listening = True
            
            # 8. AI Scribe
            self.scribe = AIScribe()
            
            # 9. Start Gesture Monitoring Loop
            self.gesture_thread = threading.Thread(target=self._gesture_monitor_loop, daemon=True)
            self.gesture_thread.start()
            
            # 10. Start Continuous Voice Monitoring Loop
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
        """Background loop to detect gestures based on static hand poses (One-shot)."""
        last_triggered_pose = "NONE"
        last_action_time = 0
        
        while self.vision_running:
            try:
                state = self.vision_manager.get_state()
                curr_pose = state["hand"].get("pose", "UNKNOWN")
                
                now = time.time()
                
                # Check for pose change to trigger action
                if curr_pose != last_triggered_pose:
                    intent = None
                    params = {}
                    
                    if curr_pose == "OPEN_PALM":
                        intent = "ZOOM_OUT"
                        params = {"factor": 1.4}
                    elif curr_pose == "L_SHAPE":
                        intent = "ZOOM_IN"
                        params = {"factor": 1.4}
                    elif curr_pose == "PINKY_POINTING":
                        intent = "NEXT_IMAGE"
                    elif curr_pose == "THUMB_POINTING":
                        intent = "PREV_IMAGE"
                    
                    # Only execute if it's a valid intent and we haven't triggered a different action too recently
                    if intent and (now - last_action_time > 1.0):
                        logger.info(f"Pose Triggered: {intent} from {curr_pose}")
                        self.vision_bridge.execute_action(intent, params)
                        self.state_manager.log_event("GESTURE_ACTION", {"intent": intent, "pose": curr_pose, "params": params})
                        last_action_time = now
                        last_triggered_pose = curr_pose
                
                # Reset trigger tracker if hand is closed or unknown
                if curr_pose in ["FIST", "UNKNOWN", "NONE"]:
                    last_triggered_pose = curr_pose

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
                
                if len(text) < 2 or re.match(r'^[ \.\,\?\!\-\_\...]+$', text):
                    continue
                
                # Filter noise/hallucinations
                if text.lower() in ["thank you.", "subtitles by", "thanks for watching"]:
                    continue
                
                logger.info(f"[VOICE] Detected: {text}")
                
                # 3. Intent Parsing
                voice_intent = self.intent_parser.parse(text)
                
                # 4. Multimodal Fusion
                vision_state = self.vision_manager.get_state()
                
                # Check Type (Blocking Clinical reasoning if Knowledge)
                intent_type = str(voice_intent.get("type", "NAVIGATION")).upper()
                if intent_type == "KNOWLEDGE":
                    # Strictly blocking "Think" phase as per user request for Q&A
                    logger.info("Knowledge query detected. Processing...")
                    answer = self.intent_parser.medical_query(text)
                    self._sync_broadcast({"type": "MESSAGE", "text": answer, "source": "AI"})
                    self.tts.speak(answer) # USER wanted this blocking for Q&A
                    self.state_manager.log_event("KNOWLEDGE_QUERY", {"query": text, "answer": answer})
                    continue

                fused_intent = self.fusion_engine.fuse(voice_intent, vision_state)
                intent = str(fused_intent["action"]).upper()

                # Handle Visual Analysis specifically
                if intent == "ANALYZE_REGION":
                    logger.info("Visual analysis request detected...")
                    threading.Thread(target=self.tts.speak, args=("Analyzing focus region...",), daemon=True).start()
                    
                    # 1. Fetch image from dashboard (via bridge)
                    # Note: This broadcasts "CAPTURE_IMAGE" to the frontend
                    self.latest_dashboard_frame = None # Reset
                    self.vision_bridge.execute_action("CAPTURE_IMAGE")
                    
                    # Wait for frame with timeout
                    start_wait = time.time()
                    while self.latest_dashboard_frame is None and (time.time() - start_wait < 5.0):
                        time.sleep(0.1)

                    if self.latest_dashboard_frame:
                        gaze_info = vision_state.get("gaze", {}).get("eye", "CENTER")
                        analysis = self.intent_parser.analyze_image(self.latest_dashboard_frame, text, gaze_info)
                        
                        self._sync_broadcast({"type": "MESSAGE", "text": analysis, "source": "AI"})
                        self.tts.speak(analysis)
                        self.state_manager.log_event("VISUAL_ANALYSIS", {"query": text, "gaze": gaze_info, "analysis": analysis})
                        continue
                    else:
                        msg = "Analysis failed: Timed out waiting for dashboard image."
                        logger.warning(msg)
                        self._sync_broadcast({"type": "MESSAGE", "text": msg, "source": "SYSTEM"})
                        self.tts.speak("I couldn't get the image from the dashboard.")
                        continue
                        
                # 5. Handle CHAT separately
                if intent == "CHAT" or intent_type == "CHAT":
                    response_text = "I'm here to assist with surgical commands."
                    if "hello" in text.lower(): 
                        response_text = "Hello! Ready for procedure."
                    
                    self._sync_broadcast({"type": "MESSAGE", "text": response_text, "source": "AI"})
                    threading.Thread(target=self.tts.speak, args=(response_text,), daemon=True).start()
                    self.state_manager.log_event("CHAT", {"text": text, "response": response_text})
                    continue
                
                # 6. Check if rejected
                if fused_intent["status"] == "REJECTED":
                    self._sync_broadcast({"type": "MESSAGE", "text": fused_intent["reason"], "source": "SYSTEM"})
                    threading.Thread(target=self.tts.speak, args=(fused_intent["reason"],), daemon=True).start()
                    continue
                
                # 7. Safety Validation
                is_valid, msg = self.state_manager.validate_command(fused_intent)
                if not is_valid:
                    self._sync_broadcast({"type": "MESSAGE", "text": msg, "source": "SYSTEM"})
                    threading.Thread(target=self.tts.speak, args=(msg,), daemon=True).start()
                    continue
                
                # 8. Execute Action
                success, exec_msg = self.vision_bridge.execute_action(intent, fused_intent.get("parameters"))
                
                if intent == "GENERATE_REPORT":
                    threading.Thread(target=self.tts.speak, args=("Ending session and generating surgical report.",), daemon=True).start()
                    logs = self.state_manager.get_event_logs()
                    summary = self.intent_parser.summarize_session(logs)
                    pdf_path = self.scribe.generate_report(summary, logs)
                    if pdf_path:
                        threading.Thread(target=self.tts.speak, args=("Report generated successfully.",), daemon=True).start()
                        self._sync_broadcast({"type": "MESSAGE", "text": f"Report saved: {pdf_path}", "source": "SYSTEM"})
                    continue

                if success:
                    logger.info(f"[VOICE] Executed: {intent}")
                    speak_text = f"Executing {intent.replace('_', ' ').lower()}."
                    threading.Thread(target=self.tts.speak, args=(speak_text,), daemon=True).start()
                    # Broadcast action to frontend
                    self._sync_broadcast({"type": "ACTION", "intent": intent, "parameters": fused_intent.get("parameters")})
                    self.state_manager.log_event("VOICE_ACTION", {"intent": intent, "text": text, "params": fused_intent.get("parameters")})
                else:
                    threading.Thread(target=self.tts.speak, args=("Failed to execute.",), daemon=True).start()
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    if not assistant or not assistant.main_loop: return
    payload = {"type": "ACTION", "intent": intent, "parameters": parameters}
    try:
        asyncio.run_coroutine_threadsafe(broadcast_to_ws(payload), assistant.main_loop)
        logger.info(f"WebSocket Broadcast: {intent}")
    except Exception as e:
        logger.error(f"Threaded broadcast failed: {e}")

# --- Models ---
class IntentRequest(BaseModel):
    text: str

# --- Endpoints ---

@app.post("/vision/upload_frame")
async def upload_frame(payload: dict = Body(...)):
    """Frontend uploads the requested frame here as base64."""
    if assistant:
        assistant.latest_dashboard_frame = payload.get("image")
        logger.info("New dashboard frame received.")
    return {"status": "success"}

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
    if not assistant or not assistant.vision_running or not assistant.vision_manager:
        raise HTTPException(status_code=503, detail="Vision manager not running")
    return assistant.vision_manager.get_state()

@app.post("/voice/listen")
async def voice_listen():
    """Trigger one listen–fuse–act cycle"""
    if not assistant or not assistant.intent_parser:
        return {"status": "error", "reason": "Assistant or Intent Parser not initialized"}
        
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
    if not assistant or not assistant.intent_parser: 
        return {"status": "error", "reason": "Intent parser not available"}
    
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

# --- Hardware Management ---

@app.get("/hardware/devices")
async def list_devices():
    """List available audio and video devices."""
    try:
        # Audio Devices
        devices = sd.query_devices()
        input_devices = []
        output_devices = []
        
        for i, d in enumerate(devices):
            dev_info = {
                "id": i,
                "name": d['name'],
                "channels": d['max_input_channels'] if d['max_input_channels'] > 0 else d['max_output_channels']
            }
            if d['max_input_channels'] > 0:
                input_devices.append(dev_info)
            if d['max_output_channels'] > 0:
                output_devices.append(dev_info)
                
        # Camera Devices (Scan first 5 indices)
        cameras = []
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                cameras.append({"id": i, "name": f"Camera {i}"})
                cap.release()
                
        return {
            "microphones": input_devices,
            "speakers": output_devices,
            "cameras": cameras
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class DeviceSelection(BaseModel):
    type: str # 'microphone', 'speaker', 'camera'
    id: int

@app.post("/hardware/select")
async def select_device(selection: DeviceSelection):
    """Switch the active hardware device."""
    if not assistant:
        raise HTTPException(status_code=503, detail="Assistant not ready")
        
    try:
        if selection.type == 'microphone':
            assistant.capture.set_device(selection.id)
            return {"status": "success", "message": f"Microphone switched to {selection.id}"}
        elif selection.type == 'speaker':
            assistant.tts.set_device(selection.id)
            return {"status": "success", "message": f"Speaker switched to {selection.id}"}
        elif selection.type == 'camera':
            assistant.vision_manager.switch_camera(selection.id)
            return {"status": "success", "message": f"Camera switched to {selection.id}"}
        else:
            raise HTTPException(status_code=400, detail="Invalid device type")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session/end")
async def end_session():
    """Summarize session and generate PDF report"""
    if not assistant:
        return {"status": "error", "message": "Assistant not initialized"}
    
    logs = assistant.state_manager.get_event_logs()
    if not logs:
        return {"status": "ignored", "message": "No events recorded"}
    
    # 1. Summarize via LLM
    summary = assistant.intent_parser.summarize_session(logs)
    
    # 2. Generate PDF
    pdf_path = assistant.scribe.generate_report(summary, logs)
    
    if pdf_path:
        return {
            "status": "success", 
            "report_path": pdf_path,
            "summary": summary
        }
    else:
        return {"status": "error", "message": "Failed to generate report"}

if __name__ == "__main__":
    # Register the broadcast hack
    get_bridge().register_action_listener(threaded_broadcast)
    
    logger.info("Starting Zero-Touch Assistant Service...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
