
import whisper
import logging
import torch
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ASREngine:
    def __init__(self, model_size="tiny", language="en"):
        """
        Initialize ASREngine with Whisper model.
        :param model_size: 'tiny', 'base', 'small', etc.
        :param language: Language code (default 'en').
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading Whisper model '{model_size}' on {self.device}...")
        try:
            self.model = whisper.load_model(model_size, device=self.device)
            self.language = language
            logger.info("Whisper model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise

    def transcribe(self, audio_data):
        """
        Transcribe audio data.
        :param audio_data: Numpy array of float32 audio.
        :return: Dict with 'text', 'confidence', 'language'.
        """
        try:
            # Whisper expects float32 numpy array
            if audio_data is None or len(audio_data) == 0:
                return {"text": "", "confidence": 0.0}

            # Pad or trim audio to fit 30 seconds if necessary, 
            # but Whisper handle raw audio buffers well usually.
            # We just pass the numpy array directly.
            
            # Use fp16=False for CPU compatibility if needed, though safe to leave auto usually.
            result = self.model.transcribe(audio_data, language=self.language, fp16=False)
            
            text = result.get("text", "").strip()
            
            # Confidence estimation (naive average of segment probabilities)
            # Whisper result['segments'] has 'avg_logprob' or 'no_speech_prob'
            # We can map logprob to probability: exp(logprob)
            
            avg_confidence = 0.0
            segments = result.get("segments", [])
            if segments:
                # Taking the average confidence of segments
                confidences = [np.exp(s.get("avg_logprob", -1)) for s in segments]
                avg_confidence = sum(confidences) / len(confidences)
            
            logger.info(f"Transcribed: '{text}' (Conf: {avg_confidence:.2f})")
            
            return {
                "text": text,
                "confidence": avg_confidence,
                "language": self.language
            }
            
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return {"text": "", "confidence": 0.0}

if __name__ == "__main__":
    # Test stub
    # Create a dummy audio buffer (sine wave) for testing code structure, 
    # capturing real audio requires AudioCapture
    engine = ASREngine()
    sample_rate = 16000
    t = np.linspace(0, 1.0, int(sample_rate * 1.0))
    # Silence
    audio = np.zeros_like(t, dtype=np.float32)
    print(engine.transcribe(audio))
