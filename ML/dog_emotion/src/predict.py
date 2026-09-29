from pathlib import Path
import sys

import numpy as np
import tensorflow as tf


# ============================================================
# CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = (
    ROOT
    / "models"
    / "dog_emotion_mobilenetv3_best.keras"
)

IMAGE_SIZE = (224, 224)

CLASS_NAMES = [
    "alert",
    "angry",
    "frown",
    "happy",
    "relax",
]


# ============================================================
# CHECK ARGUMENT
# ============================================================

if len(sys.argv) != 2:

    print(
        "\nUsage:"
    )

    print(
        'python src\\predict.py "path\\to\\dog.jpg"'
    )

    sys.exit(1)


image_path = Path(sys.argv[1])


if not image_path.exists():

    print(
        f"\nERROR: Image not found:\n{image_path}"
    )

    sys.exit(1)


# ============================================================
# LOAD MODEL
# ============================================================

print("Loading model...")

model = tf.keras.models.load_model(
    MODEL_PATH
)


# ============================================================
# LOAD IMAGE
# ============================================================

image = tf.io.read_file(
    str(image_path)
)

image = tf.image.decode_image(
    image,
    channels=3,
    expand_animations=False
)

image = tf.image.resize(
    image,
    IMAGE_SIZE
)

image = tf.cast(
    image,
    tf.float32
)

# Add batch dimension

image = tf.expand_dims(
    image,
    axis=0
)


# ============================================================
# PREDICTION
# ============================================================

probabilities = model.predict(
    image,
    verbose=0
)[0]


predicted_index = int(
    np.argmax(probabilities)
)

predicted_class = (
    CLASS_NAMES[predicted_index]
)

confidence = (
    probabilities[predicted_index]
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n")
print("=" * 60)
print("DOG EMOTION PREDICTION")
print("=" * 60)

print(
    f"\nImage: {image_path}"
)

print(
    f"\nPrediction: {predicted_class.upper()}"
)

print(
    f"Confidence: {confidence * 100:.2f}%"
)


print("\nClass probabilities:")
print("-" * 40)

results = []

for name, probability in zip(
    CLASS_NAMES,
    probabilities
):

    results.append(
        (name, probability)
    )


# Highest probability first

results.sort(
    key=lambda x: x[1],
    reverse=True
)


for name, probability in results:

    bar_length = int(
        probability * 30
    )

    bar = "█" * bar_length

    print(
        f"{name:>8}: "
        f"{probability * 100:6.2f}% "
        f"{bar}"
    )


print("=" * 60)