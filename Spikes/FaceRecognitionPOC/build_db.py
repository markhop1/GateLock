import os
from pathlib import Path

import cv2
import numpy as np
from insightface.app import FaceAnalysis


def ensure_normed_embedding(face):
    """Return an L2-normalized embedding. Use face.normed_embedding if available."""
    emb = getattr(face, "normed_embedding", None)
    if emb is None:
        emb = face.embedding
        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm
    return emb


def main():
    base_dir = Path(__file__).resolve().parent
    known_faces_dir = base_dir / "known_faces"

    if not known_faces_dir.exists():
        print(f"Directory not found: {known_faces_dir}")
        print("Create 'known_faces/<person_name>/' and include training images.")
        return

    print("Loading InsightFace model (buffalo_s)...")
    app = FaceAnalysis(
        name="buffalo_s",
        providers=["CPUExecutionProvider"],
    )
    app.prepare(ctx_id=0, det_size=(320, 320))
    print("Model loaded.")

    embeddings, labels = [], []

    for person_dir in sorted(known_faces_dir.iterdir()):
        if not person_dir.is_dir():
            continue

        person_name = person_dir.name
        print(f"Processing: {person_name}")

        for img_path in sorted(person_dir.iterdir()):
            if not img_path.is_file():
                continue

            if img_path.suffix.lower() not in [".jpg", ".jpeg", ".png", ".bmp"]:
                continue

            print(f"  Image: {img_path.name}")

            img_bgr = cv2.imread(str(img_path))
            if img_bgr is None:
                print("  Could not read image. Skipping.")
                continue

            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            faces = app.get(img_rgb)

            if len(faces) == 0:
                print("  No face detected. Skipping.")
                continue

            best_face = sorted(faces, key=lambda f: f.det_score, reverse=True)[0]
            emb = ensure_normed_embedding(best_face)

            if emb is None:
                print("  Could not extract embedding. Skipping.")
                continue

            embeddings.append(emb)
            labels.append(person_name)

    if not embeddings:
        print("No embeddings generated. Check your dataset.")
        return

    embeddings = np.stack(embeddings, axis=0)
    labels = np.array(labels)

    emb_path = base_dir / "face_embeddings.npy"
    labels_path = base_dir / "face_labels.npy"

    np.save(emb_path, embeddings)
    np.save(labels_path, labels)

    print("Database created:")
    print(f"  Embeddings: {emb_path}")
    print(f"  Labels:     {labels_path}")
    print(f"  Total faces: {embeddings.shape[0]}")


if __name__ == "__main__":
    main()
