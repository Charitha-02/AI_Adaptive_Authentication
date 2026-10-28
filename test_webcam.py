
import cv2
import time

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("ERROR: Webcam could not be opened.")
    raise SystemExit

# Give the camera a moment to initialize
time.sleep(1)

for _ in range(5):
    cap.read()

while True:
    ret, frame = cap.read()

    if not ret or frame is None:
        print("ERROR: Could not read webcam frame.")
        break

    if frame.size == 0:
        print("ERROR: Empty webcam frame.")
        break

    cv2.imshow("Webcam Test - Press Q to Exit", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
