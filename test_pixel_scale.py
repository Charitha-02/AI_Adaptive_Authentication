
import cv2
import numpy as np
import onnxruntime as ort

session = ort.InferenceSession("models/minifasnet_v2.onnx")
input_name = session.get_inputs()[0].name

image = cv2.imread("liveness_debug_crop.jpg")
if image is None:
    raise SystemExit("Could not load liveness_debug_crop.jpg")

image = cv2.resize(image, (80, 80)).astype(np.float32)

for name, pixels in [
    ("NORMALIZED 0-1", image / 255.0),
    ("RAW 0-255", image),
]:
    tensor = np.transpose(pixels, (2, 0, 1))[None, ...]

    output = session.run(None, {input_name: tensor})[0][0]
    shifted = output - np.max(output)
    exp_scores = np.exp(shifted)
    probs = exp_scores / np.sum(exp_scores)

    print("\n", name)
    print("Raw output:", output)
    print("Probabilities:", probs)
    print("Predicted class:", int(np.argmax(probs)))
