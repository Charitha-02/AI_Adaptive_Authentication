import cv2
import os
import numpy as np

dataset_path = "storage/face_data"

recognizer = cv2.face.LBPHFaceRecognizer_create()

faces = []
labels = []
label_map = {}

current_label = 0

for person in os.listdir(dataset_path):
    person_path = os.path.join(dataset_path, person)

    if not os.path.isdir(person_path):
        continue

    label_map[current_label] = person

    for image_name in os.listdir(person_path):
        image_path = os.path.join(person_path, image_name)

        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

        if img is None:
            continue

        faces.append(img)
        labels.append(current_label)

    current_label += 1

recognizer.train(faces, np.array(labels))

os.makedirs("models", exist_ok=True)

recognizer.save("models/trainer.yml")

with open("models/labels.txt", "w") as f:
    for label, email in label_map.items():
        f.write(f"{label},{email}\n")

print("Model Trained Successfully!")