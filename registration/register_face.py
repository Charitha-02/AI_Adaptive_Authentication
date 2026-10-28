import cv2
import sqlite3
import os
import sys
import time

print("Python Executable:", sys.executable)
print("OpenCV Version:", cv2.__version__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)

DB_PATH = os.path.join(BASE_DIR, "database", "users.db")
FACE_ROOT = os.path.join(BASE_DIR, "storage", "face_data")
CASCADE_PATH = os.path.join(BASE_DIR, "models", "haarcascade_frontalface_default.xml")
TOTAL_IMAGES = 30
SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp")

# Load face detector.
if os.path.exists(CASCADE_PATH):
    face_detector = cv2.CascadeClassifier(CASCADE_PATH)
else:
    face_detector = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

if face_detector.empty():
    print("ERROR: Face detection model could not be loaded.")
    sys.exit(1)

# Get and normalize email.
email = (
    sys.argv[1].strip().lower()
    if len(sys.argv) > 1
    else input("Enter Registered Email: ").strip().lower()
)
if not email:
    print("ERROR: Email cannot be empty.")
    sys.exit(1)

if not os.path.exists(DB_PATH):
    print(f"ERROR: Database not found: {DB_PATH}")
    sys.exit(1)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute("SELECT email FROM users WHERE LOWER(email)=?", (email,))
    user = cursor.fetchone()
except sqlite3.Error as exc:
    print("ERROR: Could not query users table:", exc)
    conn.close()
    sys.exit(1)

if not user:
    print("ERROR: User not found!")
    conn.close()
    sys.exit(1)

# Use the canonical email from the database, normalized to lowercase.
email = str(user[0]).strip().lower()
os.makedirs(FACE_ROOT, exist_ok=True)

# Reuse an existing folder case-insensitively so images do not split across folders.
folder = None
for existing_name in os.listdir(FACE_ROOT):
    existing_path = os.path.join(FACE_ROOT, existing_name)
    if os.path.isdir(existing_path) and existing_name.lower() == email:
        folder = existing_path
        break
if folder is None:
    folder = os.path.join(FACE_ROOT, email)
    os.makedirs(folder, exist_ok=True)

print("Opening camera...")
cam = cv2.VideoCapture(0, cv2.CAP_DSHOW) if os.name == "nt" else cv2.VideoCapture(0)
if not cam.isOpened():
    cam.release()
    cam = cv2.VideoCapture(0)

if not cam.isOpened():
    print("ERROR: Camera could not be opened. Check camera permissions and close other apps using it.")
    conn.close()
    sys.exit(1)

cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("Camera opened successfully.")
print("Look at the camera and move your head slightly between captures.")
print("Press ESC to cancel registration.")

# Keep the existing capture behavior but use unique filenames so old images are not
# accidentally overwritten when registration is repeated.
existing_indices = []
for name in os.listdir(folder):
    stem, ext = os.path.splitext(name)
    if ext.lower() in SUPPORTED_EXTENSIONS and stem.isdigit():
        existing_indices.append(int(stem))
next_index = max(existing_indices, default=-1) + 1

count = 0
last_capture = 0.0
CAPTURE_INTERVAL = 0.20

try:
    while count < TOTAL_IMAGES:
        ret, frame = cam.read()
        if not ret:
            print("ERROR: Could not read frame from camera.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
        )

        if len(faces) > 0:
            # Only capture the largest detected face.
            x, y, w, h = max(faces, key=lambda box: box[2] * box[3])
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(
                frame, f"Captured: {count}/{TOTAL_IMAGES}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2
            )

            now = time.time()
            if now - last_capture >= CAPTURE_INTERVAL:
                face = gray[y:y + h, x:x + w]
                face = cv2.resize(face, (200, 200), interpolation=cv2.INTER_AREA)
                filename = os.path.join(folder, f"{next_index + count}.jpg")
                if cv2.imwrite(filename, face):
                    count += 1
                    last_capture = now
                else:
                    print("WARNING: Could not save a captured face image.")
        else:
            cv2.putText(
                frame, "No face detected", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2
            )

        cv2.imshow("Face Registration - Look at Camera", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            print("Face registration cancelled by user.")
            break

finally:
    cam.release()
    cv2.destroyAllWindows()
    cv2.waitKey(1)
    time.sleep(0.3)

if count >= TOTAL_IMAGES:
    try:
        cursor.execute(
            "UPDATE users SET face_registered=1 WHERE LOWER(email)=?",
            (email,)
        )
        conn.commit()
        print("Face Registration Completed!")
        print(f"Images captured: {count}")
        print(f"Saved in: {folder}")
        print("Next run: python authentication/train_model.py")
        conn.close()
        sys.exit(0)
    except sqlite3.Error as exc:
        print("ERROR: Could not update face_registered:", exc)
        conn.close()
        sys.exit(1)
else:
    print("Face Registration Incomplete.")
    print(f"Captured {count}/{TOTAL_IMAGES} new images. Existing images were not deleted.")
    conn.close()
    sys.exit(1)
