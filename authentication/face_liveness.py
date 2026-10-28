
import os
import time

import cv2
import numpy as np
import onnxruntime as ort


def check_liveness():
    """
    Face anti-spoofing using MiniFASNetV2 ONNX and YuNet.

    Returns:
        (True, score) when 8 consecutive frames pass liveness.
        (False, 0) when verification fails.

    Current class assumption:
        Class 1 = live face
        Class 0 and class 2 = attack classes

    The class mapping must be confirmed for the ONNX model in use.
    """

    project_root = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )

    model_path = os.path.join(
        project_root, "models", "minifasnet_v2.onnx"
    )

    yunet_path = os.path.join(
        project_root, "models",
        "face_detection_yunet_2023mar.onnx"
    )

    if not os.path.isfile(model_path):
        print("LIVENESS ERROR: MiniFASNet model not found:", model_path)
        return False, 0

    if not os.path.isfile(yunet_path):
        print("LIVENESS ERROR: YuNet model not found:", yunet_path)
        return False, 0

    # Load the anti-spoofing model.
    try:
        session = ort.InferenceSession(
            model_path,
            providers=["CPUExecutionProvider"]
        )
        input_name = session.get_inputs()[0].name
        print("MiniFASNet loaded successfully.", flush=True)
    except Exception as exc:
        print("LIVENESS ERROR: Could not load MiniFASNet:", exc)
        return False, 0

    # Open the webcam.
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not camera.isOpened():
        camera.release()
        camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        camera.release()
        print("LIVENESS ERROR: Webcam could not open.")
        return False, 0

    live_predictions = []
    start_time = time.time()
    timeout = 12
    required_frames = 8
    live_threshold = 0.80

    try:
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        ok, frame = camera.read()

        if not ok or frame is None:
            print("LIVENESS ERROR: Could not read webcam frame.")
            return False, 0

        height, width = frame.shape[:2]

        # Initialize YuNet with the actual camera-frame dimensions.
        try:
            detector = cv2.FaceDetectorYN.create(
                yunet_path,
                "",
                (width, height),
                0.6,
                0.3,
                5000
            )
        except Exception as exc:
            print("LIVENESS ERROR: Could not initialize YuNet:", exc)
            return False, 0

        while time.time() - start_time < timeout:
            ok, frame = camera.read()

            if not ok or frame is None:
                print("LIVENESS ERROR: Could not read camera frame.")
                break

            height, width = frame.shape[:2]
            detector.setInputSize((width, height))

            _, detected_faces = detector.detect(frame)
            face_count = 0 if detected_faces is None else len(detected_faces)
            message = f"Detected faces: {face_count}"
            print(message, flush=True)
            print(
    "Detected face count:",
    0 if detected_faces is None else len(detected_faces),
    flush=True
)

            faces = []

            if detected_faces is not None:
                for detected_face in detected_faces:
                    x, y, w, h = map(
                        int, detected_face[:4]
                    )
                    faces.append((x, y, w, h))

            message = "Face the camera"
            color = (0, 255, 255)

            if len(faces) == 1:
                x, y, w, h = faces[0]

                print(
                    "YuNet face box:", x, y, w, h,
                    flush=True
                )

                if w <= 0 or h <= 0:
                    live_predictions.clear()
                    continue

                # Expand the face box by up to 2.7x.
                center_x = x + w / 2
                center_y = y + h / 2

                scale = min(
                    (height - 1) / h,
                    (width - 1) / w,
                    2.7
                )

                new_w = w * scale
                new_h = h * scale

                left = int(center_x - new_w / 2)
                top = int(center_y - new_h / 2)
                right = int(center_x + new_w / 2)
                bottom = int(center_y + new_h / 2)

                if left < 0:
                    right -= left
                    left = 0

                if top < 0:
                    bottom -= top
                    top = 0

                if right > width - 1:
                    left -= right - width + 1
                    right = width - 1

                if bottom > height - 1:
                    top -= bottom - height + 1
                    bottom = height - 1

                left = max(0, left)
                top = max(0, top)
                right = min(width - 1, right)
                bottom = min(height - 1, bottom)

                crop = frame[
                    top:bottom + 1,
                    left:right + 1
                ]

                if crop.size == 0:
                    print(
                        "LIVENESS ERROR: Empty face crop.",
                        flush=True
                    )
                    live_predictions.clear()
                    continue

                print("Face crop size:", crop.shape, flush=True)

                # Save the latest crop for debugging.
                debug_path = os.path.join(
                    project_root, "liveness_debug_crop.jpg"
                )
                cv2.imwrite(debug_path, crop)

                # MiniFASNet input preprocessing
                
# MiniFASNet-V2 input preprocessing
# Keep BGR channel order and pixel values in the 0–255 range.
                resized = cv2.resize(crop, (80, 80))

                print("BGR pixel sample:", resized[40, 40].tolist(), flush=True)

                tensor = resized.astype(np.float32)
                tensor = np.transpose(tensor, (2, 0, 1))
                tensor = np.expand_dims(tensor, axis=0)

                print("Model input:", tensor.shape, tensor.dtype, flush=True)


                print("Model input:", tensor.shape, tensor.dtype, flush=True)

                output = session.run(None, {input_name: tensor})[0]
                print("DEBUG input min/max:", tensor.min(), tensor.max(), flush=True)
                print("DEBUG input mean:", tensor.mean(), flush=True)
                print("Raw model output shape:", output.shape, flush=True)
                print("Raw model output:", output, flush=True)

                output = np.asarray(output).reshape(-1)

                if output.size != 3 or not np.all(np.isfinite(output)):
                    print("LIVENESS ERROR: Unexpected model output.", flush=True)
                    live_predictions.clear()
                    continue

                shifted = output - np.max(output)
                exp_scores = np.exp(shifted)
                probs = exp_scores / np.sum(exp_scores)

                print(
                    "Class probabilities:",
                    [round(float(p), 5) for p in probs],
                    flush=True
                )

                predicted_class = int(np.argmax(probs))
                print("Predicted class:", predicted_class, flush=True)

                # Keep the existing class mapping unchanged until verified.
                live_prob = float(probs[1])
                class_0_prob = float(probs[0])
                class_2_prob = float(probs[2])
                predicted_class = int(np.argmax(probs))

                print(
                    f"Class 0 probability: {class_0_prob:.6f}",
                    flush=True
                )
                print(
                    f"Class 1 probability (assumed live): "
                    f"{live_prob:.6f}",
                    flush=True
                )
                print(
                    f"Class 2 probability: {class_2_prob:.6f}",
                    flush=True
                )
                print(
                    "Predicted class:", predicted_class,
                    flush=True
                )

                if live_prob >= live_threshold:
                    live_predictions.append(live_prob)
                    live_predictions = live_predictions[
                        -required_frames:
                    ]
                else:
                    live_predictions.clear()

                message = (
                    f"Live {live_prob:.2f} | "
                    f"C0 {class_0_prob:.2f} | "
                    f"C2 {class_2_prob:.2f}"
                )

                color = (
                    (0, 255, 0)
                    if live_prob >= live_threshold
                    else (0, 0, 255)
                )

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    color,
                    2
                )

            elif len(faces) == 0:
                live_predictions.clear()
                message = "No face detected"

            else:
            
                live_predictions.clear()
                message = f"Only one face allowed ({len(faces)} detected)"

            cv2.putText(
                frame,
                message,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2
            )

            cv2.putText(
                frame,
                f"Verified frames: "
                f"{len(live_predictions)}/{required_frames}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )

            cv2.imshow("Face Anti-Spoofing", frame)

            if len(live_predictions) >= required_frames:
                score = int(
                    np.mean(live_predictions) * 100
                )
                print(
                    f"LIVENESS PASSED: {score}%",
                    flush=True
                )
                cv2.waitKey(300)
                return True, score

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except Exception as exc:
        print("LIVENESS ERROR:", exc, flush=True)
        return False, 0

    finally:
        camera.release()
        cv2.destroyAllWindows()

    print(
        "LIVENESS FAILED: Could not verify a live face.",
        flush=True
    )
    return False, 0
