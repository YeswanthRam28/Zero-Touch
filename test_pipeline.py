
import unittest
from unittest.mock import MagicMock, patch
import sys
import numpy as np
import logging

# Mock dependencies BEFORE importing our modules
sys.modules["whisper"] = MagicMock()
sys.modules["sounddevice"] = MagicMock()
sys.modules["TTS.api"] = MagicMock()
# Also mock torch?
sys.modules["torch"] = MagicMock()

# Now import our modules
from audio_engine.asr_engine import ASREngine
from audio_engine.intent_engine import IntentEngine
from audio_engine.state_manager import StateManager

# Configure logging
logging.basicConfig(level=logging.INFO)

class TestAudioPipeline(unittest.TestCase):
    
    def setUp(self):
        # We need to patch the internal calls or just rely on the mocks we set in sys.modules
        # But ASREngine init calls whisper.load_model, so our mock must handle that.
        self.asr = ASREngine()
        self.intent = IntentEngine()
        self.state = StateManager()

    def test_asr_loading(self):
        """Test if ASR model loads and runs on empty/dummy audio."""
        print("\n--- Testing ASR Loading ---")
        # Setup mock return for transcribe
        self.asr.model.transcribe.return_value = {"text": "test", "segments": []}
        
        dummy_audio = np.zeros(16000, dtype=np.float32)
        result = self.asr.transcribe(dummy_audio)
        self.assertIn("text", result)
        print("ASR Check Passed.")

    def test_intent_parsing_rules(self):
        """Test rule-based intent parsing."""
        print("\n--- Testing Intent Rules ---")
        text = "Please zoom in on the image"
        result = self.intent.parse(text)
        self.assertEqual(result["intent"], "ZOOM_IN")
        print(f"Computed Intent: {result['intent']} (Expected: ZOOM_IN)")

        text = "Scroll left a bit"
        result = self.intent.parse(text)
        self.assertEqual(result["intent"], "SCROLL_LEFT")
        print(f"Computed Intent: {result['intent']} (Expected: SCROLL_LEFT)")

    def test_state_validation(self):
        """Test state validation logic."""
        print("\n--- Testing State Validation ---")
        intent_packet = {"intent": "ZOOM_IN"}
        
        # Should fail initially
        valid, msg = self.state.validate_command(intent_packet)
        self.assertFalse(valid)
        print(f"Blocked as expected: {msg}")
        
        # Update state
        self.state.update_state("is_image_loaded", True)
        
        # Should pass now
        valid, msg = self.state.validate_command(intent_packet)
        self.assertTrue(valid)
        print("Allowed as expected after state update.")

if __name__ == "__main__":
    unittest.main()
