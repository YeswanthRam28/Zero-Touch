
import logging
import time
import sys
import threading
from typing import Optional
from fastapi import FastAPI, Body
from pydantic import BaseModel
import uvicorn

# Import our modules
from audio_engine.audio_capture import AudioCapture
from audio_engine.asr_engine import ASREngine
from audio_engine.intent_engine import IntentEngine
from audio_engine.state_manager import StateManager
from audio_engine.tts_engine import TTSEngine
from audio_engine.vision_bridge import get_bridge

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("AudioAPI")

# --- Models ---
class IntentRequest(BaseModel):
    text: str

class AssistantState:
    def __init__(self):
        self.asr_loaded = False
        self.llm_loaded = False
        self.tts_loaded = False
        
        # Initialize modules
        try:
            self.state_manager = StateManager()
            self.vision_bridge = get_bridge()
            self.vision_bridge.register_state_manager(self.state_manager)
            
            self.tts = TTSEngine(use_coqui=True)
            self.tts_loaded = True
            
            self.capture = AudioCapture(duration=3.0, threshold=0.01)
            
            self.asr = ASREngine(model_size="tiny")
            self.asr_loaded = True
            
            # Note: IntentEngine initialization might be slow due to LLM loading
            self.intent_parser = IntentEngine(llm_model_path="D:\\LLM\\models\\phi-2\\phi-2.Q4_K_M.gguf")
            self.llm_loaded = True
            
            logger.info("All engines loaded successfully.")
        except Exception as e:
            logger.error(f"Error during initialization: {e}")

# Global state
app = FastAPI(title="Zero-Touch Voice API")
assistant = None

@app.on_event("startup")
def startup_event():
    global assistant
    assistant = AssistantState()

# --- Endpoints ---

@app.get("/health")
def get_health():
    """System Health & Readiness"""
    return {
        "status": "ready" if (assistant and assistant.llm_loaded) else "initializing",
        "asr": "loaded" if (assistant and assistant.asr_loaded) else "failed/loading",
        "llm": "loaded" if (assistant and assistant.llm_loaded) else "failed/loading",
        "tts": "loaded" if (assistant and assistant.tts_loaded) else "failed/loading"
    }

@app.post("/voice/listen")
def voice_listen():
    """Trigger one listen–process–respond cycle"""
    if not assistant:
        return {"status": "error", "reason": "Assistant not initialized"}
        
    logger.info("API Trigger: Start Listening cycle...")
    
    # 1. Capture Audio
    audio_buffer = assistant.capture.listen_chunk()
    
    if audio_buffer is None:
        return {
            "heard_text": "",
            "confidence": 0.0,
            "intent": "None",
            "status": "ignored",
            "reason": "SILENCE"
        }
        
    # 2. Transcribe (Whisper)
    transcript_data = assistant.asr.transcribe(audio_buffer)
    text = transcript_data.get("text", "")
    confidence = transcript_data.get("confidence", 0.0)
    
    if not text or len(text) < 2:
        return {
            "heard_text": text,
            "confidence": confidence,
            "intent": "None",
            "status": "ignored",
            "reason": "TOO_SHORT"
        }
        
    logger.info(f"API Heard: {text} (Conf: {confidence:.2f})")
    
    # 3. Intent Parsing (Phi-2 / Rules)
    intent_packet = assistant.intent_parser.parse(text)
    intent = intent_packet.get("intent", "UNKNOWN")
    
    # 4. Handle conversational / fallback
    if intent == "CHAT":
        responses = {
            "hello": "Hello! I'm ready to assist.",
            "hi": "Hi there!",
            "hey": "Hey! How can I help?",
            "bye": "Goodbye!",
            "goodbye": "See you later!",
        }
        response_text = responses.get(text.strip().lower().rstrip('.!?'), "I'm here to help with surgical commands.")
        assistant.tts.speak(response_text)
        return {
            "heard_text": text,
            "confidence": confidence,
            "intent": "CHAT",
            "status": "success",
            "response": response_text
        }
        
    if intent == "UNKNOWN":
        assistant.tts.speak("I didn't understand that.")
        return {
            "heard_text": text,
            "confidence": confidence,
            "intent": "UNKNOWN",
            "status": "ignored",
            "reason": "LOW_CONFIDENCE_OR_UNKNOWN"
        }

    # 5. Safety validation / State check
    is_valid, msg = assistant.state_manager.validate_command(intent_packet)
    
    if not is_valid:
        # e.g. "NO_IMAGE_LOADED"
        assistant.tts.speak(msg)
        return {
            "heard_text": text,
            "confidence": confidence,
            "intent": intent,
            "status": "blocked",
            "reason": msg
        }
        
    # 6. Execution via VisionBridge
    success, exec_msg = assistant.vision_bridge.execute_action(intent, intent_packet)
    
    if success:
        logger.info(f"EXECUTED: {intent}")
        assistant.tts.speak(f"Executing {intent.replace('_', ' ').lower()}.")
        return {
            "heard_text": text,
            "confidence": confidence,
            "intent": intent,
            "status": "success",
            "reason": exec_msg
        }
    else:
        logger.error(f"EXECUTION FAILED: {intent} - {exec_msg}")
        assistant.tts.speak(f"Failed to execute.")
        return {
            "heard_text": text,
            "confidence": confidence,
            "intent": intent,
            "status": "failed",
            "reason": exec_msg
        }

@app.post("/intent/parse")
def intent_parse(request: IntentRequest):
    """Test intent engine without microphone"""
    if not assistant:
        return {"status": "error", "reason": "Assistant not initialized"}
        
    text = request.text
    logger.info(f"API Intent Parse Request: {text}")
    
    intent_packet = assistant.intent_parser.parse(text)
    
    # Map fields to match user requested schema
    return {
        "intent": intent_packet.get("intent", "UNKNOWN"),
        "target": intent_packet.get("target", "GAZE_REGION" if intent_packet.get("intent") != "CHAT" else "USER"),
        "confidence": intent_packet.get("confidence", 0.91),
        "source": intent_packet.get("source", "RULE")
    }

if __name__ == "__main__":
    # Run the API server
    logger.info("Starting Zero-Touch Audio API Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
