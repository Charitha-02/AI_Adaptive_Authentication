
import os
import cv2
import numpy as np
import onnxruntime as ort

MODEL_PATH = os.path.join("models", "minifasnet_v2.onnx")

if not os.path.isfile(MODEL_PATH):
    print("ERROR: Model not found:", os.path.abspath(MODEL_PATH))
    raise SystemExit(1)

session = ort.InferenceSession(
    MODEL_PATH,
    providers=["CPUExecutionProvider"]
)

input_info = session.get_inputs()[0]
print("Model input:", input_info.name, input_info.shape, input_info.type)
print("Model outputs:", session.get_outputs()[0].shape)

camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not camera.isOpened():
    camera.release()
    camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Webcam could not open.")
    raise SystemExit(1)

print("Look directly at the camera. Press Q to quit.")

try:
    while True:
        ok, frame = camera.read()
        if not ok:
            print("ERROR: Could not read webcam frame.")
            break

        height, width = frame.shape[:2]
        size = min(height, width)
        x1 = (width - size) // 2
        y1 = (height - size) // 2
        crop = frame[y1:y1 + size, x1:x1 + size]

        resized = cv2.resize(crop, (80, 80))
        tensor = resized.astype(np.float32) / 255.0
        tensor = np.transpose(tensor, (2, 0, 1))[None, ...]

        output = session.run(
            None, {input_info.name: tensor}
        )[0][0]

        shifted = output - np.max(output)
        exp_scores = np.exp(shifted)
        probs = exp_scores / np.sum(exp_scores)

        print(
            "Raw:", np.round(output, 4),
            "| Probabilities:", np.round(probs, 4),
            "| Predicted class:", int(np.argmax(probs))
        )

        cv2.imshow("Model Test - Press Q to quit", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
finally:
    camera.release()
    cv2.destroyAllWindows()
