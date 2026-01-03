import cv2
import mediapipe as mp
import numpy as np
import pyautogui

# ---------------- FACE MESH SETUP ----------------
mp_face = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles

face_mesh = mp_face.FaceMesh(
    refine_landmarks=True,
    max_num_faces=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# ---------------- CAMERA ----------------
cap = cv2.VideoCapture(0)

# ---------------- FULLSCREEN WINDOW ----------------
WINDOW_NAME = "Eye + Head Gaze Tracking"

cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(
    WINDOW_NAME,
    cv2.WND_PROP_FULLSCREEN,
    cv2.WINDOW_FULLSCREEN
)

# ---------------- LANDMARK INDICES ----------------
LEFT_EYE_CORNERS = [33, 133]
LEFT_IRIS = [468, 469, 470, 471]

RIGHT_EYE_CORNERS = [362, 263]
RIGHT_IRIS = [473, 474, 475, 476]

POSE_LANDMARKS = {
    "nose": 1,
    "chin": 152,
    "left_eye": 33,
    "right_eye": 263,
    "left_mouth": 61,
    "right_mouth": 291
}

# ---------------- CAMERA MATRIX ----------------
FOCAL_LENGTH = 800
CENTER = (640, 360)

CAM_MATRIX = np.array([
    [FOCAL_LENGTH, 0, CENTER[0]],
    [0, FOCAL_LENGTH, CENTER[1]],
    [0, 0, 1]
], dtype="double")

DIST_COEFFS = np.zeros((4, 1))

# ---------------- CURSOR SETTINGS ----------------
SCREEN_W, SCREEN_H = pyautogui.size()
CURSOR_STEP = 15   # change if you want faster/slower movement

# ---------------- MAIN LOOP ----------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = face_mesh.process(rgb)

    eye_text = "EYES: --"
    head_text = "HEAD: --"

    if result.multi_face_landmarks:
        face = result.multi_face_landmarks[0]

        # -------- FACE MESH --------
        mp_drawing.draw_landmarks(
            frame,
            face,
            mp_face.FACEMESH_TESSELATION,
            None,
            mp_styles.get_default_face_mesh_tesselation_style()
        )
        mp_drawing.draw_landmarks(
            frame,
            face,
            mp_face.FACEMESH_CONTOURS,
            None,
            mp_styles.get_default_face_mesh_contours_style()
        )

        # -------- EYE LOGIC --------
        left_eye_left = np.array([
            face.landmark[LEFT_EYE_CORNERS[0]].x * w,
            face.landmark[LEFT_EYE_CORNERS[0]].y * h
        ])
        left_eye_right = np.array([
            face.landmark[LEFT_EYE_CORNERS[1]].x * w,
            face.landmark[LEFT_EYE_CORNERS[1]].y * h
        ])

        left_iris = np.mean([
            [face.landmark[i].x * w, face.landmark[i].y * h]
            for i in LEFT_IRIS
        ], axis=0)

        right_eye_left = np.array([
            face.landmark[RIGHT_EYE_CORNERS[0]].x * w,
            face.landmark[RIGHT_EYE_CORNERS[0]].y * h
        ])
        right_eye_right = np.array([
            face.landmark[RIGHT_EYE_CORNERS[1]].x * w,
            face.landmark[RIGHT_EYE_CORNERS[1]].y * h
        ])

        right_iris = np.mean([
            [face.landmark[i].x * w, face.landmark[i].y * h]
            for i in RIGHT_IRIS
        ], axis=0)

        for i in LEFT_IRIS + RIGHT_IRIS:
            x = int(face.landmark[i].x * w)
            y = int(face.landmark[i].y * h)
            cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

        left_ratio = (left_iris[0] - left_eye_left[0]) / (
            left_eye_right[0] - left_eye_left[0] + 1e-6
        )
        right_ratio = (right_iris[0] - right_eye_left[0]) / (
            right_eye_right[0] - right_eye_left[0] + 1e-6
        )

        gaze_ratio = (left_ratio + right_ratio) / 2

        if gaze_ratio < 0.4:
            eye_text = "EYES: LEFT"
        elif gaze_ratio > 0.6:
            eye_text = "EYES: RIGHT"
        else:
            eye_text = "EYES: CENTER"
        # -------- FAST CURSOR MOVEMENT (EYES ONLY) --------
        CENTER_X = SCREEN_W // 2
        CENTER_Y = SCREEN_H // 2

        mouse_x, mouse_y = pyautogui.position()

        if eye_text == "EYES: LEFT":
            pyautogui.moveTo(0, mouse_y, duration=0.05)   # FAST to left

        elif eye_text == "EYES: RIGHT":
            pyautogui.moveTo(SCREEN_W - 1, mouse_y, duration=0.05)  # FAST to right

        elif eye_text == "EYES: CENTER":
            pyautogui.moveTo(CENTER_X, CENTER_Y, duration=0.05)  # SNAP to center

        # -------- HEAD LOGIC --------
        image_points = np.array([
            (face.landmark[POSE_LANDMARKS["nose"]].x * w,
             face.landmark[POSE_LANDMARKS["nose"]].y * h),
            (face.landmark[POSE_LANDMARKS["chin"]].x * w,
             face.landmark[POSE_LANDMARKS["chin"]].y * h),
            (face.landmark[POSE_LANDMARKS["left_eye"]].x * w,
             face.landmark[POSE_LANDMARKS["left_eye"]].y * h),
            (face.landmark[POSE_LANDMARKS["right_eye"]].x * w,
             face.landmark[POSE_LANDMARKS["right_eye"]].y * h),
            (face.landmark[POSE_LANDMARKS["left_mouth"]].x * w,
             face.landmark[POSE_LANDMARKS["left_mouth"]].y * h),
            (face.landmark[POSE_LANDMARKS["right_mouth"]].x * w,
             face.landmark[POSE_LANDMARKS["right_mouth"]].y * h)
        ], dtype="double")

        model_points = np.array([
            (0.0, 0.0, 0.0),
            (0.0, -330.0, -65.0),
            (-225.0, 170.0, -135.0),
            (225.0, 170.0, -135.0),
            (-150.0, -150.0, -125.0),
            (150.0, -150.0, -125.0)
        ])

        _, rot_vec, _ = cv2.solvePnP(
            model_points,
            image_points,
            CAM_MATRIX,
            DIST_COEFFS,
            flags=cv2.SOLVEPNP_ITERATIVE
        )

        rmat, _ = cv2.Rodrigues(rot_vec)
        angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)

        yaw = angles[1]
        yaw = max(min(yaw, 20), -20)

        YAW_THRESH = 6

        if yaw > YAW_THRESH:
            head_text = "HEAD: LEFT"
        elif yaw < -YAW_THRESH:
            head_text = "HEAD: RIGHT"
        else:
            head_text = "HEAD: CENTER"

    # -------- DISPLAY --------
    cv2.putText(frame, head_text, (40, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 255), 3)

    cv2.putText(frame, eye_text, (40, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 1.3, (255, 0, 0), 3)

    cv2.imshow(WINDOW_NAME, frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
