import cv2
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")

cascade = cv2.CascadeClassifier(
    os.path.join(MODEL_DIR, "haarcascade_frontalface_default.xml")
)

if cascade.empty():
    raise SystemExit("Error: Haar Cascade could not be loaded.")

if not hasattr(cv2, "face"):
    raise SystemExit("Error: Install opencv-contrib-python.")

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read(os.path.join(MODEL_DIR, "trainer.yml"))

labels = {}
with open(
    os.path.join(MODEL_DIR, "labels.txt"),
    "r",
    encoding="utf-8"
) as f:
    for line in f:
        label, email = line.strip().split(",", 1)
        labels[int(label)] = email

# Temporary threshold for testing; calibrate using actual results.
CONFIDENCE_THRESHOLD = 70

cam = cv2.VideoCapture(0)

if not cam.isOpened():
    raise SystemExit("Error: Webcam could not be opened.")

try:
    while True:
        ret, frame = cam.read()

        if not ret:
            print("Could not read webcam frame.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = cascade.detectMultiScale(
            gray,
            scaleFactor=1.3,
            minNeighbors=5,
            minSize=(60, 60)
        )

        for (x, y, w, h) in faces:
            face = gray[y:y + h, x:x + w]
            face = cv2.resize(face, (200, 200))

            label, confidence = recognizer.predict(face)

            if (
                label in labels
                and confidence < CONFIDENCE_THRESHOLD
            ):
                name = labels[label]
                color = (0, 180, 0)
            else:
                name = "Unknown"
                color = (0, 0, 255)

            cv2.rectangle(
                frame, (x, y), (x + w, y + h), color, 2
            )

            cv2.putText(
                frame,
                f"{name} | Distance: {confidence:.1f}",
                (x, max(y - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )

        cv2.imshow("Face Recognition Test", frame)

        if cv2.waitKey(1) == 27:
            break

finally:
    cam.release()
    cv2.destroyAllWindows()