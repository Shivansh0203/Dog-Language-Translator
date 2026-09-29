import csv
from pathlib import Path

BASE = Path(__file__).resolve().parent
METADATA = BASE / "metadata"

DOG_CLASSES = {
    "/m/05tny_": "bark",
    "/m/07r_k2n": "yip",
    "/m/07qf0zm": "howl",
    "/m/07rc7d9": "bow-wow",
    "/m/0ghcn6": "growling",
    "/t/dd00136": "whimper_dog",
}

FILES = [
    METADATA / "balanced_train_segments.csv",
    METADATA / "eval_segments.csv",
]

all_matches = []

for file in FILES:

    print()
    print("=" * 60)
    print(f"Reading: {file.name}")
    print("=" * 60)

    with open(file, "r", encoding="utf-8") as f:

        reader = csv.reader(f)

        rows = 0

        for row in reader:

            # Skip AudioSet comments/header lines
            if not row:
                continue

            if row[0].startswith("#"):
                continue

            rows += 1

            # AudioSet format:
            # youtube_id, start_seconds, end_seconds, positive_labels

            if len(row) < 4:
                continue

            youtube_id = row[0].strip()
            start = float(row[1])
            end = float(row[2])

            # Everything after column 3 belongs to labels
            labels = ",".join(row[3:])

            for mid, name in DOG_CLASSES.items():

                if mid in labels:

                    all_matches.append({
                        "split": file.stem,
                        "youtube_id": youtube_id,
                        "start": start,
                        "end": end,
                        "label": name,
                    })

    print(f"Rows processed: {rows}")


print()
print("=" * 60)
print("DOG AUDIOSET RESULTS")
print("=" * 60)

if not all_matches:

    print("No dog clips found.")

else:

    # Count classes
    counts = {}

    for item in all_matches:
        label = item["label"]
        counts[label] = counts.get(label, 0) + 1

    print()
    print("Clips per class:")

    for label, count in sorted(
        counts.items(),
        key=lambda x: x[1],
        reverse=True
    ):
        print(f"  {label:15} {count}")

    print()
    print(f"TOTAL DOG CLIPS: {len(all_matches)}")

    # Count splits
    splits = {}

    for item in all_matches:
        split = item["split"]
        splits[split] = splits.get(split, 0) + 1

    print()
    print("Clips by split:")

    for split, count in splits.items():
        print(f"  {split:30} {count}")

    # Save
    output = BASE / "dog_clips.csv"

    with open(
        output,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "split",
                "youtube_id",
                "start",
                "end",
                "label",
            ],
        )

        writer.writeheader()
        writer.writerows(all_matches)

    print()
    print(f"Saved metadata:")
    print(output)
