from pathlib import Path
import hashlib
import csv
import random
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]

DATASET = ROOT / "data" / "raw" / "train_images_5_class"
SPLITS_DIR = ROOT / "data" / "splits"

CLASSES = [
    "alert",
    "angry",
    "frown",
    "happy",
    "relax",
]

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

SEED = 42


def md5_hash(path):
    """Return MD5 hash of a file."""
    md5 = hashlib.md5()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            md5.update(chunk)

    return md5.hexdigest()


def collect_images():
    """Collect all images and their labels."""

    records = []

    for label in CLASSES:
        folder = DATASET / label

        if not folder.exists():
            raise FileNotFoundError(
                f"Missing class folder: {folder}"
            )

        for path in sorted(folder.glob("*.jpg")):
            records.append({
                "path": str(path.resolve()),
                "label": label,
                "hash": md5_hash(path),
            })

    return records


def group_by_hash(records):
    """Group files that have identical contents."""

    groups = defaultdict(list)

    for record in records:
        groups[record["hash"]].append(record)

    return groups


def split_class(records):
    """Split records from one class into train/val/test."""

    records = list(records)

    random.shuffle(records)

    n = len(records)

    train_end = int(n * TRAIN_RATIO)
    val_end = train_end + int(n * VAL_RATIO)

    train = records[:train_end]
    val = records[train_end:val_end]
    test = records[val_end:]

    return train, val, test


def write_csv(path, records):

    with open(path, "w", newline="", encoding="utf-8") as f:

        writer = csv.DictWriter(
            f,
            fieldnames=["path", "label"]
        )

        writer.writeheader()

        for record in records:
            writer.writerow({
                "path": record["path"],
                "label": record["label"],
            })


def main():

    random.seed(SEED)

    SPLITS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("PREPARING DOG EMOTION DATASET SPLITS")
    print("=" * 70)

    records = collect_images()

    print(f"\nImages found: {len(records)}")

    # ---------------------------------------------------------
    # Detect duplicate files
    # ---------------------------------------------------------

    groups = group_by_hash(records)

    duplicate_groups = {
        h: items
        for h, items in groups.items()
        if len(items) > 1
    }

    print(f"Unique file hashes: {len(groups)}")
    print(f"Duplicate hash groups: {len(duplicate_groups)}")

    # ---------------------------------------------------------
    # Remove conflicting-label duplicate groups
    # ---------------------------------------------------------

    conflicting_hashes = set()

    for file_hash, items in duplicate_groups.items():

        labels = {item["label"] for item in items}

        if len(labels) > 1:
            conflicting_hashes.add(file_hash)

    if conflicting_hashes:

        print(
            f"Conflicting duplicate groups: "
            f"{len(conflicting_hashes)}"
        )

    usable = []

    for record in records:

        if record["hash"] in conflicting_hashes:
            continue

        usable.append(record)

    # ---------------------------------------------------------
    # Keep only one copy of same-label duplicates
    # ---------------------------------------------------------

    seen_hashes = set()
    unique_records = []

    for record in usable:

        if record["hash"] in seen_hashes:
            continue

        seen_hashes.add(record["hash"])
        unique_records.append(record)

    removed = len(records) - len(unique_records)

    print(f"Images removed as duplicates/conflicts: {removed}")
    print(f"Usable unique images: {len(unique_records)}")

    # ---------------------------------------------------------
    # Stratified split
    # ---------------------------------------------------------

    by_class = defaultdict(list)

    for record in unique_records:
        by_class[record["label"]].append(record)

    train = []
    val = []
    test = []

    print("\nClass distribution:")

    for label in CLASSES:

        class_records = by_class[label]

        class_train, class_val, class_test = split_class(
            class_records
        )

        train.extend(class_train)
        val.extend(class_val)
        test.extend(class_test)

        print(
            f"{label:10s} "
            f"train={len(class_train):4d} "
            f"val={len(class_val):4d} "
            f"test={len(class_test):4d}"
        )

    # Shuffle each split

    random.shuffle(train)
    random.shuffle(val)
    random.shuffle(test)

    # ---------------------------------------------------------
    # Save manifests
    # ---------------------------------------------------------

    write_csv(
        SPLITS_DIR / "train.csv",
        train
    )

    write_csv(
        SPLITS_DIR / "val.csv",
        val
    )

    write_csv(
        SPLITS_DIR / "test.csv",
        test
    )

    print("\n" + "=" * 70)
    print("SPLIT COMPLETE")
    print("=" * 70)

    print(f"Training:   {len(train)}")
    print(f"Validation: {len(val)}")
    print(f"Testing:    {len(test)}")
    print(f"Total:      {len(train) + len(val) + len(test)}")

    print("\nCreated:")

    print(SPLITS_DIR / "train.csv")
    print(SPLITS_DIR / "val.csv")
    print(SPLITS_DIR / "test.csv")


if __name__ == "__main__":
    main()