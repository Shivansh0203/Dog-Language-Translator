from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

DATASET = ROOT / "data" / "raw" / "train_images_5_class"

CLASSES = [
    "alert",
    "angry",
    "frown",
    "happy",
    "relax",
]

total = 0
corrupted = []

print("=" * 60)
print("DOG EMOTION DATASET INSPECTION")
print("=" * 60)

for label in CLASSES:

    folder = DATASET / label

    if not folder.exists():
        print(f"ERROR: Missing folder: {folder}")
        continue

    images = list(folder.glob("*.jpg"))

    print(f"{label:10s}: {len(images)} images")

    total += len(images)

    for image in images:
        try:
            with Image.open(image) as img:
                img.verify()
        except Exception:
            corrupted.append(image)

print("=" * 60)
print(f"Total images: {total}")
print(f"Corrupted images: {len(corrupted)}")
print("=" * 60)

if corrupted:
    print("\nCorrupted files:")

    for image in corrupted:
        print(image)