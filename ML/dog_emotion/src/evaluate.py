from pathlib import Path
import csv

import numpy as np
import tensorflow as tf
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
)

ROOT = Path(__file__).resolve().parents[1]

TEST_CSV = ROOT / "data" / "splits" / "test.csv"

MODEL_PATH = (
    ROOT
    / "models"
    / "dog_emotion_mobilenetv3_best.keras"
)

RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_SIZE = (224, 224)

CLASS_NAMES = [
    "alert",
    "angry",
    "frown",
    "happy",
    "relax",
]


# ============================================================
# LOAD TEST CSV
# ============================================================

paths = []
labels = []

with open(TEST_CSV, "r", encoding="utf-8") as f:

    reader = csv.DictReader(f)

    for row in reader:
        paths.append(row["path"])
        labels.append(
            CLASS_NAMES.index(row["label"])
        )

print("=" * 70)
print("DOG EMOTION MODEL EVALUATION")
print("=" * 70)

print(f"Test images: {len(paths)}")
print(f"Model: {MODEL_PATH}")


# ============================================================
# LOAD IMAGES
# ============================================================

def load_image(path):

    image = tf.io.read_file(path)

    image = tf.image.decode_jpeg(
        image,
        channels=3
    )

    image = tf.image.resize(
        image,
        IMAGE_SIZE
    )

    image = tf.cast(
        image,
        tf.float32
    )

    return image


images = []

for i, path in enumerate(paths):

    images.append(
        load_image(path)
    )

    if (i + 1) % 200 == 0:
        print(
            f"Loaded {i + 1}/{len(paths)} images"
        )


X_test = tf.stack(images)

y_test = np.array(labels)


# ============================================================
# LOAD BEST MODEL
# ============================================================

print("\nLoading best model...")

model = tf.keras.models.load_model(
    MODEL_PATH
)


# ============================================================
# PREDICTIONS
# ============================================================

print("\nRunning predictions...")

probabilities = model.predict(
    X_test,
    batch_size=32,
    verbose=1
)

y_pred = np.argmax(
    probabilities,
    axis=1
)


# ============================================================
# ACCURACY
# ============================================================

accuracy = accuracy_score(
    y_test,
    y_pred
)

print("\n")
print("=" * 70)
print("TEST RESULTS")
print("=" * 70)

print(
    f"\nTest Accuracy: {accuracy:.4f}"
)

print(
    f"Test Accuracy: {accuracy * 100:.2f}%"
)


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print("\nClassification Report:\n")

report = classification_report(
    y_test,
    y_pred,
    target_names=CLASS_NAMES,
    digits=4
)

print(report)


# ============================================================
# CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(
    y_test,
    y_pred
)

print("\nConfusion Matrix:")
print()

print(
    "             "
    + " ".join(
        f"{name:>8}"
        for name in CLASS_NAMES
    )
)

for i, row in enumerate(cm):

    print(
        f"{CLASS_NAMES[i]:>10} "
        + " ".join(
            f"{value:8d}"
            for value in row
        )
    )


# ============================================================
# SAVE RESULTS
# ============================================================

with open(
    RESULTS_DIR / "classification_report.txt",
    "w",
    encoding="utf-8"
) as f:

    f.write(
        "DOG EMOTION MODEL TEST RESULTS\n"
    )

    f.write(
        "==============================\n\n"
    )

    f.write(
        f"Test images: {len(paths)}\n"
    )

    f.write(
        f"Test accuracy: {accuracy:.4f}\n"
    )

    f.write(
        f"Test accuracy: {accuracy * 100:.2f}%\n\n"
    )

    f.write(
        "Classification Report\n"
    )

    f.write(
        "----------------------\n"
    )

    f.write(report)

    f.write(
        "\n\nConfusion Matrix\n"
    )

    f.write(
        "----------------\n"
    )

    f.write(
        str(cm)
    )


np.save(
    RESULTS_DIR / "confusion_matrix.npy",
    cm
)

print("\nResults saved to:")

print(
    RESULTS_DIR
    / "classification_report.txt"
)

print(
    RESULTS_DIR
    / "confusion_matrix.npy"
)