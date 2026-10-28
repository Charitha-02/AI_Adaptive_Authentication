import cv2
import os

MODEL = "models/trainer.yml"
CASCADE = "models/haarcascade_frontalface_default.xml"

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read(MODEL)

cascade = cv2.CascadeClassifier(CASCADE)

print("Model loaded:", os.path.exists(MODEL))
print("Cascade loaded:", not cascade.empty())

cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cam.isOpened():
    cam = cv2.VideoCapture(0)

if not cam.isOpened():
    print("Camera could not be opened")
    exit()

print("\nCamera opened.")
print("Look directly at the camera.")
print("Press ESC to stop.\n")

while True:

    ret, frame = cam.read()

    if not ret:
        print("Could not read frame")
        break

    frame = cv2.flip(frame, 1)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.05,
        minNeighbors=3,
        minSize=(40, 40)
    )

    for (x, y, w, h) in faces:

        face = gray[y:y+h, x:x+w]

        label, confidence = recognizer.predict(face)

        print(
            f"Predicted label: {label} | Confidence: {confidence:.2f}"
        )

        cv2.rectangle(
            frame,
            (x, y),
            (x+w, y+h),
            (0, 255, 0),
            3
        )

        cv2.putText(
            frame,
            f"Label: {label}",
            (x, y - 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Confidence: {confidence:.1f}",
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

    cv2.imshow("Face Recognition Test", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == 27:
        break

cam.release()
cv2.destroyAllWindows()