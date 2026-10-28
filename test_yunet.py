
import cv2
from pathlib import Path

model_path = Path("models/face_detection_yunet_2023mar.onnx")

print("OpenCV version:", cv2.__version__)
print("Model exists:", model_path.exists())
print("YuNet supported:", hasattr(cv2, "FaceDetectorYN"))

if not model_path.exists():
    print("ERROR: YuNet model file is missing.")
    raise SystemExit

if not hasattr(cv2, "FaceDetectorYN"):
    print("ERROR: This OpenCV build does not support FaceDetectorYN.")
    raise SystemExit

camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not camera.isOpened():
    camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Could not open webcam.")
    raise SystemExit

try:
    ok, frame = camera.read()

    if not ok:
        print("ERROR: Could not read webcam frame.")
        raise SystemExit

    height, width = frame.shape[:2]

    detector = cv2.FaceDetectorYN.create(
        str(model_path),
        "",
        (width, height),
        0.6,
        0.3,
        5000
    )

    _, faces = detector.detect(frame)

    if faces is None:
        print("No face detected. Try better lighting.")
    else:
        print("Faces detected:", len(faces))
        for face in faces:
            x, y, w, h = map(int, face[:4])
            print("Face box:", x, y, w, h)
            cv2.rectangle(
                frame, (x, y), (x + w, y + h), (0, 255, 0), 2
            )

    cv2.imshow("YuNet Face Detector Test", frame)
    print("Press any key while the image window is active to close.")
    cv2.waitKey(0)

finally:
    camera.release()
    cv2.destroyAllWindows()
