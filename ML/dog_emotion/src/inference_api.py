from pathlib import Path
import io

import tempfile
import os
import cv2
import numpy as np
import tensorflow as tf
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "models" / "dog_emotion_mobilenetv3_best.keras"


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


# --------------------------------------------------
# LOAD MODEL ONCE
# --------------------------------------------------

print("=" * 60)
print("PAWAI DOG EMOTION INFERENCE API")
print("=" * 60)

print(f"Loading model from:")
print(MODEL_PATH)

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Model not found: {MODEL_PATH}"
    )

model = tf.keras.models.load_model(MODEL_PATH)

print("Model loaded successfully.")
print("=" * 60)


# --------------------------------------------------
# FASTAPI
# --------------------------------------------------

app = FastAPI(
    title="PawAI Dog Emotion ML API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": "dog_emotion_mobilenetv3_best",
        "classes": CLASS_NAMES,
    }


# --------------------------------------------------
# IMAGE PREDICTION
# --------------------------------------------------

@app.post("/predict")
async def predict(file: UploadFile = File(...)):

    # Check file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Please upload an image file.",
        )

    try:
        contents = await file.read()

        image = Image.open(
            io.BytesIO(contents)
        ).convert("RGB")

        # Resize
        image = image.resize(IMAGE_SIZE)

        # Convert to numpy
        image_array = np.array(image, dtype=np.float32)

        # MobileNetV3 preprocessing
        image_array = tf.keras.applications.mobilenet_v3.preprocess_input(
            image_array
        )

        # Add batch dimension
        image_array = np.expand_dims(
            image_array,
            axis=0,
        )

        # Prediction
        predictions = model.predict(
            image_array,
            verbose=0,
        )[0]

        predicted_index = int(
            np.argmax(predictions)
        )

        emotion = CLASS_NAMES[predicted_index]

        confidence = float(
            predictions[predicted_index]
        )

        probabilities = {
            CLASS_NAMES[i]: float(predictions[i])
            for i in range(len(CLASS_NAMES))
        }

        return {
            "emotion": emotion,
            "confidence": confidence,
            "probabilities": probabilities,
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}",
        )

@app.post("/predict-video")
async def predict_video(file: UploadFile = File(...)):

    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a video file.",
        )

    temp_path = None

    try:
        # Read uploaded video
        contents = await file.read()

        # Create temporary video file
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp4"
        ) as temp_file:

            temp_file.write(contents)
            temp_path = temp_file.name

        # Open video
        cap = cv2.VideoCapture(temp_path)

        if not cap.isOpened():
            raise HTTPException(
                status_code=400,
                detail="Could not open video.",
            )

        fps = cap.get(cv2.CAP_PROP_FPS)

        frame_count = int(
            cap.get(cv2.CAP_PROP_FRAME_COUNT)
        )

        duration = (
            frame_count / fps
            if fps > 0
            else 0
        )

        # Sample 2 frames per second
        sample_fps = 2

        sample_every = max(
            1,
            int(fps / sample_fps)
        )

        all_predictions = []

        frame_number = 0
        sampled_frames = 0

        while True:

            success, frame = cap.read()

            if not success:
                break

            if frame_number % sample_every == 0:

                # BGR → RGB
                frame = cv2.cvtColor(
                    frame,
                    cv2.COLOR_BGR2RGB
                )

                # Resize
                frame = cv2.resize(
                    frame,
                    IMAGE_SIZE
                )

                # Float conversion
                image_array = np.array(
                    frame,
                    dtype=np.float32
                )

                # MobileNetV3 preprocessing
                image_array = (
                    tf.keras.applications
                    .mobilenet_v3
                    .preprocess_input(
                        image_array
                    )
                )

                # Batch dimension
                image_array = np.expand_dims(
                    image_array,
                    axis=0
                )

                # Prediction
                predictions = model.predict(
                    image_array,
                    verbose=0
                )[0]

                all_predictions.append(
                    predictions
                )

                sampled_frames += 1

            frame_number += 1

        cap.release()

        if not all_predictions:

            raise HTTPException(
                status_code=400,
                detail="No frames could be processed.",
            )

        # Average probabilities
        all_predictions = np.array(
            all_predictions
        )

        average_probabilities = np.mean(
            all_predictions,
            axis=0
        )

        # Final prediction
        predicted_index = int(
            np.argmax(
                average_probabilities
            )
        )

        emotion = CLASS_NAMES[
            predicted_index
        ]

        confidence = float(
            average_probabilities[
                predicted_index
            ]
        )

        probabilities = {
            CLASS_NAMES[i]: float(
                average_probabilities[i]
            )
            for i in range(
                len(CLASS_NAMES)
            )
        }

        return {
            "emotion": emotion,
            "confidence": confidence,
            "probabilities": probabilities,
            "sampled_frames": sampled_frames,
            "video_fps": fps,
            "frame_count": frame_count,
            "duration": duration,
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Video prediction failed: {str(e)}",
        )

    finally:

        if temp_path and os.path.exists(temp_path):

            os.remove(temp_path)