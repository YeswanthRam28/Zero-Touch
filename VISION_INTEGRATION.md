# Vision System Integration Guide

This guide explains how to integrate the Audio & Intent Engine with the Vision/Display system.

## Architecture

```
Voice Input → ASR → Intent Parser → State Validator → VisionBridge → Your Vision System
```

## Integration Steps

### 1. Import the Bridge

```python
from audio_engine.vision_bridge import get_bridge
```

### 2. Create Your Vision Functions

Implement these functions in your vision system:

```python
def load_image(image_path):
    """Load and display an image."""
    # Your code here
    return True  # Return True on success

def zoom_in(factor=1.2):
    """Zoom in on the current image."""
    # Your code here
    return True

def zoom_out(factor=0.8):
    """Zoom out on the current image."""
    # Your code here
    return True

def scroll(direction, amount):
    """Scroll/pan the image.
    direction: 'left', 'right', 'up', 'down'
    amount: pixels to scroll
    """
    # Your code here
    return True

def next_image():
    """Load next image in sequence."""
    # Your code here
    return True

def prev_image():
    """Load previous image in sequence."""
    # Your code here
    return True

def reset_view():
    """Reset zoom and pan to default."""
    # Your code here
    return True
```

### 3. Register Your Callbacks

```python
bridge = get_bridge()
bridge.register_vision_callbacks({
    "load_image": load_image,
    "zoom_in": zoom_in,
    "zoom_out": zoom_out,
    "scroll": scroll,
    "next_image": next_image,
    "prev_image": prev_image,
    "reset_view": reset_view,
})
```

### 4. Update State When Images Load

When you successfully load an image, update the state manager:

```python
bridge = get_bridge()
if bridge.state_manager:
    bridge.state_manager.update_state("is_image_loaded", True)
```

### 5. Run the Audio Assistant

```python
from main_audio import AudioAssistant

assistant = AudioAssistant()
assistant.start()
```

## Example

See `example_vision_integration.py` for a complete working example with a simple OpenCV-based image viewer.

## Voice Commands Supported

- **Zoom**: "zoom in", "zoom out"
- **Scroll**: "scroll left", "scroll right", "scroll up", "scroll down"
- **Navigation**: "next image", "previous image"
- **Reset**: "reset"
- **Greetings**: "hello", "hi", "bye"

## Testing Without Vision System

The audio assistant works in "mock mode" if no callbacks are registered. It will:
- Recognize voice commands
- Validate against state
- Log actions (but not execute them)
- Provide voice feedback

This allows you to test the voice interface independently.
