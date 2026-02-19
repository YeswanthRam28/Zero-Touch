
import sounddevice as sd
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioCapture:
    def __init__(self, sample_rate=16000, duration=3.0, threshold=0.005, device_index=None):
        """
        Initialize AudioCapture.
        :param sample_rate: Sampling rate in Hz (default 16000 for Whisper).
        :param duration: Duration of chunk to record in seconds.
        :param threshold: RMS threshold for silence detection.
        :param device_index: Index of the input device to use.
        """
        self.sample_rate = sample_rate
        self.duration = duration
        self.threshold = threshold
        self.channels = 1
        self.device_index = device_index

    def set_device(self, index):
        """Set the active input device."""
        self.device_index = index
        logger.info(f"Audio input device set to index: {index}")

    def listen_chunk(self):
        """
        Captures a chunk of audio.
        :return: Numpy array of audio data or None if silence.
        """
        logger.info(f"Listening for {self.duration} seconds...")
        try:
            # Record audio
            audio_data = sd.rec(int(self.duration * self.sample_rate),
                                samplerate=self.sample_rate,
                                channels=self.channels,
                                dtype='float32',
                                device=self.device_index)
            sd.wait()  # Wait until recording is finished
            
            # Flatten to 1D array
            audio_flat = audio_data.flatten()
            
            # Calculate RMS (Root Mean Square) for volume
            rms = np.sqrt(np.mean(audio_flat**2))
            
            if rms < self.threshold:
                logger.info(f"Silence (RMS: {rms:.5f} < {self.threshold})") # Changed to INFO for debugging
                return None
            
            logger.info(f"Audio captured (RMS: {rms:.4f})")
            return audio_flat
            
        except Exception as e:
            logger.error(f"Error during audio capture: {e}")
            return None

if __name__ == "__main__":
    # Test stub
    capture = AudioCapture()
    audio = capture.listen_chunk()
    if audio is not None:
        print(f"Captured {len(audio)} samples.")
    else:
        print("Silence.")
