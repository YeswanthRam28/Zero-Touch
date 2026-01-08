"""
Integration Bridge between Audio Engine and Vision System

This module provides the interface for the Audio & Intent Engine to communicate
with the Vision/Display system (built by Vision & Gaze Lead).

Usage:
    1. Vision system imports this module
    2. Vision system calls register_vision_callbacks() with its functions
    3. Audio engine calls execute_action() which triggers vision callbacks
"""

import logging

logger = logging.getLogger(__name__)

class VisionBridge:
    """
    Bridge between voice commands and vision system.
    """
    def __init__(self):
        self.callbacks = {
            "load_image": None,
            "zoom_in": None,
            "zoom_out": None,
            "scroll": None,
            "next_image": None,
            "prev_image": None,
            "reset_view": None,
        }
        self.state_manager = None
        self.action_listeners = [] # For WebSocket broadcasting
    
    def register_action_listener(self, listener):
        """Register a function to be called on every action execution."""
        self.action_listeners.append(listener)

    def register_state_manager(self, state_manager):
        """
        Register the state manager for tracking system state.
        """
        self.state_manager = state_manager
        logger.info("State manager registered with VisionBridge")
    
    def register_vision_callbacks(self, callbacks_dict):
        """
        Register callbacks from the vision system.
        
        Expected callbacks:
        {
            "load_image": function(image_path) -> bool,
            "zoom_in": function(factor=1.2) -> bool,
            "zoom_out": function(factor=0.8) -> bool,
            "scroll": function(direction, amount) -> bool,  # direction: 'left', 'right', 'up', 'down'
            "next_image": function() -> bool,
            "prev_image": function() -> bool,
            "reset_view": function() -> bool,
        }
        
        Each callback should return True on success, False on failure.
        """
        for key, func in callbacks_dict.items():
            if key in self.callbacks:
                self.callbacks[key] = func
                logger.info(f"Registered vision callback: {key}")
            else:
                logger.warning(f"Unknown callback key: {key}")
    
    def execute_action(self, intent, parameters=None):
        """
        Execute a vision action based on intent.
        
        :param intent: Intent name (e.g., 'ZOOM_IN', 'SCROLL_LEFT')
        :param parameters: Optional parameters dict
        :return: (success: bool, message: str)
        """
        parameters = parameters or {}
        
        # Broadcast to listeners (WebSockets)
        for listener in self.action_listeners:
            try:
                listener(intent, parameters)
            except Exception as e:
                logger.error(f"Error in action listener: {e}")

        # Map intents to callbacks
        action_map = {
            "ZOOM_IN": ("zoom_in", {"factor": parameters.get("factor", 1.2), "region": parameters.get("region")}),
            "ZOOM_OUT": ("zoom_out", {"factor": parameters.get("factor", 0.8), "region": parameters.get("region")}),
            "SCROLL_LEFT": ("scroll", {"direction": "left", "amount": parameters.get("amount", 50)}),
            "SCROLL_RIGHT": ("scroll", {"direction": "right", "amount": parameters.get("amount", 50)}),
            "SCROLL_UP": ("scroll", {"direction": "up", "amount": parameters.get("amount", 50)}),
            "SCROLL_DOWN": ("scroll", {"direction": "down", "amount": parameters.get("amount", 50)}),
            "NEXT_IMAGE": ("next_image", {}),
            "PREV_IMAGE": ("prev_image", {}),
            "RESET_VIEW": ("reset_view", {}),
            "LOAD_IMAGE": ("load_image", {"image_path": parameters.get("image_path")}),
            "HIGHLIGHT_REGION": ("scroll", {"direction": "center", "amount": 0}), # Mock for now
        }
        
        if intent not in action_map:
            return False, f"Unknown intent: {intent}"
        
        callback_name, callback_params = action_map[intent]
        callback = self.callbacks.get(callback_name)
        
        if callback is None:
            # We treat this as success because the WebSocket listener will handle it in the frontend
            return True, f"Action {intent} broadcasted to listeners."
        
        try:
            success = callback(**callback_params)
            if success:
                return True, f"Executed {intent}"
            else:
                return False, f"Failed to execute {intent}"
        except Exception as e:
            logger.error(f"Error executing {intent}: {e}")
            return False, f"Error: {e}"

# Global singleton instance
_bridge = VisionBridge()

def get_bridge():
    """Get the global VisionBridge instance."""
    return _bridge
