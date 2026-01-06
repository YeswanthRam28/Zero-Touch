"""
Example Integration for Vision & Gaze Lead

This shows how to connect your image viewer/display system to the voice commands.

Steps:
1. Import the vision bridge
2. Create your vision functions (load_image, zoom_in, etc.)
3. Register them with the bridge
4. Run the audio assistant

The audio assistant will then call your functions when voice commands are recognized.
"""

import cv2
import numpy as np
from audio_engine.vision_bridge import get_bridge

# Import AudioAssistant if available; otherwise fall back to a light mock so example runs without heavy deps
try:
    from main_audio import AudioAssistant
except Exception:
    class AudioAssistant:
        def __init__(self):
            pass
        def start(self, interactive: bool = False):
            print("🎙️ (mock) Starting voice-controlled image viewer — audio stack not installed")
            print("Say commands like: 'Open patient file', 'Show CT scan', 'Zoom in', 'Zoom out', 'Reset view', 'Highlight abnormalities'")

class SimpleImageViewer:
    """
    Example image viewer that responds to voice commands.
    Replace this with your actual vision system.
    """
    def __init__(self):
        self.current_image = None
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.image_list = []
        self.current_index = 0
        
    def load_image(self, image_path):
        """Load an image from disk."""
        try:
            self.current_image = cv2.imread(image_path)
            if self.current_image is not None:
                print(f"✅ Loaded image: {image_path}")
                # Update state manager
                bridge = get_bridge()
                if bridge.state_manager:
                    bridge.state_manager.update_state("is_image_loaded", True)
                return True
            return False
        except Exception as e:
            print(f"❌ Failed to load image: {e}")
            return False
    
    def zoom_in(self, factor=1.2):
        """Zoom in on the image."""
        if self.current_image is None:
            return False
        self.zoom_level *= factor
        print(f"🔍 Zoomed in to {self.zoom_level:.2f}x")
        # Here you would update your display
        return True
    
    def zoom_out(self, factor=0.8):
        """Zoom out on the image."""
        if self.current_image is None:
            return False
        self.zoom_level *= factor
        print(f"🔍 Zoomed out to {self.zoom_level:.2f}x")
        return True
    
    def scroll(self, direction, amount):
        """Scroll/pan the image."""
        if self.current_image is None:
            return False
        
        if direction == "left":
            self.pan_x -= amount
        elif direction == "right":
            self.pan_x += amount
        elif direction == "up":
            self.pan_y -= amount
        elif direction == "down":
            self.pan_y += amount
        
        print(f"📜 Scrolled {direction} by {amount}px (pan: {self.pan_x}, {self.pan_y})")
        return True
    
    def next_image(self):
        """Load next image in list."""
        if not self.image_list:
            return False
        self.current_index = (self.current_index + 1) % len(self.image_list)
        return self.load_image(self.image_list[self.current_index])
    
    def prev_image(self):
        """Load previous image in list."""
        if not self.image_list:
            return False
        self.current_index = (self.current_index - 1) % len(self.image_list)
        return self.load_image(self.image_list[self.current_index])
    
    def reset_view(self):
        """Reset zoom and pan."""
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        print("🔄 View reset")
        return True

def main(interactive: bool = False):
    """
    Example integration main function.
    """
    # 1. Create your vision system
    viewer = SimpleImageViewer()
    
    # 2. Get the bridge
    bridge = get_bridge()
    
    # 3. Register your callbacks
    bridge.register_vision_callbacks({
        "load_image": viewer.load_image,
        "zoom_in": viewer.zoom_in,
        "zoom_out": viewer.zoom_out,
        "scroll": viewer.scroll,
        "next_image": viewer.next_image,
        "prev_image": viewer.prev_image,
        "reset_view": viewer.reset_view,
    })
    
    # 4. Auto-load sample images from ./samples (if present)
    import glob, os
    samples_dir = os.path.join(os.path.dirname(__file__), "samples")
    if os.path.isdir(samples_dir):
        imgs = sorted(glob.glob(os.path.join(samples_dir, "*.jpg")) + glob.glob(os.path.join(samples_dir, "*.png")))
        if imgs:
            viewer.image_list = imgs
            print(f"✅ Loaded {len(imgs)} sample images from {samples_dir}")
        else:
            print(f"No images found in {samples_dir} (supported: .jpg, .png)")
    else:
        print(f"Tip: Create a folder at {samples_dir} and put .jpg/.png images there to auto-load them.")

    # 5. Start the audio assistant
    print("🎙️ Starting voice-controlled image viewer...")
    print("Say commands like: 'Open patient file', 'Show CT scan', 'Zoom in', 'Zoom out', 'Reset view', 'Highlight abnormalities'")

    assistant = AudioAssistant()
    assistant.start(interactive=interactive)

    if interactive:
        print("Interactive assistant started. Type commands or 'exit' to quit")
    else:
        print("Example viewer started (assistant in non-interactive mode). To try interactive mode run: `python example_vision_integration.py --interactive`")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Example Vision Integration')
    parser.add_argument('--interactive', action='store_true', help='Start assistant in interactive REPL mode')
    args = parser.parse_args()
    main(interactive=args.interactive)
