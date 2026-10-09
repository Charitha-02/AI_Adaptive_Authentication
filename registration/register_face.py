import cv2
import sqlite3
import os
import sys
import time

print("Python Executable:", sys.executable)
print("OpenCV Version:", cv2.__version__)

# ============================================================
# SETTINGS
# ============================================================

CASCADE_PATH = "models/haarcascade_frontalface_default.xml"
TOTAL_IMAGES = 30

# ============================================================
# LOAD FACE DETECTOR
# ============================================================

face_detector = cv2.CascadeClassifier(CASCADE_PATH)

if face_detector.empty():
    print("ERROR: Face detection model could not be loaded.")
    sys.exit(1)

# ============================================================
# GET EMAIL
# ============================================================

if len(sys.argv) > 1:
    email = sys.argv[1].strip()
else:
    email = input("Enter Registered Email: ").strip()

if email == "":
    print("ERROR: Email cannot be empty.")
    sys.exit(1)

# ============================================================
# CHECK USER
# ============================================================

conn = sqlite3.connect("database/users.db")
cursor = conn.cursor()

cursor.execute(
    "SELECT * FROM users WHERE email=?",
    (email,)
)

user = cursor.fetchone()

if not user:
    print("ERROR: User not found!")
    conn.close()
    sys.exit(1)

# ============================================================
# CREATE FACE DATA FOLDER
# ============================================================

folder = f"storage/face_data/{email}"
os.makedirs(folder, exist_ok=True)

# ============================================================
# OPEN CAMERA
# ============================================================

print("Opening camera...")

cam = cv2.VideoCapture(0)

# Check whether camera actually opened
if not cam.isOpened():
    print("ERROR: Camera could not be opened.")
    conn.close()
    sys.exit(1)

print("Camera opened successfully.")
print("Look at the camera.")
print("Press ESC to cancel.")

# ============================================================
# FACE CAPTURE
# ============================================================

count = 0

while True:

    ret, frame = cam.read()

    # Camera failed to provide frame
    if not ret:
        print("ERROR: Could not read frame from camera.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_detector.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5,
        minSize=(100, 100)
    )

    # --------------------------------------------------------
    # FACE DETECTED
    # --------------------------------------------------------

    if len(faces) > 0:

        for (x, y, w, h) in faces:

            face = gray[y:y + h, x:x + w]

            face = cv2.resize(face, (200, 200))

            filename = os.path.join(
                folder,
                f"{count}.jpg"
            )

            cv2.imwrite(filename, face)

            count += 1

            # Draw rectangle
            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                f"Captured: {count}/{TOTAL_IMAGES}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            break

    else:

        cv2.putText(
            frame,
            "No face detected",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

    # --------------------------------------------------------
    # SHOW CAMERA WINDOW
    # --------------------------------------------------------

    cv2.imshow(
        "Face Registration - Look at Camera",
        frame
    )

    key = cv2.waitKey(100) & 0xFF

    # ESC = cancel registration
    if key == 27:
        print("Face registration cancelled by user.")
        break

    # 30 images captured
    if count >= TOTAL_IMAGES:
        print("30 face images captured successfully.")
        break

# ============================================================
# CLOSE CAMERA
# ============================================================

cam.release()
cv2.destroyAllWindows()

# Small delay to make sure camera closes properly
time.sleep(0.5)

# ============================================================
# CHECK REGISTRATION RESULT
# ============================================================

if count >= TOTAL_IMAGES:

    cursor.execute("""
        UPDATE users
        SET face_registered=1
        WHERE email=?
    """, (email,))

    conn.commit()

    print("Face Registration Completed!")
    print(f"Images captured: {count}")
    print(f"Saved in: {folder}")

    conn.close()

    sys.exit(0)

else:

    print("Face Registration Failed.")
    print(f"Only {count}/{TOTAL_IMAGES} images were captured.")

    conn.close()

    sys.exit(1)