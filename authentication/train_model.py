import os
import cv2
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "storage", "face_data")
MODEL_DIR = os.path.join(BASE_DIR, "models")
TRAINER_PATH = os.path.join(MODEL_DIR, "trainer.yml")
LABELS_PATH = os.path.join(MODEL_DIR, "labels.txt")

os.makedirs(MODEL_DIR, exist_ok=True)

cascade_path = os.path.join(
    MODEL_DIR, "haarcascade_frontalface_default.xml"
)
if os.path.exists(cascade_path):
    cascade = cv2.CascadeClassifier(cascade_path)
else:
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

if cascade.empty():
    raise SystemExit("ERROR: Haar face detector could not be loaded.")

if not hasattr(cv2, "face"):
    raise SystemExit(
        "ERROR: cv2.face is unavailable. Install opencv-contrib-python."
    )

recognizer = cv2.face.LBPHFaceRecognizer_create()

faces = []
face_labels = []
label_map = {}
next_label = 0

if not os.path.isdir(DATA_DIR):
    raise SystemExit(
        f"ERROR: Face data folder not found: {DATA_DIR}"
    )

for email in sorted(os.listdir(DATA_DIR)):
    folder = os.path.join(DATA_DIR, email)
    if not os.path.isdir(folder):
        continue

    image_files = []
    for name in os.listdir(folder):
        if name.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
            image_files.append(os.path.join(folder, name))

    if not image_files:
        continue

    current_label = next_label
    next_label += 1
    label_map[current_label] = email

    added_for_user = 0

    for image_path in sorted(image_files):
        image = cv2.imread(image_path)
        if image is None:
            continue

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        detected = cascade.detectMultiScale(
            gray,
            scaleFactor=1.10,
            minNeighbors=5,
            minSize=(60, 60),
        )

        if len(detected) > 0:
            x, y, w, h = max(
                detected,
                key=lambda box: box[2] * box[3]
            )
            face = gray[y:y + h, x:x + w]
        else:
            # Registration may already have saved a cropped face.
            face = gray

        try:
            face = cv2.resize(face, (200, 200))
        except Exception:
            continue

        faces.append(face)
        face_labels.append(current_label)
        added_for_user += 1

    if added_for_user:
        print(f"Added {added_for_user} face samples for {email}")
    else:
        del label_map[current_label]

if not faces:
    raise SystemExit(
        "ERROR: No usable face images were found in storage/face_data."
    )

recognizer.train(
    faces,
    np.asarray(face_labels, dtype=np.int32)
)
recognizer.write(TRAINER_PATH)

with open(LABELS_PATH, "w", encoding="utf-8") as file:
    for label, email in sorted(label_map.items()):
        file.write(f"{label},{email}\n")

print()
print("========================================")
print("FACE MODEL TRAINING COMPLETE")
print("========================================")
print(f"Samples: {len(faces)}")
print(f"Users: {len(label_map)}")
print(f"Model: {TRAINER_PATH}")
print(f"Labels: {LABELS_PATH}")
for label, email in sorted(label_map.items()):
    print(f"{label} -> {email}")
