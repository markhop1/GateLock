import sys
from pathlib import Path

import cv2
import numpy as np
from insightface.app import FaceAnalysis


def ensure_normed_embedding(face):
    """Return an L2-normalized embedding."""
    emb = getattr(face, "normed_embedding", None)
    if emb is None:
        emb = face.embedding
        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm
    return emb


def load_db(base_dir: Path):
    """Load embeddings and labels from disk."""
    emb_path = base_dir / "face_embeddings.npy"
    labels_path = base_dir / "face_labels.npy"

    if not emb_path.exists() or not labels_path.exists():
        print("Database files not found:")
        print(f"  {emb_path}")
        print(f"  {labels_path}")
        print("Run: python build_db.py")
        sys.exit(1)

    embeddings = np.load(emb_path)
    labels = np.load(labels_path)

    if embeddings.ndim != 2:
        raise ValueError("Embeddings must have shape (N, D).")

    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    embeddings = embeddings / norms

    return embeddings, labels


def recognize_face(face_emb, known_embeddings, known_labels, threshold=0.5):
    """Return the best matching label and similarity."""
    sims = known_embeddings @ face_emb
    idx = int(np.argmax(sims))
    sim = float(sims[idx])
    if sim >= threshold:
        return known_labels[idx], sim
    return "Unknown", sim


def main():
    base_dir = Path(__file__).resolve().parent

    print("Loading face database...")
    known_embeddings, known_labels = load_db(base_dir)
    print(f"Loaded {known_embeddings.shape[0]} embeddings.")

    print("Loading InsightFace model (buffalo_s)...")
    app = FaceAnalysis(
        name="buffalo_s",
        providers=["CPUExecutionProvider"],
    )
    app.prepare(ctx_id=0, det_size=(320, 320))
    print("Model loaded.")

    print("Opening camera (index 0)...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Unable to access camera. Check device index or permissions.")
        sys.exit(1)

    print("Real-time face recognition started. Press 'q' to exit.")

    while True:
        ret, frame_bgr = cap.read()
        if not ret:
            print("Unable to capture frame.")
            break

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        faces = app.get(frame_rgb)

        for face in faces:
            emb = ensure_normed_embedding(face)
            if emb is None:
                continue

            emb = emb.astype(np.float32)
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm

            name, sim = recognize_face(emb, known_embeddings, known_labels, threshold=0.5)

            x1, y1, x2, y2 = face.bbox.astype(int)
            cv2.rectangle(frame_bgr, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame_bgr,
                f"{name} ({sim:.2f})",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

        cv2.imshow("Real-time facial recognition (press q to exit)", frame_bgr)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Program terminated.")
    

if __name__ == "__main__":
    main()
