import cv2
import face_recognition
import numpy as np

import face_recognition
print("Face recognition is ready!")

# Start webcam
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detect face locations and landmarks
    face_locations = face_recognition.face_locations(rgb_frame)
    face_landmarks_list = face_recognition.face_landmarks(rgb_frame, face_locations)

    for landmarks in face_landmarks_list:
        def draw_poly(feature, color):
            if feature in landmarks:
                points = np.array(landmarks[feature], dtype=np.int32)
                cv2.polylines(frame, [points], isClosed=False, color=color, thickness=2)

        # Draw features with different colors
        draw_poly("chin", (255, 0, 0))              # Jawline - Blue
        draw_poly("left_eyebrow", (0, 255, 0))       # Left eyebrow - Green
        draw_poly("right_eyebrow", (0, 255, 0))      # Right eyebrow - Green
        draw_poly("nose_bridge", (128, 0, 128))      # Nose bridge - Purple
        draw_poly("nose_tip", (128, 0, 128))         # Nose tip - Purple
        draw_poly("top_lip", (0, 0, 255))            # Top lip - Red
        draw_poly("bottom_lip", (0, 0, 255))         # Bottom lip - Red
        draw_poly("left_eye", (255, 255, 0))         # Left eye - Cyan
        draw_poly("right_eye", (255, 255, 0))        # Right eye - Cyan

    cv2.imshow("Facial Features Viewer", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
