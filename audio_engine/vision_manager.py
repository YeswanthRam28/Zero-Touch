import cv2
import mediapipe as mp
import numpy as np
import threading
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("VisionManager")

try:
    from mediapipe.python.solutions import face_mesh as mp_face_mesh
    from mediapipe.python.solutions import hands as mp_hands
    from mediapipe.python.solutions import drawing_utils as mp_drawing
except ImportError:
    import mediapipe.solutions.face_mesh as mp_face_mesh
    import mediapipe.solutions.hands as mp_hands
    import mediapipe.solutions.drawing_utils as mp_drawing

class VisionManager:
    """
    Combines Eye Gaze and Hand Gesture tracking into a single unified stream.
    Runs in a background thread to maintain high FPS regardless of ASR/LLM load.
    """
    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.running = False
        self.thread = None
        self.cap = None
        self.new_camera_id = None
        
        # State
        self.current_state = {
            "gaze": {"eye": "CENTER", "head": "CENTER", "yaw": 0.0},
            "hand": {"pose": "UNKNOWN", "gesture": "NONE", "pinch_delta": 0.0, "cursor": [0, 0]},
            "user_present": False,
            "fps": 0.0,
            "timestamp": 0.0
        }
        
        # MediaPipe Setup
        self.face_mesh = mp_face_mesh.FaceMesh(
            refine_landmarks=True,
            max_num_faces=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        
        self.hands = mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        
        # Indices and Constants
        self.LEFT_IRIS = [468, 469, 470, 471]
        self.RIGHT_IRIS = [473, 474, 475, 476]
        self.LEFT_EYE_CORNERS = [33, 133]
        self.RIGHT_EYE_CORNERS = [362, 263]
        
        self.POSE_LANDMARKS = {"nose": 1, "chin": 152, "left_eye": 33, "right_eye": 263, "left_mouth": 61, "right_mouth": 291}
        self.MODEL_POINTS = np.array([
            (0.0, 0.0, 0.0), (0.0, -330.0, -65.0), (-225.0, 170.0, -135.0), 
            (225.0, 170.0, -135.0), (-150.0, -150.0, -125.0), (150.0, -150.0, -125.0)
        ])
        self.FOCAL_LENGTH = 800
        self.CENTER = (640, 360)
        self.CAM_MATRIX = np.array([[self.FOCAL_LENGTH, 0, self.CENTER[0]], [0, self.FOCAL_LENGTH, self.CENTER[1]], [0, 0, 1]], dtype="double")
        self.DIST_COEFFS = np.zeros((4, 1))

        # Internal tracking
        self._prev_pinch_dist = 0
        self._prev_hand_x = 0
        self._hand_x_history = []
        self._hand_history_size = 5
        self._last_swipe_time = 0

    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("Vision Manager started background thread.")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        if self.cap:
            self.cap.release()
        logger.info("Vision Manager stopped.")

    def switch_camera(self, new_id):
        """Signal the background thread to switch cameras."""
        self.new_camera_id = new_id
        logger.info(f"Vision Manager: Requesting camera switch to ID {new_id}")

    def get_state(self) -> Dict[str, Any]:
        return self.current_state.copy()

    def _run_loop(self):
        self.cap = cv2.VideoCapture(self.camera_id)
        
        last_time = time.time()
        
        while self.running:
            # Check for camera switch request
            if self.new_camera_id is not None:
                logger.info(f"Switching camera from {self.camera_id} to {self.new_camera_id}")
                if self.cap: self.cap.release()
                self.camera_id = self.new_camera_id
                self.cap = cv2.VideoCapture(self.camera_id)
                self.new_camera_id = None
                if not self.cap.isOpened():
                    logger.error(f"Failed to open camera {self.camera_id}")
                    continue

            if not self.cap or not self.cap.isOpened():
                time.sleep(0.5)
                continue

            ret, frame = self.cap.read()
            if not ret: break
            
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process Face and Hands
            face_results = self.face_mesh.process(rgb)
            hand_results = self.hands.process(rgb)
            
            new_state = {
                "gaze": self.current_state["gaze"],
                "hand": self.current_state["hand"],
                "user_present": False,
                "fps": 0.0,
                "timestamp": time.time()
            }

            # 1. Handle Gaze (Face Mesh)
            if face_results.multi_face_landmarks:
                new_state["user_present"] = True
                face = face_results.multi_face_landmarks[0]
                self._process_gaze(face, w, h, new_state["gaze"])

            # 2. Handle Hands
            if hand_results.multi_hand_landmarks:
                hand = hand_results.multi_hand_landmarks[0]
                self._process_hand(hand, w, h, new_state["hand"])
            else:
                new_state["hand"]["pose"] = "NONE"
                new_state["hand"]["gesture"] = "NONE"

            # Compute FPS
            now = time.time()
            new_state["fps"] = 1.0 / (now - last_time + 1e-6)
            last_time = now
            
            self.current_state = new_state
            
            # Small sleep to be CPU friendly, though Mediapipe is the bottleneck
            time.sleep(0.01)

        if self.cap:
            self.cap.release()

    def _process_gaze(self, face, w, h, gaze_state):
        # Iris Logic
        li = np.mean([[face.landmark[i].x * w, face.landmark[i].y * h] for i in self.LEFT_IRIS], axis=0)
        ri = np.mean([[face.landmark[i].x * w, face.landmark[i].y * h] for i in self.RIGHT_IRIS], axis=0)
        
        # Ratios (simplified)
        ll = face.landmark[self.LEFT_EYE_CORNERS[0]].x * w
        lr = face.landmark[self.LEFT_EYE_CORNERS[1]].x * w
        rl = face.landmark[self.RIGHT_EYE_CORNERS[0]].x * w
        rr = face.landmark[self.RIGHT_EYE_CORNERS[1]].x * w
        
        l_ratio = (li[0] - ll) / (lr - ll + 1e-6)
        r_ratio = (ri[0] - rl) / (rr - rl + 1e-6)
        ratio = (l_ratio + r_ratio) / 2
        
        if ratio < 0.4: gaze_state["eye"] = "LEFT"
        elif ratio > 0.6: gaze_state["eye"] = "RIGHT"
        else: gaze_state["eye"] = "CENTER"

        # Head Logic
        image_pts = np.array([(face.landmark[self.POSE_LANDMARKS[k]].x * w, face.landmark[self.POSE_LANDMARKS[k]].y * h) for k in ["nose", "chin", "left_eye", "right_eye", "left_mouth", "right_mouth"]], dtype="double")
        _, rv, _ = cv2.solvePnP(self.MODEL_POINTS, image_pts, self.CAM_MATRIX, self.DIST_COEFFS, flags=cv2.SOLVEPNP_ITERATIVE)
        rmat, _ = cv2.Rodrigues(rv)
        angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)
        yaw = angles[1]
        gaze_state["yaw"] = yaw
        
        if yaw > 6: gaze_state["head"] = "LEFT"
        elif yaw < -6: gaze_state["head"] = "RIGHT"
        else: gaze_state["head"] = "CENTER"

    def _process_hand(self, hand, w, h, hand_state):
        landmarks = hand.landmark
        
        # 1. Determine which fingers are extended
        p0 = landmarks[0] # Wrist
        p17 = landmarks[17] # Pinky Base
        finger_stats = []
        
        # --- Thumb (landmark 4) ---
        d_thumb_tip = np.hypot(landmarks[4].x - p17.x, landmarks[4].y - p17.y)
        d_thumb_base = np.hypot(landmarks[2].x - p17.x, landmarks[2].y - p17.y)
        thumb_extended = d_thumb_tip > d_thumb_base * 1.2
        
        # --- Other Fingers (8, 12, 16, 20) ---
        tips = [8, 12, 16, 20]
        pips = [6, 10, 14, 18]
        for t, p in zip(tips, pips):
            d_tip = np.hypot(landmarks[t].x - p0.x, landmarks[t].y - p0.y)
            d_pip = np.hypot(landmarks[p].x - p0.x, landmarks[p].y - p0.y)
            finger_stats.append(d_tip > d_pip * 1.15)
            
        index, middle, ring, pinky = finger_stats
        
        # 2. Pose Hierarchy
        pose = "UNKNOWN"
        if thumb_extended and all(finger_stats):
            pose = "OPEN_PALM"
        elif not thumb_extended and not any(finger_stats):
            pose = "FIST"
        elif thumb_extended and index and not any([middle, ring, pinky]):
            pose = "L_SHAPE"
        elif index and not thumb_extended and not any([middle, ring, pinky]):
            pose = "INDEX_POINTING"
        elif thumb_extended and not any(finger_stats):
            pose = "THUMB_POINTING"
        elif pinky and not any([thumb_extended, index, middle, ring]):
            pose = "PINKY_POINTING"
            
        hand_state["pose"] = pose

        # Gestures
        idx_tip = landmarks[8]
        thumb_tip = landmarks[4]
        hand_state["cursor"] = [int(idx_tip.x * w), int(idx_tip.y * h)]
        
        # --- Robust Swipe Detection ---
        current_x = idx_tip.x * w
        self._hand_x_history.append(current_x)
        if len(self._hand_x_history) > self._hand_history_size:
            self._hand_x_history.pop(0)

        # Only check for swipe if we have enough history and we are in L_SHAPE or OPEN_PALM
        gesture = "NONE"
        if len(self._hand_x_history) == self._hand_history_size and pose in ["L_SHAPE", "OPEN_PALM"]:
            # Check for a consistent movement trend
            delta = self._hand_x_history[-1] - self._hand_x_history[0]
            velocity = delta / self._hand_history_size
            
            if abs(velocity) > 15: # Lower threshold because it's averaged
                now = time.time()
                if now - self._last_swipe_time > 1.2: # Internal debounce
                    gesture = "SWIPE_RIGHT" if velocity > 0 else "SWIPE_LEFT"
                    self._last_swipe_time = now
                    # Clear history to prevent multiple triggers from one motion
                    self._hand_x_history = []
        
        hand_state["gesture"] = gesture

        # Pinch Based Zoom
        pinch_dist = np.hypot(thumb_tip.x - idx_tip.x, thumb_tip.y - idx_tip.y) * w
        hand_state["pinch_dist"] = pinch_dist
        
        # Only allow pinch if Index and Thumb are open, and others are closed (or it's just a general pinch pose)
        if self._prev_pinch_dist > 0:
            delta = pinch_dist - self._prev_pinch_dist
            if abs(delta) > 5: # Minimal change to register
                hand_state["pinch_delta"] = delta
            else:
                hand_state["pinch_delta"] = 0.0
        self._prev_pinch_dist = pinch_dist

if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    vm = VisionManager()
    vm.start()
    try:
        for _ in range(50):
            print(vm.get_state())
            time.sleep(0.5)
    finally:
        vm.stop()
