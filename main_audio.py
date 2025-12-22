
import logging
import time
import sys
import threading

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
logger = logging.getLogger("MainLoop")

class AudioAssistant:
    def __init__(self):
        logger.info("Initializing Zero-Touch Audio Assistant...")
        
        # Initialize modules
        self.state_manager = StateManager()
        self.vision_bridge = get_bridge()
        self.vision_bridge.register_state_manager(self.state_manager)
        self.tts = TTSEngine(use_coqui=True) # Set True if Coqui installed
        self.capture = AudioCapture(duration=3.0, threshold=0.01)
        self.asr = ASREngine(model_size="tiny") # or tiny.en
        self.intent_parser = IntentEngine(llm_model_path="D:\LLM\models\phi-2\phi-2.Q4_K_M.gguf") # Add path if available
        
        self.running = False

    def start(self):
        self.running = True
        logger.info("System Ready. Listening...")
        self.tts.speak("System Ready. Listening.")
        
        try:
            while self.running:
                # 1. Capture Audio
                audio_buffer = self.capture.listen_chunk()
                
                if audio_buffer is not None:
                    # 2. Transcribe
                    transcript_data = self.asr.transcribe(audio_buffer)
                    text = transcript_data.get("text", "")
                    confidence = transcript_data.get("confidence", 0.0)
                    
                    if not text or len(text) < 2:
                        continue
                        
                    logger.info(f"User said: {text} (Conf: {confidence:.2f})")
                    
                    # 3. Intent Parsing
                    intent_packet = self.intent_parser.parse(text)
                    intent = intent_packet.get("intent")
                    
                    # Safety check for malformed LLM responses
                    if not intent or intent == "":
                        self.tts.speak("I didn't understand that. Please say a surgical command or greeting.")
                        logger.warning(f"Malformed intent packet: {intent_packet}")
                        continue
                    
                    # Handle conversational inputs
                    if intent == "CHAT":
                        responses = {
                            "hello": "Hello! I'm ready to assist.",
                            "hi": "Hi there!",
                            "hey": "Hey! How can I help?",
                            "bye": "Goodbye!",
                            "goodbye": "See you later!",
                        }
                        response = responses.get(text.strip().lower().rstrip('.!?'), "I'm here to help with surgical commands.")
                        self.tts.speak(response)
                        logger.info(f"CHAT: {response}")
                        continue
                    
                    if intent == "UNKNOWN":
                        self.tts.speak("I didn't understand that. Please say a surgical command or greeting.")
                        logger.info("UNKNOWN intent - no action taken")
                        continue
                        
                    # 4. State Validation
                    is_valid, msg = self.state_manager.validate_command(intent_packet)
                    
                    if is_valid:
                        # 5. Execution via VisionBridge
                        success, msg = self.vision_bridge.execute_action(intent, intent_packet)
                        
                        if success:
                            logger.info(f"EXECUTED: {intent} - {msg}")
                            self.tts.speak(f"Executing {intent.replace('_', ' ').lower()}.")
                        else:
                            logger.error(f"EXECUTION FAILED: {intent} - {msg}")
                            self.tts.speak(f"Failed to execute {intent.replace('_', ' ').lower()}.")
                        
                        # Update state if needed (e.g., if user said "Load Image")
                        # self.state_manager.update_state(...)
                    else:
                        logger.warning(f"Command Blocked: {msg}")
                        self.tts.speak(msg)
                        
                else:
                    # Silence - just loop or sleep tiny bit
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            logger.info("Stopping...")
            self.stop()

    def stop(self):
        self.running = False
        logger.info("System Stopped.")

if __name__ == "__main__":
    assistant = AudioAssistant()
    assistant.start()
