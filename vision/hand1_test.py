import cv2
import mediapipe as mp
import math
import time
import numpy as np
import pyautogui

# Optional: Disable fail-safe if you find it triggering too easily, 
# but keep it enabled for safety during development usually.
# pyautogui.FAILSAFE = False

# --- Configuration ---
MIN_DETECTION_CONFIDENCE = 0.7
MIN_TRACKING_CONFIDENCE = 0.7
SWIPE_THRESHOLD_VELOCITY = 30  # pixels per frame approx, tune based on fps
PINCH_THRESHOLD_DELTA = 10      # minimal change to register zoom
SMOOTHING_FACTOR = 1           # 1 = No smoothing (instant), Higher = Smoother
FRAME_REDUCTION = 0            # 0 = Entire frame maps to screen (1:1 visual alignment)

# Colors for UI
COLOR_TEXT = (255, 255, 255)
COLOR_HAND = (0, 255, 0)
COLOR_ALERT = (0, 0, 255)

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

def calculate_distance(p1, p2):
    """Euclidean distance between two landmarks (normalized or pixel)."""
    return math.hypot(p1.x - p2.x, p1.y - p2.y)

def is_finger_open(tip, pip, mcp, hand_orientation='up'):
    """
    Check if a finger is open (extended).
    Simple logic: Tip is higher (lower y) than PIP for upright hand.
    """
    # Note: In screen coordinates, y increases downwards.
    # So "higher" visually means smaller y value.
    if hand_orientation == 'up':
        return tip.y < pip.y
    return False

def get_hand_state(landmarks, width, height):
    """
    Analyze landmarks to determine open/closed state of each finger.
    Returns: list of booleans [Thumb, Index, Middle, Ring, Pinky]
    """
    # Landmark indices
    # Thumb: 4 (Tip), 3 (IP), 2 (MCP) -- Thumb is special, moves laterally
    # Index: 8 (Tip), 6 (PIP)
    # Middle: 12 (Tip), 10 (PIP)
    # Ring: 16 (Tip), 14 (PIP)
    # Pinky: 20 (Tip), 18 (PIP)
    
    fingers_open = []
    
    # 1. Thumb Analysis
    # Thumb is open if tip is further from the pinky MCP (17) than the thumb IP (3) is.
    # This works for general open/closed generic status.
    p4 = landmarks[4]
    p3 = landmarks[3]
    p17 = landmarks[17]
    
    dist_tip_pinky = calculate_distance(p4, p17)
    dist_ip_pinky = calculate_distance(p3, p17)
    
    # Heuristic: Thumb open if tip is far from palm (pinky base)
    fingers_open.append(dist_tip_pinky > dist_ip_pinky)

    # 2. Other Fingers
    finger_tips = [8, 12, 16, 20]
    finger_pips = [6, 10, 14, 18]
    
    # Assuming hand is roughly upright for medical gestures
    # Refine logic: check distance from wrist (0) to tip vs wrist to PIP
    # This is rotation invariant-ish for open/close
    p0 = landmarks[0]
    
    for tip_idx, pip_idx in zip(finger_tips, finger_pips):
        tip = landmarks[tip_idx]
        pip = landmarks[pip_idx]
        
        d_tip = calculate_distance(p0, tip)
        d_pip = calculate_distance(p0, pip)
        
        # If tip is further from wrist than PIP, it's extended
        fingers_open.append(d_tip > d_pip)
        
    return fingers_open

def main():
    cap = cv2.VideoCapture(0)
    
    # State tracking variables
    prev_x = 0
    prev_pinch_dist = 0
    
    # Cursor Control Variables
    screen_w, screen_h = pyautogui.size()
    plocX, plocY = 0, 0  # Previous Location X, Y for smoothing
    clocX, clocY = 0, 0  # Current Location X, Y
    
    # Setup Window for Fullscreen
    cv2.namedWindow('Surgical Hand Control', cv2.WINDOW_NORMAL)
    cv2.setWindowProperty('Surgical Hand Control', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    
    with mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=MIN_TRACKING_CONFIDENCE
    ) as hands:
        
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                continue

            # Flip image for selfie-view mirroring
            image = cv2.flip(image, 1)
            h, w, c = image.shape
            
            # Convert to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = hands.process(image_rgb)
            
            # Draw overlay info
            status_text = "Status: Detecting..."
            action_text = ""
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    
                    # 1. Analyze Fingers
                    fingers = get_hand_state(hand_landmarks.landmark, w, h)
                    # fingers: [Thumb, Index, Middle, Ring, Pinky]
                    
                    thumb_open, index_open = fingers[0], fingers[1]
                    others_closed = not any(fingers[2:]) # Middle, Ring, Pinky must be False
                    all_open = all(fingers)
                    all_closed = not any(fingers) # All False
                    
                    # 2. Classify Static Pose
                    pose = "Unknown"
                    if all_open:
                        pose = "OPEN PALM"
                    elif all_closed:
                        pose = "CLOSED FIST"
                    elif thumb_open and index_open and others_closed:
                        pose = "L_SHAPE (Ready for Swipe)"
                    elif not thumb_open and index_open and all(fingers[2:]):
                        pose = "FOUR_FINGERS (Ready for Page Turn)"
                    elif thumb_open and index_open and not others_closed:
                         # Distinguish typical pinch pose from L-Shape
                         # often pinched fingers are close
                         pass

                    status_text = f"Pose: {pose}"

                    # 3. Dynamic Gesture Logic
                    
                    # --- Global Velocity Tracking ---
                    # Track Wrist (0) or Index Tip (8) for general horizontal movement
                    # Using Index Tip (8) gives more range
                    current_x = hand_landmarks.landmark[8].x * w
                    
                    # Calculate velocity regardless of pose
                    velocity = current_x - prev_x
                    prev_x = current_x # Update for next frame immediately

                    swiping = abs(velocity) > SWIPE_THRESHOLD_VELOCITY
                    
                    if swiping:
                        # High Velocity detected - prioritize motion gestures
                        
                        # SWIPE (L-Shape)
                        if pose == "L_SHAPE (Ready for Swipe)":
                            if velocity > 0:
                                action_text = ">>> SWIPE RIGHT >>>"
                            else:
                                action_text = "<<< SWIPE LEFT <<<"
                        
                        # PAGE TURN (Four Fingers)
                        # Relaxed check: If high velocity, and 4 fingers are open, 
                        # we prioritize Page Turn even if Thumb is slightly loose (Open Palm flickering)
                        # UNLESS it's explicitly L-Shape.
                        elif index_open and all(fingers[2:]): 
                            # Index, Middle, Ring, Pinky are OPEN.
                            # We don't strictly care about thumb if moving fast, 
                            # as "Open Palm" fast move isn't assigned another action.
                            if velocity > 0:
                                 action_text = "PAGE PREVIOUS (Right)"
                            else:
                                 action_text = "PAGE NEXT (Left)"

                    # --- ZOOM (Pinch specific) ---
                    # ONLY check Zoom if NOT swiping
                    if not swiping and not action_text: 
                        # Interaction: "towards pinch is zoom out and away from pinch action is zoom in"
                        p4 = hand_landmarks.landmark[4]
                        p8 = hand_landmarks.landmark[8]
                        
                        # Convert to pixel coords for easier understanding
                        cx4, cy4 = int(p4.x * w), int(p4.y * h)
                        cx8, cy8 = int(p8.x * w), int(p8.y * h)
                        
                        # visual line
                        cv2.line(image, (cx4, cy4), (cx8, cy8), (255, 0, 255), 2)
                        
                        current_pinch_dist = math.hypot(cx4 - cx8, cy4 - cy8)
                        
                        # Calculate delta if we had a previous distance
                        if prev_pinch_dist > 0:
                            delta = current_pinch_dist - prev_pinch_dist
                            
                            # Significant change check
                            if abs(delta) > PINCH_THRESHOLD_DELTA:
                                if delta > 0:
                                    # Distance increasing -> Away -> Zoom In
                                    action_text = "ZOOM IN (+)"
                                else:
                                    # Distance decreasing -> Towards -> Zoom Out
                                    action_text = "ZOOM OUT (-)"
                        
                        prev_pinch_dist = current_pinch_dist
                    else:
                        # Reset pinch dist if moving fast so we don't zoom on stop
                        prev_pinch_dist = 0

                    
                    # --- CURSOR CONTROL ---
                    # Only move cursor if NOT swiping (to avoid conflict)
                    # Use Index Finger Tip (8)
                    if index_open and not swiping:
                        x1 = hand_landmarks.landmark[8].x
                        y1 = hand_landmarks.landmark[8].y
                        
                        # Map coordinates
                        # We use a frame reduction to reach edges easier
                        
                        # Convert to screen coordinates
                        # Improving range: map a smaller window of cam to full screen
                        # x1 is 0..1. Let's remap (frame_r/w) to (1 - frame_r/w) to 0..screen_w
                        
                        try:
                            # Screen X = Map(x1, frame_r/w, 1-frame_r/w, 0, screen_w)
                            # Using numpy interp for clean mapping
                            x3 =  np.interp(x1 * w, (FRAME_REDUCTION, w - FRAME_REDUCTION), (0, screen_w))
                            y3 =  np.interp(y1 * h, (FRAME_REDUCTION, h - FRAME_REDUCTION), (0, screen_h))
                            
                            # Smoothing
                            # cloc = ploc + (target - ploc) / smoothing_factor
                            clocX = plocX + (x3 - plocX) / SMOOTHING_FACTOR
                            clocY = plocY + (y3 - plocY) / SMOOTHING_FACTOR
                            
                            pyautogui.moveTo(clocX, clocY)
                            plocX, plocY = clocX, clocY
                            
                        except Exception as e:
                            pass # Handle edge cases

            
            # Draw UI
            cv2.rectangle(image, (0, 0), (w, 80), (0, 0, 0), -1)
            cv2.putText(image, status_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, COLOR_TEXT, 2)
            
            if action_text:
                color_action = (0, 255, 255) if "SWIPE" in action_text else (255, 0, 255)
                if "PAGE" in action_text: color_action = (255, 255, 0)
                cv2.putText(image, action_text, (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color_action, 3)

            cv2.imshow('Surgical Hand Control', image)
            
            if cv2.waitKey(5) & 0xFF == 27: # Esc to exit
                break
                
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
