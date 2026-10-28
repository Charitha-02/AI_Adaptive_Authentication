import os
import sys
import time
import sqlite3

from pathlib import Path

import cv2

# AI Adaptive Authentication - face login prototype.
# IMPORTANT: threshold 55 is temporary for a controlled project demo,
# based on the live scores seen during debugging. It is NOT security-
# validated and must not be used for real accounts or sensitive data.

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "users.db"
MODEL_PATH = BASE_DIR / "models" / "trainer.yml"
LABELS_PATH = BASE_DIR / "models" / "labels.txt"
CASCADE_PATH = BASE_DIR / "models" / "haarcascade_frontalface_default.xml"

CAMERA_INDEX = 0
LOGIN_TIMEOUT_SECONDS = 30
REQUIRED_CONSECUTIVE_MATCHES = 5

try:
    FACE_DISTANCE_THRESHOLD = float(
        os.environ.get("FACE_DISTANCE_THRESHOLD", "55.0")
    )
except ValueError:
    FACE_DISTANCE_THRESHOLD = 55.0

if not 0 < FACE_DISTANCE_THRESHOLD <= 150:
    print("FACE_DISTANCE_THRESHOLD must be between 0 and 150.")
    sys.exit(1)

os.chdir(BASE_DIR)
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from authentication.logger import log_event
except Exception as exc:
    print("WARNING: Could not import authentication.logger:", exc)

    def log_event(user_email, event_name):
        print(f"[LOG FALLBACK] {user_email}: {event_name}")


def deny(message):
    print(message)
    print("ACCESS DENIED")
    sys.exit(1)


def read_labels(path):
    labels = {}
    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            parts = line.split(",", 1)
            if len(parts) != 2:
                print("WARNING: Ignoring malformed labels.txt line:", line)
                continue
            try:
                labels[int(parts[0])] = parts[1].strip().lower()
            except ValueError:
                print("WARNING: Ignoring invalid label:", line)
    return labels


def preprocess_face_crop(face_gray, detector):
    """
    Use the same crop-or-whole-image approach as training:
    if a face is detected inside the crop, use the largest inner face;
    otherwise use the entire detected crop. Resize to 200x200.
    """
    if face_gray is None or face_gray.size == 0:
        return None

    inner_faces = detector.detectMultiScale(
        face_gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60),
    )
    if len(inner_faces) > 0:
        x, y, w, h = max(
            inner_faces, key=lambda rect: rect[2] * rect[3]
        )
        face_gray = face_gray[y:y + h, x:x + w]

    if face_gray is None or face_gray.size == 0:
        return None

    return cv2.resize(face_gray, (200, 200), interpolation=cv2.INTER_AREA)



def open_camera():
    backends = []

    if os.name == "nt":
        backends = [
            cv2.CAP_DSHOW,
            cv2.CAP_MSMF,
            cv2.CAP_ANY,
        ]
    else:
        backends = [cv2.CAP_ANY]

    for backend in backends:
        camera = cv2.VideoCapture(CAMERA_INDEX, backend)

        if not camera.isOpened():
            camera.release()
            continue

        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Allow the camera time to initialize and discard startup frames.
        valid_frame = False

        for _ in range(15):
            ok, frame = camera.read()

            if ok and frame is not None and frame.size > 0:
                valid_frame = True
                break

            time.sleep(0.1)

        if valid_frame:
            print(f"Webcam opened successfully with backend {backend}")
            return camera

        print(f"Backend {backend} opened, but frames were invalid.")
        camera.release()

    return None


def main():
    email = (
        sys.argv[1].strip().lower()
        if len(sys.argv) > 1
        else input("Enter your registered email: ").strip().lower()
    )
    if not email:
        deny("Email cannot be empty.")

    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT email FROM users WHERE LOWER(email) = ?",
                (email,),
            )
            account = cursor.fetchone()
    except Exception as exc:
        deny(f"Database error: {exc}")

    if not account:
        deny("User not found in the database.")
    email = str(account[0]).strip().lower()

    for file_path, description in (
        (MODEL_PATH, "Trained face model"),
        (LABELS_PATH, "Face labels file"),
        (CASCADE_PATH, "Haar Cascade XML"),
    ):
        if not file_path.is_file():
            deny(
                f"{description} not found: {file_path}\n"
                "Check the file path. If the model or labels are missing, "
                "run python authentication/train_model.py."
            )

    try:
        labels = read_labels(LABELS_PATH)
    except Exception as exc:
        deny(f"Could not read labels.txt: {exc}")

    if email not in labels.values():
        deny(
            "This email is not present in the trained face model. "
            "Register the face and run authentication/train_model.py."
        )

    detector = cv2.CascadeClassifier(str(CASCADE_PATH))
    if detector.empty():
        deny(f"Could not load face detector: {CASCADE_PATH}")

    if not hasattr(cv2, "face"):
        deny(
            "cv2.face is unavailable. Install opencv-contrib-python "
            "inside the active virtual environment."
        )

    try:
        # Must match the settings used by authentication/train_model.py.
        recognizer = cv2.face.LBPHFaceRecognizer_create(
            radius=1, neighbors=8, grid_x=8, grid_y=8
        )
        recognizer.read(str(MODEL_PATH))
    except Exception as exc:
        deny(f"Could not load the trained LBPH model: {exc}")

    print("\n--- FACE LOGIN ---")
    print("Account:", email)
    print("Model loaded:", MODEL_PATH)
    print("Temporary demo threshold:", FACE_DISTANCE_THRESHOLD)
    print("Keep only your face in view. Press ESC to cancel.")
    print("This threshold is for project demonstration only.")

    camera = open_camera()
    if camera is None:
        deny(
            "Could not open webcam. Check camera permissions and close "
            "other applications using the camera."
        )

    started_at = time.time()
    consecutive_matches = 0
    authenticated = False
    best_distance = float("inf")
    best_identity = "Unknown"
    window_name = "AI Face Authentication"

    try:
        
        while time.time() - started_at < LOGIN_TIMEOUT_SECONDS:
            ok, frame = camera.read()

            if not ok or frame is None:
                print("ERROR: Could not read a webcam frame.")
                break

            print(
                "Frame shape:", frame.shape,
                "Average brightness:", round(float(frame.mean()), 2)
            )


            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=4,
                minSize=(45, 45),
            )

            if len(faces) == 0:
                equalized = cv2.equalizeHist(gray)
                faces = detector.detectMultiScale(
                    equalized,
                    scaleFactor=1.08,
                    minNeighbors=3,
                    minSize=(40, 40),
                )

            if len(faces) == 0:
                consecutive_matches = 0
                cv2.putText(
                    frame, "NO FACE DETECTED", (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2
                )

            elif len(faces) > 1:
                consecutive_matches = 0
                for (x, y, w, h) in faces:
                    cv2.rectangle(
                        frame, (x, y), (x + w, y + h), (0, 0, 255), 2
                    )
                cv2.putText(
                    frame, "MULTIPLE FACES - TRY AGAIN", (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 255), 2
                )

            else:
                x, y, w, h = faces[0]
                detected_crop = gray[y:y + h, x:x + w]
                face_input = preprocess_face_crop(detected_crop, detector)

                try:
                    if face_input is None:
                        raise ValueError("Empty face crop")
                    predicted_label, distance = recognizer.predict(face_input)
                    distance = float(distance)
                    detected_identity = labels.get(
                        int(predicted_label), "unknown"
                    ).strip().lower()
                except Exception as exc:
                    print("Recognition error:", exc)
                    distance = float("inf")
                    detected_identity = "unknown"
                    consecutive_matches = 0

                if distance < best_distance:
                    best_distance = distance
                    best_identity = detected_identity

                identity_matches = detected_identity == email
                distance_ok = distance <= FACE_DISTANCE_THRESHOLD
                frame_verified = identity_matches and distance_ok

                if frame_verified:
                    consecutive_matches += 1
                    box_color = (0, 255, 0)
                else:
                    consecutive_matches = 0
                    box_color = (0, 0, 255)

                cv2.rectangle(
                    frame, (x, y), (x + w, y + h), box_color, 3
                )
                cv2.putText(
                    frame, f"Match: {detected_identity}",
                    (x, min(y + h + 23, frame.shape[0] - 40)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, box_color, 2
                )
                cv2.putText(
                    frame, f"Distance: {distance:.1f}",
                    (x, min(y + h + 47, frame.shape[0] - 15)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, box_color, 2
                )

                status = (
                    f"VERIFYING {consecutive_matches}/"
                    f"{REQUIRED_CONSECUTIVE_MATCHES}"
                    if frame_verified else "FACE NOT VERIFIED"
                )
                cv2.putText(
                    frame, status, (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.70,
                    (0, 255, 255) if frame_verified else (0, 0, 255), 2
                )

                if consecutive_matches >= REQUIRED_CONSECUTIVE_MATCHES:
                    authenticated = True
                    cv2.putText(
                        frame, "ACCESS GRANTED", (20, 82),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3
                    )
                    cv2.imshow(window_name, frame)
                    cv2.waitKey(900)
                    break

            cv2.imshow(window_name, frame)
            if cv2.waitKey(1) & 0xFF == 27:
                print("Authentication cancelled.")
                break

    finally:
        camera.release()
        cv2.destroyAllWindows()

    if authenticated:
        try:
            log_event(email, "FACE_VERIFICATION_SUCCESS")
        except Exception as exc:
            print("WARNING: Could not write success log:", exc)
        print("AUTHENTICATED")
        print("LOGIN SUCCESSFUL")
        print("Best detected identity:", best_identity)
        print(f"Best confidence/distance: {best_distance:.2f}")
        sys.exit(0)

    try:
        log_event(email, "FACE_VERIFICATION_FAILED")
    except Exception as exc:
        print("WARNING: Could not write failure log:", exc)

    print("ACCESS DENIED")
    print("Best detected identity:", best_identity)
    if best_distance != float("inf") and best_distance == best_distance:
        print(f"Best confidence/distance: {best_distance:.2f}")
    else:
        print("No valid face score was produced.")
    sys.exit(1)


if __name__ == "__main__":
    main()
