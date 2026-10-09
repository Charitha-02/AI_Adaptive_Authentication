
import cv2
import os
import sys
import time
import glob
import sqlite3
import statistics

# Always run from the project root so imports and relative paths work
# when Streamlit launches this file as a subprocess.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from authentication.logger import log_event

# ============================================================
# GET TARGET EMAIL
# ============================================================
email = (
    sys.argv[1].strip().lower()
    if len(sys.argv) > 1
    else input("Enter your registered email: ").strip().lower()
)

if not email:
    print("ACCESS DENIED")
    sys.exit(1)

# ============================================================
# CHECK USER
# ============================================================
try:
    conn = sqlite3.connect("database/users.db")
    cur = conn.cursor()
    cur.execute("SELECT email FROM users WHERE email=?", (email,))
    user = cur.fetchone()
    conn.close()
except Exception as e:
    print("Database error:", e)
    sys.exit(1)

if not user:
    print("User not found.")
    print("ACCESS DENIED")
    sys.exit(1)

# ============================================================
# REQUIRED FILES
# ============================================================
trainer_path = "models/trainer.yml"
labels_path = "models/labels.txt"
cascade_path = "models/haarcascade_frontalface_default.xml"
face_root = os.path.join("storage", "face_data")

if not os.path.exists(trainer_path):
    print("Face model not found.")
    print("Run: python authentication\\train_model.py")
    sys.exit(1)

if not os.path.exists(labels_path):
    print("labels.txt not found.")
    sys.exit(1)

# ============================================================
# LOAD LABELS
# ============================================================
labels = {}

try:
    with open(labels_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split(",", 1)

            if len(parts) == 2:
                try:
                    labels[int(parts[0])] = parts[1].strip().lower()
                except ValueError:
                    pass
except Exception as e:
    print("Unable to read labels.txt:", e)
    sys.exit(1)

if email not in labels.values():
    print("This email is not present in the trained face model.")
    print("Please register the face and retrain the model.")
    print("ACCESS DENIED")
    sys.exit(1)

# ============================================================
# LOAD FACE DETECTOR
# ============================================================
if os.path.exists(cascade_path):
    cascade = cv2.CascadeClassifier(cascade_path)
else:
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

if cascade.empty():
    print("Unable to load Haar face detector.")
    sys.exit(1)

# ============================================================
# LOAD EXISTING MULTI-USER LBPH MODEL
# ============================================================
try:
    recognizer = cv2.face.LBPHFaceRecognizer_create(
        radius=1,
        neighbors=8,
        grid_x=8,
        grid_y=8
    )
    recognizer.read(trainer_path)
except Exception as e:
    print("Unable to load LBPH face model.")
    print(e)
    sys.exit(1)

# ============================================================
# CALIBRATE FROM THE TARGET USER'S REGISTERED FACE SAMPLES
# This prevents us from blindly using a large global threshold.
# ============================================================
target_dir = os.path.join(face_root, email)
target_images = []

if os.path.isdir(target_dir):
    for pattern in ("*.jpg", "*.jpeg", "*.png", "*.bmp"):
        target_images.extend(glob.glob(os.path.join(target_dir, pattern)))

self_scores = []

for image_path in target_images:
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    if img is None:
        continue

    try:
        img = cv2.resize(img, (200, 200))
        predicted_label, score = recognizer.predict(img)

        predicted_email = labels.get(predicted_label, "")

        if predicted_email == email:
            self_scores.append(float(score))
    except Exception:
        continue

# Conservative threshold.
# The old project used 115, which was too permissive.
if self_scores:
    mean_score = statistics.mean(self_scores)
    std_score = statistics.pstdev(self_scores) if len(self_scores) > 1 else 0.0

    # Keep the threshold in a safer range.
    calibrated_threshold = mean_score + (2.5 * std_score) + 10.0
    ACCEPTANCE_THRESHOLD = max(92.0, min(calibrated_threshold, 108.0))
else:
    ACCEPTANCE_THRESHOLD = 100.0

# ============================================================
# OPEN WEBCAM FIRST
# ============================================================
print("Opening camera...")

cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cam.isOpened():
    cam.release()
    cam = cv2.VideoCapture(0)

if not cam.isOpened():
    print("Unable to open camera.")
    print("ACCESS DENIED")
    sys.exit(1)

cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cam.set(cv2.CAP_PROP_FPS, 30)

print("Camera opened successfully.")
print("Target:", email)
print(f"Acceptance threshold: {ACCEPTANCE_THRESHOLD:.1f}")
print("Look directly at the camera.")

# ============================================================
# AUTHENTICATION
# ============================================================
TIMEOUT = 15
REQUIRED_MATCHES = 5

start_time = time.time()
consecutive_matches = 0
authenticated = False
best_confidence = 999.0
best_match = "Unknown"

try:
    while time.time() - start_time < TIMEOUT:

        ret, frame = cam.read()

        if not ret:
            print("Camera frame could not be read.")
            break

        frame = cv2.flip(frame, 1)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Improve detection in dim/uneven lighting, and allow a face that
        # appears smaller in the webcam frame to be detected.
        gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)

        faces = cascade.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=4,
            minSize=(45, 45),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        # Fallback detector settings for difficult lighting/face angles.
        if len(faces) == 0:
            faces = cascade.detectMultiScale(
                cv2.equalizeHist(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)),
                scaleFactor=1.08,
                minNeighbors=3,
                minSize=(40, 40),
                flags=cv2.CASCADE_SCALE_IMAGE
            )

        # ----------------------------------------------------
        # NO FACE
        # ----------------------------------------------------
        if len(faces) == 0:
            consecutive_matches = 0

            cv2.putText(
                frame,
                "NO FACE DETECTED",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (0, 0, 255),
                2
            )

        # ----------------------------------------------------
        # MULTIPLE FACES
        # ----------------------------------------------------
        elif len(faces) > 1:
            consecutive_matches = 0

            cv2.putText(
                frame,
                "MULTIPLE FACES - ACCESS DENIED",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.62,
                (0, 0, 255),
                2
            )

            for (x, y, w, h) in faces:
                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    (0, 0, 255),
                    2
                )

        # ----------------------------------------------------
        # ONE FACE
        # ----------------------------------------------------
        else:
            x, y, w, h = faces[0]

            face = gray[y:y+h, x:x+w]
            face = cv2.resize(face, (200, 200))

            try:
                predicted_label, confidence = recognizer.predict(face)
                confidence = float(confidence)
            except Exception:
                predicted_label = -1
                confidence = 999.0

            detected_email = labels.get(
                predicted_label,
                "unknown"
            ).lower()

            if confidence < best_confidence:
                best_confidence = confidence
                best_match = detected_email

            # IMPORTANT:
            # Both identity and confidence must pass.
            identity_match = detected_email == email
            confidence_ok = confidence <= ACCEPTANCE_THRESHOLD

            verified_frame = identity_match and confidence_ok

            if verified_frame:
                consecutive_matches += 1
                box_color = (0, 255, 0)
            else:
                consecutive_matches = 0
                box_color = (0, 0, 255)

            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                box_color,
                3
            )

            cv2.putText(
                frame,
                f"Match: {detected_email}",
                (x, y + h + 23),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.52,
                box_color,
                2
            )

            cv2.putText(
                frame,
                f"Confidence: {confidence:.1f}",
                (x, y + h + 47),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.52,
                box_color,
                2
            )

            if verified_frame:
                cv2.putText(
                    frame,
                    f"VERIFYING {consecutive_matches}/{REQUIRED_MATCHES}",
                    (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.70,
                    (0, 255, 255),
                    2
                )
            else:
                cv2.putText(
                    frame,
                    "FACE NOT VERIFIED",
                    (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.70,
                    (0, 0, 255),
                    2
                )

            # ------------------------------------------------
            # SUCCESS
            # ------------------------------------------------
            if consecutive_matches >= REQUIRED_MATCHES:

                authenticated = True

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    (0, 255, 0),
                    4
                )

                cv2.putText(
                    frame,
                    "ACCESS GRANTED",
                    (20, 82),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 255, 0),
                    3
                )

                cv2.putText(
                    frame,
                    "IDENTITY VERIFIED",
                    (20, 117),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (0, 255, 0),
                    2
                )

                cv2.imshow(
                    "AI Face Authentication",
                    frame
                )

                cv2.waitKey(900)
                break

        cv2.imshow(
            "AI Face Authentication",
            frame
        )

        key = cv2.waitKey(1) & 0xFF

        if key == 27:
            print("Authentication cancelled.")
            break

finally:
    cam.release()
    cv2.destroyAllWindows()
    cv2.waitKey(1)

# ============================================================
# FINAL RESULT
# ============================================================
if authenticated:

    log_event(
        email,
        "FACE_VERIFICATION_SUCCESS"
    )

    print("AUTHENTICATED")
    print("LOGIN SUCCESSFUL")
    print(f"Best confidence: {best_confidence:.2f}")

    sys.exit(0)

log_event(
    email,
    "FACE_VERIFICATION_FAILED"
)

print("ACCESS DENIED")
print("Best detected identity:", best_match)
print(f"Best confidence: {best_confidence:.2f}")

sys.exit(1)
