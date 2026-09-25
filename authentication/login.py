import cv2
import sqlite3
import sys
import time
from logger import log_event


# -------------------------------------------------
# GET EMAIL
# -------------------------------------------------

if len(sys.argv) > 1:
    email = sys.argv[1].strip()
else:
    email = input("Enter your registered email: ").strip()


# -------------------------------------------------
# CHECK USER IN DATABASE
# -------------------------------------------------

conn = sqlite3.connect("database/users.db")
cursor = conn.cursor()

cursor.execute(
    "SELECT * FROM users WHERE email=?",
    (email,)
)

user = cursor.fetchone()

conn.close()

if not user:
    print("User not found!")
    sys.exit(1)


# -------------------------------------------------
# LOAD FACE DETECTION MODEL
# -------------------------------------------------

cascade = cv2.CascadeClassifier(
    "models/haarcascade_frontalface_default.xml"
)

if cascade.empty():
    print("Face detection model not found!")
    sys.exit(1)


# -------------------------------------------------
# LOAD TRAINED FACE RECOGNIZER
# -------------------------------------------------

recognizer = cv2.face.LBPHFaceRecognizer_create()

try:
    recognizer.read("models/trainer.yml")
except Exception:
    print("Face recognition model not found!")
    sys.exit(1)


# -------------------------------------------------
# LOAD FACE LABELS
# -------------------------------------------------

labels = {}

try:

    with open("models/labels.txt", "r") as file:

        for line in file:

            line = line.strip()

            if line:

                label, name = line.split(",", 1)

                labels[int(label)] = name

except Exception:

    print("Face labels file not found!")
    sys.exit(1)


# -------------------------------------------------
# OPEN CAMERA
# -------------------------------------------------

cam = cv2.VideoCapture(0)

if not cam.isOpened():

    print("Unable to open camera.")
    sys.exit(1)


print("Looking for your face...")
print("Please look at the camera.")


authenticated = False

start_time = time.time()

TIMEOUT = 10


# -------------------------------------------------
# FACE RECOGNITION LOOP
# -------------------------------------------------

while True:

    # Stop after 10 seconds
    if time.time() - start_time > TIMEOUT:

        print("Authentication Timeout")

        break


    ret, frame = cam.read()

    if not ret:

        print("Unable to read camera.")

        break


    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )


    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5
    )


    for (x, y, w, h) in faces:

        face = gray[y:y+h, x:x+w]

        face = cv2.resize(
            face,
            (200, 200)
        )


        label, confidence = recognizer.predict(face)


        if confidence < 70:

            detected_email = labels.get(label, "")


            if detected_email == email:

                authenticated = True


                cv2.rectangle(
                    frame,
                    (x, y),
                    (x+w, y+h),
                    (0, 255, 0),
                    2
                )


                cv2.putText(
                    frame,
                    "ACCESS GRANTED",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2
                )


                cv2.imshow(
                    "Login",
                    frame
                )


                cv2.waitKey(1000)

                break


    cv2.imshow(
        "Login",
        frame
    )


    if authenticated:

        break


    # Press ESC to cancel
    if cv2.waitKey(1) & 0xFF == 27:

        print("Authentication Cancelled")

        break


# -------------------------------------------------
# CLOSE CAMERA
# -------------------------------------------------

cam.release()

cv2.destroyAllWindows()

cv2.waitKey(1)


# -------------------------------------------------
# FINAL RESULT
# -------------------------------------------------

if authenticated:

    log_event(
        email,
        "SUCCESS"
    )

    print("Login Successful")

else:

    log_event(
        email,
        "FAILED"
    )

    print("Access Denied")

    sys.exit(1)