
import os
import cv2
import numpy as np
import onnxruntime as ort

MODEL_PATH = os.path.join("models", "minifasnet_v2.onnx")

session = ort.InferenceSession(
    MODEL_PATH,
    providers=["CPUExecutionProvider"]
)
input_name = session.get_inputs()[0].name

camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not camera.isOpened():
    camera = cv2.VideoCapture(0)

if not camera.isOpened():
    raise RuntimeError("Could not open webcam")

try:
    print("Look at the camera. Press Q to finish.")
    while True:
        ok, frame = camera.read()
        if not ok:
            break

        h, w = frame.shape[:2]
        size = min(h, w)
        x = (w - size) // 2
        y = (h - size) // 2
        crop = cv2.resize(frame[y:y+size, x:x+size], (80, 80))

        print("\n--- Same frame, four preprocessing variants ---")
        for color_name, image in [
            ("BGR", crop),
            ("RGB", cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)),
        ]:
            for scale_name, pixels in [
                ("0-255", image.astype(np.float32)),
                ("0-1", image.astype(np.float32) / 255.0),
            ]:
                tensor = np.transpose(pixels, (2, 0, 1))[None, ...]
                raw = session.run(None, {input_name: tensor})[0].reshape(-1)
                exp = np.exp(raw - np.max(raw))
                probs = exp / exp.sum()
                print(
                    f"{color_name}, {scale_name}: "
                    f"probabilities={np.round(probs, 4)}, "
                    f"class={int(np.argmax(probs))}"
                )

        cv2.imshow("Preprocessing diagnostic - Q to quit", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
finally:
    camera.release()
    cv2.destroyAllWindows()
