
import logging
import json
import re
import time
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
        self.ollama_url = "http://127.0.0.1:11434/api/generate"
        
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

    def ensure_vision_model(self):
        """Pre-warm the llava model in Ollama to ensure it's ready."""
        try:
            logger.info("Pre-warming Ollama vision model (llava)...")
            payload = {
                "model": "llava",
                "prompt": "hello",
                "stream": False
            }
            # Fast timeout for pre-warm
            requests.post(self.ollama_url, json=payload, timeout=30)
            logger.info("Vision model (llava) is ready.")
        except Exception as e:
            logger.warning(f"Could not pre-warm llava: {e}")

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
            # Maintenance/System
            (r"(generate (a )?report|end session|finish procedure|create report|make report|save report)", "GENERATE_REPORT"),
            # Conversational
            (r"^(hello|hi|hey|greetings|hi assistant|hello assistant)[\.\?!]*$", "CHAT"),
            (r"^(bye|goodbye|see you)[\.\?!]*$", "CHAT"),
            (r"^(how are you|what'?s up|how'?s it going)[\.\?!]*$", "CHAT"),
            # Medical Knowledge Fast-Track
            (r"(dosage|how much|what is|tell me about|contraindication|parasit|paracetamol|medication)", "KNOWLEDGE_QUERY"),
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
                    "intent": "KNOWLEDGE" if intent == "KNOWLEDGE_QUERY" else intent,
                    "type": "KNOWLEDGE" if intent == "KNOWLEDGE_QUERY" else ("NAVIGATION" if intent not in ["CHAT"] else "CHAT"),
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
        prompt = f"""You are a surgical assistant. Classify the input into ONE of these types and intents:
TYPES:
- NAVIGATION: For physical control of images (Zoom, Scroll, Next, Prev) OR system actions like GENERATE_REPORT.
- KNOWLEDGE: For medical questions, patient data, or clinical reasoning.
- CHAT: ONLY for greetings, "how are you", or small talk. 

CRITICAL: "Generate report", "end session", or "finish procedure" are NAVIGATION/SYSTEM intents, NEVER CHAT.

INTENTS:
- ZOOM_IN, ZOOM_OUT, SCROLL_LEFT, SCROLL_RIGHT, SCROLL_UP, SCROLL_DOWN
- NEXT_IMAGE, PREV_IMAGE, RESET_VIEW
- HIGHLIGHT, ANALYZE_REGION
- OPEN_PATIENT_FILE, SHOW_SCAN
- GENERATE_REPORT
- CHAT
- UNKNOWN

Return ONLY valid JSON: {{"type": "TYPE_NAME", "intent": "INTENT_NAME", "target": "SCREEN" or "GAZE_REGION", "parameter": "value"}}

Input: "{text}"
JSON:"""
        
        # Try Ollama Primary
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }
            response = requests.post(self.ollama_url, json=payload, timeout=20)
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "").strip()
                data = json.loads(response_text)
                data["confidence"] = 0.85 
                data["source"] = "OLLAMA"
                data["raw_text"] = text
                # Force uppercase and ensure fields exist
                data["type"] = str(data.get("type", "KNOWLEDGE")).upper()
                data["intent"] = str(data.get("intent", "UNKNOWN")).upper()
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
                        temperature=0.1,
                    )
                )
                
                response_text = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(response_text)
                data["confidence"] = 0.90
                data["source"] = "GEMINI"
                data["raw_text"] = text
                data["type"] = str(data.get("type", "KNOWLEDGE")).upper()
                data["intent"] = str(data.get("intent", "UNKNOWN")).upper()
                return data
            except Exception as e:
                logger.error(f"Gemini Fallback Error: {e}")
        
        return {"intent": "UNKNOWN", "type": "UNKNOWN", "confidence": 0.0}

    def medical_query(self, query):
        """
        Specialized method for clinical reasoning/Q&A.
        """
        logger.info(f"Medical Q&A Query: {query}")
        
        prompt = f"""You are an expert surgical co-pilot and clinical data engine. 
The user is a lead surgeon in an active operating room. 
Provide precise, evidence-based medical data for the following question. 
Be concise, authoritative, and factual. Skip all generic safety warnings and disclaimers.

Question: "{query}"
Assistant (Direct Answer):"""

        # Primary: Ollama (high timeout - model may need to swap after llava)
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False
            }
            logger.info(f"Sending medical query to Ollama ({self.model_name})...")
            response = requests.post(self.ollama_url, json=payload, timeout=90)
            if response.status_code == 200:
                answer = response.json().get("response", "").strip()
                logger.info(f"Medical Q&A answered ({len(answer)} chars).")
                return answer
            else:
                logger.warning(f"Ollama medical_query returned status {response.status_code}")
        except Exception as e:
            logger.warning(f"Ollama medical_query failed: {e}")

        # Fallback: Gemini
        if self.gemini_model:
            try:
                logger.info("Falling back to Gemini for medical Q&A...")
                response = self.gemini_model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                logger.error(f"Gemini medical_query fallback failed: {e}")

        return "I'm sorry, I cannot access the medical database right now. Please verify with hospital protocols."

    def analyze_image(self, image_data, text_query, gaze_info=None):
        """
        Analyze an image (base64) using Ollama (llava) or Gemini.
        :param image_data: Base64 string of the image.
        :param text_query: The question/command from the surgeon.
        :param gaze_info: Description of where the surgeon is looking (e.g. "LEFT", "CENTER", "RIGHT")
        """
        logger.info("Starting visual analysis...")
        
        location_context = f"The surgeon is currently focused on the {gaze_info} part of the image." if gaze_info else ""
        
        prompt = f"""You are a smart surgical assistant. {location_context}
Analyze this medical image based on the surgeon's request: "{text_query}". 
Be precise, clinical, and highlight any potential anomalies or structures of interest in the {gaze_info or 'specified'} region.
Assistant:"""

        # 1. Try Ollama with 'llava' (Hardcoded for vision tasks), with retry
        MAX_RETRIES = 2
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                payload = {
                    "model": "llava",
                    "prompt": prompt,
                    "images": [image_data],
                    "stream": False
                }
                logger.info(f"Sending request to Ollama (llava) — attempt {attempt}/{MAX_RETRIES}...")
                response = requests.post(self.ollama_url, json=payload, timeout=120)
                if response.status_code == 200:
                    result = response.json().get("response", "").strip()
                    logger.info(f"Ollama (llava) responded successfully on attempt {attempt}.")
                    return result
                else:
                    logger.warning(f"Ollama returned status {response.status_code} on attempt {attempt}. Body: {response.text[:200]}")
                    if attempt < MAX_RETRIES:
                        logger.info("Retrying in 3 seconds...")
                        time.sleep(3)
            except Exception as e:
                logger.warning(f"Ollama Vision (llava) attempt {attempt} failed: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(3)

        # 2. Fallback to Gemini Pro Vision
        if self.gemini_model:
            try:
                logger.info("Falling back to Gemini Vision...")
                import base64
                img_bytes = base64.b64decode(image_data)
                response = self.gemini_model.generate_content([prompt, {"mime_type": "image/jpeg", "data": img_bytes}])
                return response.text.strip()
            except Exception as e:
                logger.error(f"Gemini Vision Fallback Error: {e}")

        return "I am unable to analyze the image at this moment. Please ensure the local vision model is running."

    def summarize_session(self, logs):
        """
        Summarize surgical logs into a procedure note.
        """
        log_text = json.dumps(logs, indent=2)
        prompt = f"""Based on the following surgical assistant event logs, generate a professional, concise "Surgical Procedure Note".
Summarize the key actions taken and the progression of the procedure.

Logs:
{log_text}

Surgical Note:"""

        try:
            payload = {"model": self.model_name, "prompt": prompt, "stream": False}
            response = requests.post(self.ollama_url, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json().get("response", "").strip()
        except:
            return "Failed to generate summary automatically."

if __name__ == "__main__":
    engine = IntentEngine(model_name="phi2-local")
    print(engine.parse("zoom in please"))
    print(engine.parse("scroll right a bit"))
