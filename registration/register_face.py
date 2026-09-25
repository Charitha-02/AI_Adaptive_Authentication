import cv2
import sqlite3
import os
import sys

print("Python Executable:", sys.executable)

import cv2

print("OpenCV Version:", cv2.__version__)

CASCADE_PATH = "models/haarcascade_frontalface_default.xml"

face_detector = cv2.CascadeClassifier(CASCADE_PATH)
import sys

if len(sys.argv) > 1:
    email = sys.argv[1]
else:
    email = input("Enter Registered Email: ").strip()

conn = sqlite3.connect("database/users.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM users WHERE email=?", (email,))
user = cursor.fetchone()

if not user:
    print("User not found!")
    exit()

folder = f"storage/face_data/{email}"
os.makedirs(folder, exist_ok=True)

cam = cv2.VideoCapture(0)

count = 0

print("Look at the camera...")

while True:

    ret, frame = cam.read()

    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_detector.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5
    )

    for (x, y, w, h) in faces:

        face = gray[y:y+h, x:x+w]

        face = cv2.resize(face, (200, 200))

        cv2.imwrite(f"{folder}/{count}.jpg", face)

        count += 1

        cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)

        cv2.putText(frame,
                    f"{count}/30",
                    (20,40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0,255,0),
                    2)

        break

    cv2.imshow("Face Registration", frame)

    if cv2.waitKey(100) == 27:
        break

    if count >= 30:
        break

cursor.execute("""
UPDATE users
SET face_registered=1
WHERE email=?
""", (email,))

conn.commit()
conn.close()

cam.release()
cv2.destroyAllWindows()

print("Face Registration Completed!")