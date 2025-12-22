
import logging
import json
import re

# Configure logging
logger = logging.getLogger(__name__)

class IntentEngine:
    def __init__(self, llm_model_path=None):
        """
        Initialize Intent Engine.
        :param llm_model_path: Path to GGUF model for llama-cpp-python.
        """
        self.llm = None
        if llm_model_path:
            try:
                from llama_cpp import Llama
                logger.info(f"Loading LLM from {llm_model_path}...")
                self.llm = Llama(model_path=llm_model_path, n_ctx=2048, verbose=False)
                logger.info("LLM loaded.")
            except Exception as e:
                logger.error(f"Failed to load LLM: {e}")
        else:
            logger.info("No LLM model path provided. Running in Rule-Based only mode.")

    def parse(self, text):
        """
        Parse text into intent packet.
        :param text: Transcribed text.
        :return: Dict intent packet.
        """
        text = text.lower().strip()
        logger.info(f"Parsing intent for: '{text}'")

        # 1. Rule-Based (Fast Path)
        rule_intent = self._rule_based_parse(text)
        if rule_intent:
            logger.info(f"Rule match: {rule_intent}")
            return rule_intent

        # 2. LLM Fallback (Slow Path)
        if self.llm:
            return self._llm_parse(text)
        
        # 3. Fail
        logger.warning("No intent matched.")
        return {"intent": "UNKNOWN", "confidence": 0.0}

    def _rule_based_parse(self, text):
        """
        Simple regex/keyword matching.
        """
        rules = [
            # Surgical commands
            (r"zoom in", "ZOOM_IN"),
            (r"zoom out", "ZOOM_OUT"),
            (r"scroll left", "SCROLL_LEFT"),
            (r"scroll right", "SCROLL_RIGHT"),
            (r"scroll up", "SCROLL_UP"),
            (r"scroll down", "SCROLL_DOWN"),
            (r"next image", "NEXT_IMAGE"),
            (r"previous image", "PREV_IMAGE"),
            (r"reset", "RESET_VIEW"),
            (r"stop", "STOP"),
            # Conversational
            (r"^(hello|hi|hey|greetings)[\.\?!]*$", "CHAT"),
            (r"^(bye|goodbye|see you)[\.\?!]*$", "CHAT"),
            (r"^(how are you|what'?s up|how'?s it going)[\.\?!]*$", "CHAT"),
        ]

        for pattern, intent in rules:
            if re.search(pattern, text):
                return {
                    "intent": intent,
                    "target": "SCREEN" if intent not in ["CHAT"] else "USER",
                    "confidence": 1.0,  # Rules are deterministic
                    "source": "RULE"
                }
        return None

    def _llm_parse(self, text):
        """
        Use Phi-2/Llama to parse complex commands.
        """
        prompt = f"""You are a surgical assistant. Classify the command into ONE of these intents:
- ZOOM_IN, ZOOM_OUT: for zoom/enlarge/magnify commands
- SCROLL_LEFT, SCROLL_RIGHT, SCROLL_UP, SCROLL_DOWN: for navigation
- NEXT_IMAGE, PREV_IMAGE: for switching images
- CHAT: for greetings, questions, or non-surgical conversation
- UNKNOWN: if unclear

Return ONLY valid JSON: {{"intent": "INTENT_NAME", "parameter": "value"}}

Command: "{text}"
JSON:"""
        
        try:
            output = self.llm(
                prompt, 
                max_tokens=64, 
                stop=["\n", "}"], 
                echo=False
            )
            response_text = output['choices'][0]['text'].strip() + "}"
            
            # Simple JSON cleanup
            # Try to frame it
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = response_text[start:end]
                data = json.loads(json_str)
                data["confidence"] = 0.85 # Mock confidence for LLM
                data["source"] = "LLM"
                return data
            
        except Exception as e:
            logger.error(f"LLM Parse Error: {e}")
        
        return {"intent": "UNKNOWN", "confidence": 0.0}

if __name__ == "__main__":
    engine = IntentEngine() # No LLM for testing
    print(engine.parse("zoom in please"))
    print(engine.parse("scroll right a bit"))
