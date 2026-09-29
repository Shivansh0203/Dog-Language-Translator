from pathlib import Path
import csv

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers


# ============================================================
# CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

SPLITS_DIR = ROOT / "data" / "splits"
MODEL_DIR = ROOT / "models"
RESULTS_DIR = ROOT / "results"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_CSV = SPLITS_DIR / "train.csv"
VAL_CSV = SPLITS_DIR / "val.csv"

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32

NUM_CLASSES = 5

CLASS_NAMES = [
    "alert",
    "angry",
    "frown",
    "happy",
    "relax",
]

EPOCHS_FROZEN = 10
EPOCHS_FINE_TUNE = 10

SEED = 42


# ============================================================
# LOAD CSV
# ============================================================

def load_csv(csv_path):

    paths = []
    labels = []

    with open(csv_path, "r", encoding="utf-8") as f:

        reader = csv.DictReader(f)

        for row in reader:

            paths.append(row["path"])
            labels.append(CLASS_NAMES.index(row["label"]))

    return paths, labels


print("=" * 70)
print("DOG EMOTION MODEL TRAINING")
print("=" * 70)

train_paths, train_labels = load_csv(TRAIN_CSV)
val_paths, val_labels = load_csv(VAL_CSV)

print(f"Training images:   {len(train_paths)}")
print(f"Validation images: {len(val_paths)}")


# ============================================================
# IMAGE LOADING
# ============================================================

def load_image(path, label):

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

    return image, label


# ============================================================
# DATA AUGMENTATION
# ============================================================

data_augmentation = keras.Sequential(
    [
        layers.RandomFlip(
            "horizontal"
        ),

        layers.RandomRotation(
            0.08
        ),

        layers.RandomZoom(
            0.10
        ),

        layers.RandomTranslation(
            height_factor=0.05,
            width_factor=0.05
        ),

        layers.RandomContrast(
            0.10
        ),
    ],
    name="data_augmentation",
)


# ============================================================
# CREATE DATASETS
# ============================================================

train_ds = tf.data.Dataset.from_tensor_slices(
    (
        train_paths,
        train_labels
    )
)

val_ds = tf.data.Dataset.from_tensor_slices(
    (
        val_paths,
        val_labels
    )
)

train_ds = train_ds.map(
    load_image,
    num_parallel_calls=tf.data.AUTOTUNE
)

val_ds = val_ds.map(
    load_image,
    num_parallel_calls=tf.data.AUTOTUNE
)


def augment(image, label):

    image = data_augmentation(
        image,
        training=True
    )

    return image, label


train_ds = train_ds.map(
    augment,
    num_parallel_calls=tf.data.AUTOTUNE
)


train_ds = train_ds.shuffle(
    1000,
    seed=SEED
)


train_ds = train_ds.batch(
    BATCH_SIZE
)

val_ds = val_ds.batch(
    BATCH_SIZE
)


train_ds = train_ds.prefetch(
    tf.data.AUTOTUNE
)

val_ds = val_ds.prefetch(
    tf.data.AUTOTUNE
)


# ============================================================
# MODEL
# ============================================================

print("\nLoading MobileNetV3-Small...")

base_model = tf.keras.applications.MobileNetV3Small(
    input_shape=(
        IMAGE_SIZE[0],
        IMAGE_SIZE[1],
        3
    ),
    include_top=False,
    weights="imagenet",
    pooling="avg"
)


# Freeze pretrained layers initially

base_model.trainable = False


inputs = keras.Input(
    shape=(
        IMAGE_SIZE[0],
        IMAGE_SIZE[1],
        3
    )
)


x = inputs


# MobileNetV3 expects inputs in the 0-255 range
# when include_preprocessing=True (default).

x = base_model(
    x,
    training=False
)


x = layers.Dropout(
    0.30
)(x)


outputs = layers.Dense(
    NUM_CLASSES,
    activation="softmax"
)(x)


model = keras.Model(
    inputs,
    outputs
)


model.summary()


# ============================================================
# COMPILE — STAGE 1
# ============================================================

model.compile(
    optimizer=keras.optimizers.Adam(
        learning_rate=1e-3
    ),

    loss=keras.losses.SparseCategoricalCrossentropy(),

    metrics=[
        "accuracy"
    ]
)


# ============================================================
# CALLBACKS
# ============================================================

best_model_path = (
    MODEL_DIR /
    "dog_emotion_mobilenetv3_best.keras"
)


callbacks = [

    keras.callbacks.ModelCheckpoint(
        filepath=str(best_model_path),
        monitor="val_accuracy",
        save_best_only=True,
        mode="max",
        verbose=1
    ),

    keras.callbacks.EarlyStopping(
        monitor="val_accuracy",
        patience=3,
        mode="max",
        restore_best_weights=True,
        verbose=1
    ),

    keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.2,
        patience=2,
        min_lr=1e-6,
        verbose=1
    ),
]


# ============================================================
# STAGE 1 — TRAIN CLASSIFIER
# ============================================================

print("\n")
print("=" * 70)
print("STAGE 1 — TRAINING CLASSIFICATION HEAD")
print("=" * 70)

history1 = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS_FROZEN,
    callbacks=callbacks
)


# ============================================================
# STAGE 2 — FINE TUNING
# ============================================================

print("\n")
print("=" * 70)
print("STAGE 2 — FINE TUNING")
print("=" * 70)


base_model.trainable = True


# Freeze most of MobileNetV3.
# Only fine-tune the final layers.

fine_tune_from = len(base_model.layers) - 30


for layer in base_model.layers[:fine_tune_from]:

    layer.trainable = False


# Keep BatchNorm layers frozen.

for layer in base_model.layers:

    if isinstance(
        layer,
        layers.BatchNormalization
    ):

        layer.trainable = False


model.compile(

    optimizer=keras.optimizers.Adam(
        learning_rate=1e-5
    ),

    loss=keras.losses.SparseCategoricalCrossentropy(),

    metrics=[
        "accuracy"
    ]
)


history2 = model.fit(

    train_ds,

    validation_data=val_ds,

    epochs=EPOCHS_FINE_TUNE,

    callbacks=callbacks
)


# ============================================================
# SAVE FINAL MODEL
# ============================================================

final_model_path = (
    MODEL_DIR /
    "dog_emotion_mobilenetv3_final.keras"
)


model.save(
    final_model_path
)


print("\n")
print("=" * 70)
print("TRAINING COMPLETE")
print("=" * 70)

print(
    f"Best model:  {best_model_path}"
)

print(
    f"Final model: {final_model_path}"
)