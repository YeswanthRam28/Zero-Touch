
import logging
import os
import sounddevice as sd
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)

class TTSEngine:
    def __init__(self, use_coqui=False):
        """
        Initialize TTS Engine.
        :param use_coqui: If True, tries to use Coqui TTS (heavy). 
                          If False, uses pyttsx3 (offline, fast) if available, or mock.
        """
        self.engine = None
        self.use_coqui = use_coqui
        
        if self.use_coqui:
            try:
                from TTS.api import TTS
                # specific model or default
                logger.info("Initializing Coqui TTS...")
                self.engine = TTS(model_name="tts_models/en/ljspeech/glow-tts", progress_bar=False, gpu=False)
                logger.info("Coqui TTS initialized.")
            except ImportError:
                logger.warning("TTS library not found. Falling back to simple print/logging.")
            except Exception as e:
                logger.error(f"Error initializing Coqui TTS: {e}")
        
    def speak(self, text):
        """
        Speak the text.
        """
        logger.info(f"🗣️ TTS: {text}")
        
        if self.engine:
            try:
                # Generate audio (returns list of floats)
                wav = self.engine.tts(text=text)
                
                # Convert to numpy array
                wav_np = np.array(wav, dtype=np.float32)
                
                # Play
                # Default sample rate for GlowTTS/LJSPEECH is often 22050
                sd.play(wav_np, samplerate=22050)
                sd.wait()
            except Exception as e:
                logger.error(f"TTS Error: {e}")
        else:
            # Fallback for now: print to console is enough for logic verification
            print(f"[SYSTEM SPEAKS]: {text}")

if __name__ == "__main__":
    tts = TTSEngine(use_coqui=False)
    tts.speak("Zooming in.")
