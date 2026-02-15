
import logging
import json
import re
import requests
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class IntentEngine:
    def __init__(self, model_name="phi"):
        """
        Initialize Intent Engine with Ollama and Gemini fallback.
        :param model_name: Name of the model in Ollama.
        """
        self.model_name = model_name
        self.ollama_url = "http://localhost:11434/api/generate"
        
        # Configure Gemini
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.use_gemini = os.getenv("USE_GEMINI_FALLBACK", "false").lower() == "true"
        
        if self.gemini_api_key and self.use_gemini:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Gemini fallback configured.")
        elif not self.use_gemini:
            self.gemini_model = None
            logger.info("Gemini fallback is disabled via .env (USE_GEMINI_FALLBACK=false).")
        else:
            self.gemini_model = None
            logger.warning("GEMINI_API_KEY not found in .env. Fallback disabled.")
            
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

        # 2. Ollama Fallback (Slow Path) -> then Gemini
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
        Use Ollama to parse complex commands with Gemini fallback.
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
        
        # Try Ollama Primary
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }
            response = requests.post(self.ollama_url, json=payload, timeout=10) # Shorter timeout for faster failover
            
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
            logger.warning(f"Ollama unavailable or timed out: {e}")

        # Fallback to Gemini
        if self.gemini_model:
            try:
                logger.info(f"Attempting Gemini fallback for: {text}")
                response = self.gemini_model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        candidate_count=1,
                        stop_sequences=[],
                        max_output_tokens=100,
                        temperature=0.1,
                    )
                )
                
                # Cleanup potential markdown code blocks in response
                response_text = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(response_text)
                data["confidence"] = 0.90
                data["source"] = "GEMINI"
                data["raw_text"] = text
                logger.info(f"Gemini success: {data['intent']}")
                return data
            except Exception as e:
                logger.error(f"Gemini Fallback Error: {e}")
        
        return {"intent": "UNKNOWN", "confidence": 0.0}

if __name__ == "__main__":
    engine = IntentEngine(model_name="phi2-local")
    print(engine.parse("zoom in please"))
    print(engine.parse("scroll right a bit"))
