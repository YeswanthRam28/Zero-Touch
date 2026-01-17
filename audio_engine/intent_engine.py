
import logging
import json
import re
import requests

# Configure logging
logger = logging.getLogger(__name__)

class IntentEngine:
    def __init__(self, model_name="phi"):
        """
        Initialize Intent Engine using Ollama.
        :param model_name: Name of the model in Ollama (e.g., "phi", "llama3").
        """
        self.model_name = model_name
        self.ollama_url = "http://localhost:11434/api/generate"
        logger.info(f"Ollama Intent Engine initialized with model: {self.model_name}")

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

        # 2. Ollama Fallback (Slow Path)
        return self._llm_parse(text)

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
            # New surgical commands
            (r"highlight", "HIGHLIGHT"),
            (r"open patient file", "OPEN_PATIENT_FILE"),
            (r"show (ct|mri|x-ray)", "SHOW_SCAN"),
            (r"analyze", "ANALYZE_REGION"),
            (r"compare", "COMPARE_SCANS"),
            # Conversational
            (r"^(hello|hi|hey|greetings|hi assistant|hello assistant)[\.\?!]*$", "CHAT"),
            (r"^(bye|goodbye|see you)[\.\?!]*$", "CHAT"),
            (r"^(how are you|what'?s up|how'?s it going)[\.\?!]*$", "CHAT"),
        ]

        spatial_keywords = ["here", "this", "that", "there", "this region"]
        target = "SCREEN"
        for kw in spatial_keywords:
            if kw in text:
                target = "GAZE_REGION"
                break

        for pattern, intent in rules:
            if re.search(pattern, text):
                return {
                    "intent": intent,
                    "target": target if intent not in ["CHAT"] else "USER",
                    "confidence": 1.0,
                    "source": "RULE",
                    "raw_text": text
                }
        return None

    def _llm_parse(self, text):
        """
        Use Ollama to parse complex commands.
        """
        prompt = f"""You are a surgical assistant. Classify the command into ONE of these intents:
- ZOOM_IN, ZOOM_OUT: for zoom/enlarge/magnify commands
- SCROLL_LEFT, SCROLL_RIGHT, SCROLL_UP, SCROLL_DOWN: for navigation
- NEXT_IMAGE, PREV_IMAGE: for switching images
- HIGHLIGHT, ANALYZE_REGION: for specific areas (often uses "this" or "here")
- OPEN_PATIENT_FILE, SHOW_SCAN: for data management
- CHAT: for greetings, questions, or non-surgical conversation
- UNKNOWN: if unclear

Return ONLY valid JSON: {{"intent": "INTENT_NAME", "target": "SCREEN" or "GAZE_REGION", "parameter": "value"}}

Command: "{text}"
JSON:"""
        
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }
            response = requests.post(self.ollama_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "").strip()
                data = json.loads(response_text)
                data["confidence"] = 0.85 
                data["source"] = "OLLAMA"
                data["raw_text"] = text
                return data
            else:
                logger.error(f"Ollama Error: Status {response.status_code}")
            
        except Exception as e:
            logger.error(f"Ollama Parse Error: {e}")
        
        return {"intent": "UNKNOWN", "confidence": 0.0}

if __name__ == "__main__":
    engine = IntentEngine(model_name="phi")
    print(engine.parse("zoom in please"))
    print(engine.parse("scroll right a bit"))
