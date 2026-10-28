
import os
import cv2
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODEL = ROOT / "models" / "trainer.yml"
LABELS = ROOT / "models" / "labels.txt"
FACE_ROOT = ROOT / "storage" / "face_data"

email = input("Enter your registered email: ").strip().lower()

labels = {}
with open(LABELS, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.strip().split(",", 1)
        if len(parts) == 2:
            labels[int(parts[0])] = parts[1].strip().lower()

recognizer = cv2.face.LBPHFaceRecognizer_create(
    radius=1, neighbors=8, grid_x=8, grid_y=8
)
recognizer.read(str(MODEL))

cascade_path = ROOT / "models" / "haarcascade_frontalface_default.xml"
cascade = cv2.CascadeClassifier(str(cascade_path))

if cascade.empty():
    raise RuntimeError("Could not load Haar Cascade XML file.")

for folder_name in os.listdir(FACE_ROOT):
    folder = FACE_ROOT / folder_name
    if not folder.is_dir():
        continue

    scores = []
    predicted_emails = []

    for name in os.listdir(folder):
        if Path(name).suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp"}:
            continue

        image = cv2.imread(str(folder / name), cv2.IMREAD_GRAYSCALE)
        if image is None:
            continue

        # Registration stores already-cropped face images.
        faces = cascade.detectMultiScale(
            image, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
        )

        if len(faces) > 0:
            x, y, w, h = max(faces, key=lambda r: r[2] * r[3])
            image = image[y:y+h, x:x+w]

        image = cv2.resize(image, (200, 200))
        label, distance = recognizer.predict(image)

        scores.append(float(distance))
        predicted_emails.append(labels.get(label, "unknown"))

    if scores:
        correct = sum(p == folder_name.lower() for p in predicted_emails)
        print(f"\nFolder: {folder_name}")
        print(f"Images tested: {len(scores)}")
        print(f"Correct identity predictions: {correct}/{len(scores)}")
        print(f"Distance min: {np.min(scores):.2f}")
        print(f"Distance median: {np.median(scores):.2f}")
        print(f"Distance 95th percentile: {np.percentile(scores, 95):.2f}")
        print(f"Distance max: {np.max(scores):.2f}")
