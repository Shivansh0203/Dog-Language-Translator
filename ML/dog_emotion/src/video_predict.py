import sys
from pathlib import Path

import cv2
import numpy as np
import tensorflow as tf


# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "dog_emotion_mobilenetv3_best.keras"
)


# --------------------------------------------------
# CONFIG
# --------------------------------------------------

CLASS_NAMES = [
    "alert",
    "angry",
    "frown",
    "happy",
    "relax",
]

IMAGE_SIZE = (224, 224)

# Number of frames sampled per second
SAMPLE_FPS = 2


# --------------------------------------------------
# LOAD MODEL
# --------------------------------------------------

print("=" * 60)
print("PAWAI DOG EMOTION VIDEO PREDICTION")
print("=" * 60)

print(f"Loading model:")
print(MODEL_PATH)

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Model not found: {MODEL_PATH}"
    )

model = tf.keras.models.load_model(MODEL_PATH)

print("Model loaded successfully.")
print("=" * 60)


# --------------------------------------------------
# FRAME PREDICTION
# --------------------------------------------------

def predict_frame(frame):

    # OpenCV uses BGR.
    # Convert to RGB for the model.
    frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    # Resize to model input size
    frame = cv2.resize(
        frame,
        IMAGE_SIZE
    )

    # Convert to float
    image_array = np.array(
        frame,
        dtype=np.float32
    )

    # MobileNetV3 preprocessing
    image_array = (
        tf.keras.applications.mobilenet_v3
        .preprocess_input(image_array)
    )

    # Add batch dimension
    image_array = np.expand_dims(
        image_array,
        axis=0
    )

    # Prediction
    predictions = model.predict(
        image_array,
        verbose=0
    )[0]

    return predictions


# --------------------------------------------------
# VIDEO PREDICTION
# --------------------------------------------------

def predict_video(video_path):

    video_path = Path(video_path)

    if not video_path.exists():
        raise FileNotFoundError(
            f"Video not found: {video_path}"
        )

    cap = cv2.VideoCapture(
        str(video_path)
    )

    if not cap.isOpened():
        raise RuntimeError(
            f"Could not open video: {video_path}"
        )

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    frame_count = int(
        cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    duration = (
        frame_count / fps
        if fps > 0
        else 0
    )

    print()
    print("VIDEO INFORMATION")
    print("-" * 40)
    print(f"Video: {video_path}")
    print(f"FPS: {fps:.2f}")
    print(f"Frames: {frame_count}")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Sampling: {SAMPLE_FPS} frames/sec")
    print()

    # Number of frames between samples
    sample_every = max(
        1,
        int(fps / SAMPLE_FPS)
    )

    all_predictions = []

    frame_number = 0
    sampled_frames = 0

    while True:

        success, frame = cap.read()

        if not success:
            break

        if frame_number % sample_every == 0:

            predictions = predict_frame(
                frame
            )

            all_predictions.append(
                predictions
            )

            sampled_frames += 1

            predicted_index = int(
                np.argmax(predictions)
            )

            emotion = CLASS_NAMES[
                predicted_index
            ]

            confidence = float(
                predictions[predicted_index]
            )

            print(
                f"Frame {frame_number:6d} "
                f"→ {emotion.upper():6s} "
                f"({confidence * 100:.2f}%)"
            )

        frame_number += 1

    cap.release()

    if not all_predictions:
        raise RuntimeError(
            "No frames were sampled."
        )

    # Convert list → numpy array
    all_predictions = np.array(
        all_predictions
    )

    # Average probability for every class
    average_probabilities = (
        np.mean(
            all_predictions,
            axis=0
        )
    )

    # Final prediction
    final_index = int(
        np.argmax(
            average_probabilities
        )
    )

    final_emotion = CLASS_NAMES[
        final_index
    ]

    final_confidence = float(
        average_probabilities[
            final_index
        ]
    )

    # --------------------------------------------------
    # RESULTS
    # --------------------------------------------------

    print()
    print("=" * 60)
    print("VIDEO RESULT")
    print("=" * 60)

    print(
        f"Sampled frames: {sampled_frames}"
    )

    print(
        f"Prediction: "
        f"{final_emotion.upper()}"
    )

    print(
        f"Confidence: "
        f"{final_confidence * 100:.2f}%"
    )

    print()
    print("Average class probabilities:")
    print("-" * 40)

    sorted_results = sorted(
        zip(
            CLASS_NAMES,
            average_probabilities
        ),
        key=lambda x: x[1],
        reverse=True
    )

    for emotion, probability in sorted_results:

        print(
            f"{emotion:>8}: "
            f"{probability * 100:6.2f}%"
        )

    print("=" * 60)

    return {
        "emotion": final_emotion,
        "confidence": final_confidence,
        "probabilities": {
            CLASS_NAMES[i]: float(
                average_probabilities[i]
            )
            for i in range(
                len(CLASS_NAMES)
            )
        },
        "sampled_frames": sampled_frames,
    }


# --------------------------------------------------
# COMMAND LINE
# --------------------------------------------------

if __name__ == "__main__":

    if len(sys.argv) != 2:

        print(
            "Usage:"
        )

        print(
            'python src\\video_predict.py '
            '"path\\to\\video.mp4"'
        )

        sys.exit(1)

    video_path = sys.argv[1]

    predict_video(
        video_path
    )