
import logging
import os
import sounddevice as sd
import numpy as np
import threading
import sys

if sys.platform == "win32":
    import pythoncom

# Configure logging
logger = logging.getLogger(__name__)

class TTSEngine:
    def __init__(self, use_coqui=False, device_index=None):
        """
        Initialize TTS Engine.
        :param use_coqui: If True, tries to use Coqui TTS (heavy). 
                          If False, uses pyttsx3 (offline, fast) if available.
        :param device_index: Index of the output device to use.
        """
        self.engine = None
        self.use_coqui = use_coqui
        self.pyttsx3_engine = None
        self.lock = threading.Lock()
        self.device_index = device_index

    def set_device(self, index):
        """Set the active output device."""
        self.device_index = index
        logger.info(f"Audio output device set to index: {index}")
        
        if self.use_coqui:
            # ... existing coqui init ...
            try:
                from TTS.api import TTS
                logger.info("Initializing Coqui TTS...")
                self.engine = TTS(model_name="tts_models/en/ljspeech/glow-tts", progress_bar=False, gpu=False)
                logger.info("Coqui TTS initialized.")
            except ImportError:
                logger.warning("Coqui TTS library not found.")
            except Exception as e:
                logger.error(f"Error initializing Coqui TTS: {e}")
        
        # Always try to initialize pyttsx3 as a fallback or primary if use_coqui is False
        if not self.engine:
            try:
                import pyttsx3
                logger.info("Initializing pyttsx3...")
                self.pyttsx3_engine = pyttsx3.init()
                # Set properties
                self.pyttsx3_engine.setProperty('rate', 175)    # Speed
                self.pyttsx3_engine.setProperty('volume', 1.0)  # Volume
                logger.info("pyttsx3 initialized.")
            except ImportError:
                logger.warning("pyttsx3 library not found. Falling back to simple print.")
            except Exception as e:
                logger.error(f"Error initializing pyttsx3: {e}")

    def speak(self, text):
        """
        Speak the text using available engine. Thread-safe.
        """
        with self.lock:
            if sys.platform == "win32":
                pythoncom.CoInitialize()
            
            logger.info(f"🗣️ TTS: {text}")
            
            if self.use_coqui and self.engine:
                try:
                    # Coqui TTS
                    wav = self.engine.tts(text=text)
                    wav_np = np.array(wav, dtype=np.float32)
                    sd.play(wav_np, samplerate=22050, device=self.device_index)
                    sd.wait()
                    return
                except Exception as e:
                    logger.error(f"Coqui TTS Error: {e}")

            if self.pyttsx3_engine:
                try:
                    # pyttsx3 speak needs to run in a way that doesn't block too much if possible, 
                    # but standard usage is synchronous.
                    self.pyttsx3_engine.say(text)
                    self.pyttsx3_engine.runAndWait()
                except Exception as e:
                    logger.error(f"pyttsx3 Error: {e}")
                    print(f"[SYSTEM SPEAKS]: {text}")
            else:
                # Final fallback
                print(f"[SYSTEM SPEAKS]: {text}")

if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    tts = TTSEngine(use_coqui=False)
    tts.speak("Zero Touch system is ready.")
