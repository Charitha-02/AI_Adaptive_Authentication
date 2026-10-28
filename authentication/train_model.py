import os
import cv2
import numpy as np

# Resolve all paths from the project root, regardless of how this script is launched.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "storage", "face_data")
MODEL_DIR = os.path.join(BASE_DIR, "models")
TRAINER_PATH = os.path.join(MODEL_DIR, "trainer.yml")
LABELS_PATH = os.path.join(MODEL_DIR, "labels.txt")
CASCADE_PATH = os.path.join(MODEL_DIR, "haarcascade_frontalface_default.xml")

os.makedirs(MODEL_DIR, exist_ok=True)

if os.path.exists(CASCADE_PATH):
    cascade = cv2.CascadeClassifier(CASCADE_PATH)
else:
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

if cascade.empty():
    raise SystemExit("ERROR: Haar face detector could not be loaded.")

if not hasattr(cv2, "face"):
    raise SystemExit(
        "ERROR: cv2.face is unavailable. Install opencv-contrib-python "
        "in the same Python environment used to run this project."
    )

# Keep these settings identical in login.py.
recognizer = cv2.face.LBPHFaceRecognizer_create(
    radius=1, neighbors=8, grid_x=8, grid_y=8
)

if not os.path.isdir(DATA_DIR):
    raise SystemExit(f"ERROR: Face data folder not found: {DATA_DIR}")

faces = []
face_labels = []
label_map = {}
next_label = 0
supported_extensions = (".jpg", ".jpeg", ".png", ".bmp")

# Case-insensitive email handling avoids separate identities caused by letter case.
user_folders = []
for folder_name in sorted(os.listdir(DATA_DIR), key=str.lower):
    folder_path = os.path.join(DATA_DIR, folder_name)
    if os.path.isdir(folder_path):
        user_folders.append((folder_name, folder_path))

seen_emails = set()

for folder_name, folder_path in user_folders:
    email = folder_name.strip().lower()
    if not email:
        continue
    if email in seen_emails:
        print(f"WARNING: Skipping duplicate case-insensitive folder for {email}")
        continue

    image_files = [
        os.path.join(folder_path, name)
        for name in sorted(os.listdir(folder_path))
        if name.lower().endswith(supported_extensions)
    ]
    if not image_files:
        print(f"Skipping {email}: no supported images found.")
        continue

    current_label = next_label
    samples_for_user = []

    for image_path in image_files:
        image = cv2.imread(image_path)
        if image is None:
            print(f"WARNING: Could not read image: {image_path}")
            continue

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        detected = cascade.detectMultiScale(
            gray, scaleFactor=1.10, minNeighbors=5, minSize=(60, 60)
        )

        if len(detected) > 0:
            x, y, w, h = max(detected, key=lambda box: box[2] * box[3])
            face = gray[y:y + h, x:x + w]
        else:
            # register_face.py saves already-cropped 200x200 face images.
            # In that case, train on the whole saved image.
            face = gray

        if face is None or face.size == 0:
            continue

        face = cv2.resize(face, (200, 200), interpolation=cv2.INTER_AREA)
        samples_for_user.append(face)

    if not samples_for_user:
        print(f"WARNING: No usable face images for {email}.")
        continue

    label_map[current_label] = email
    seen_emails.add(email)
    faces.extend(samples_for_user)
    face_labels.extend([current_label] * len(samples_for_user))
    next_label += 1
    print(f"Added {len(samples_for_user)} face samples for {email} (label {current_label}).")

if not faces or not label_map:
    raise SystemExit("ERROR: No usable face images found. Register a face first.")

labels_array = np.asarray(face_labels, dtype=np.int32)
recognizer.train(faces, labels_array)
recognizer.write(TRAINER_PATH)

with open(LABELS_PATH, "w", encoding="utf-8") as file:
    for label, email in sorted(label_map.items()):
        file.write(f"{label},{email}\n")

print("\n========================================")
print("FACE MODEL TRAINING COMPLETE")
print("========================================")
print(f"Samples: {len(faces)}")
print(f"Users: {len(label_map)}")
print(f"Model: {TRAINER_PATH}")
print(f"Labels: {LABELS_PATH}")
for label, email in sorted(label_map.items()):
    print(f"{label} -> {email}")
