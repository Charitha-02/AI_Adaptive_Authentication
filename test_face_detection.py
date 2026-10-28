
from pathlib import Path
import cv2

# Get the project folder automatically
PROJECT_ROOT = Path(__file__).resolve().parent

print("OpenCV version:", cv2.__version__)
print("Project folder:", PROJECT_ROOT)

# Check possible locations for the Haar Cascade XML file
cascade_paths = [
    PROJECT_ROOT / "models" / "haarcascade_frontalface_default.xml",
    Path(cv2.__file__).resolve().parent / "data" / "haarcascade_frontalface_default.xml",
]

face_cascade = None

for cascade_path in cascade_paths:
    print("Checking cascade:", cascade_path)

    if cascade_path.is_file():
        detector = cv2.CascadeClassifier(str(cascade_path))

        if not detector.empty():
            face_cascade = detector
            print("Cascade loaded successfully!")
            break

if face_cascade is None:
    print("\nERROR: Haar Cascade XML file was not found.")
    print("Please check the models folder or reinstall OpenCV.")
    raise SystemExit(1)

# Open the webcam
camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# Fall back to the default backend if necessary
if not camera.isOpened():
    camera.release()
    camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Could not open webcam.")
    raise SystemExit(1)

print("\nWebcam opened.")
print("Keep your face visible and well-lit.")
print("Press Q to quit.")

while True:
    success, frame = camera.read()

    if not success or frame is None:
        print("ERROR: Could not read webcam frame.")
        break

    # Mirror the image for easier positioning
    frame = cv2.flip(frame, 1)

    # Convert frame to grayscale and improve contrast
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    # Detect faces
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.05,
        minNeighbors=3,
        minSize=(30, 30)
    )

    # Draw a rectangle around every detected face
    for (x, y, w, h) in faces:
        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )

    if len(faces) > 0:
        message = "FACE DETECTED"
        color = (0, 255, 0)
    else:
        message = "NO FACE DETECTED"
        color = (0, 0, 255)

    cv2.putText(
        frame,
        message,
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        color,
        2
    )

    cv2.imshow("Face Detection Test", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
