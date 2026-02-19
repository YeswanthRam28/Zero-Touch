import logging
import datetime

logger = logging.getLogger(__name__)

class StateManager:
    def __init__(self):
        """
        Initialize the system state.
        """
        self.state = {
            "is_image_loaded": False,
            "gaze_available": False,
            "current_mode": "IDLE",  # IDLE, VIEWING, MEASURING, etc.
            "last_action": None,
            "event_logs": [] # To store actions for AI Scribe
        }

    def update_state(self, key, value):
        """
        Update a specific state variable.
        """
        if key in self.state:
            self.state[key] = value
            logger.info(f"State updated: {key} -> {value}")
        else:
            logger.warning(f"Attempted to update unknown state key: {key}")

    def log_event(self, event_type, details):
        """
        Log an event for the AI Scribe.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "timestamp": timestamp,
            "type": event_type,
            "details": details
        }
        self.state["event_logs"].append(entry)
        logger.info(f"Event logged: {event_type}")

    def get_event_logs(self):
        """
        Return the list of logged events.
        """
        return self.state["event_logs"]

    def get_state(self, key):
        # ... existing ...
        return self.state.get(key)

    def validate_command(self, intent_packet):
        # ... existing ...
        intent = intent_packet.get("intent")
        
        # Example validation logic
        if intent in ["ZOOM_IN", "ZOOM_OUT", "SCROLL_LEFT", "SCROLL_RIGHT", "SCROLL_UP", "SCROLL_DOWN", "NEXT_IMAGE", "PREV_IMAGE"]:
            if not self.state["is_image_loaded"]:
                return False, "No image loaded."
        
        if intent == "GAZE_SELECT":
            if not self.state["gaze_available"]:
                return False, "Gaze tracking not available."

        return True, "OK"
