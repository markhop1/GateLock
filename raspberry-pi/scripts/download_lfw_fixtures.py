#!/usr/bin/env python3
"""
Download face images from the LFW (Labeled Faces in the Wild) dataset via TensorFlow Datasets
and save them in the directory structure expected by build_database.py (known_faces/).

Use this script to quickly obtain real face images for testing the recognition pipeline
without manually collecting photos.

Requirements: pip install tensorflow-datasets
"""

import argparse
import re
from collections import defaultdict
from pathlib import Path

import tensorflow_datasets as tfds
from PIL import Image


def sanitize_folder_name(name: str) -> str:
    """Convert person name to a filesystem-safe folder name."""
    return re.sub(r"[^\w\-]", "_", name)[:50]


def main():
    parser = argparse.ArgumentParser(
        description="Download LFW face images and save them for build_database.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/download_lfw_fixtures.py
  python scripts/download_lfw_fixtures.py --output tests/fixtures/test_images --max-people 3
  python scripts/download_lfw_fixtures.py --max-people 10 --max-images-per 5
        """,
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory (default: raspberry-pi/known_faces)",
    )
    parser.add_argument(
        "--max-people",
        type=int,
        default=5,
        help="Maximum number of people to download (default: 5)",
    )
    parser.add_argument(
        "--max-images-per",
        type=int,
        default=5,
        help="Maximum images per person (default: 5)",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent
    output_dir = Path(args.output) if args.output else base_dir / "known_faces"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Downloading LFW dataset (first run may take a few minutes, ~172 MB)...")
    ds = tfds.load("lfw", split="train", as_supervised=False)

    # Collect multiple images per person (person -> list of image arrays)
    collected: dict[str, list] = defaultdict(list)

    for example in ds:
        # Stop when we have enough people, each with enough images
        if len(collected) >= args.max_people:
            if all(len(imgs) >= args.max_images_per for imgs in collected.values()):
                break
        else:
            # Still filling up to max_people
            pass

        image = example["image"].numpy()
        label = example["label"].numpy()

        person_name = label.decode("utf-8") if isinstance(label, bytes) else str(label)
        folder_name = sanitize_folder_name(person_name)

        # Skip if this person already has enough images
        if len(collected.get(folder_name, [])) >= args.max_images_per:
            continue

        # Add new person only if under limit (use .get to avoid creating key)
        if folder_name not in collected and len(collected) >= args.max_people:
            continue

        collected[folder_name].append(image)

    # Save to disk
    total_saved = 0
    for folder_name, images in collected.items():
        if not images:
            continue
        person_dir = output_dir / folder_name
        person_dir.mkdir(parents=True, exist_ok=True)
        for i, img_array in enumerate(images):
            filepath = person_dir / f"{i}.jpg"
            Image.fromarray(img_array).save(filepath)
            print(f"  Saved: {folder_name}/{i}.jpg")
            total_saved += 1

    print(f"\nDone. {len(collected)} people, {total_saved} images saved to {output_dir}")


if __name__ == "__main__":
    main()
