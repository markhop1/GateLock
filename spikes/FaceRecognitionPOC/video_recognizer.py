# video_recognizer.py
from pathlib import Path
import sys

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
    """Load face embeddings and labels from disk."""
    emb_path = base_dir / "face_embeddings.npy"
    labels_path = base_dir / "face_labels.npy"

    if not emb_path.exists() or not labels_path.exists():
        print("Database files not found.")
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
    """Return best matching label and similarity."""
    sims = known_embeddings @ face_emb
    idx = int(np.argmax(sims))
    sim = float(sims[idx])
    if sim >= threshold:
        return known_labels[idx], sim
    return "Unknown", sim


def process_video(video_path: Path, output_path: Path | None = None, threshold: float = 0.5):
    base_dir = Path(__file__).resolve().parent

    known_embeddings, known_labels = load_db(base_dir)

    print("Loading InsightFace model (buffalo_s)...")
    app = FaceAnalysis(
        name="buffalo_s",
        providers=["CPUExecutionProvider"],
    )
    app.prepare(ctx_id=0, det_size=(320, 320))
    print("Model loaded.")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"Unable to open video: {video_path}")
        sys.exit(1)

    writer = None
    if output_path is not None:
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 25.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    frame_index = 0
    print("Starting video processing...")

    while True:
        ret, frame_bgr = cap.read()
        if not ret:
            break

        frame_index += 1
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

            name, sim = recognize_face(emb, known_embeddings, known_labels, threshold=threshold)

            x1, y1, x2, y2 = face.bbox.astype(int)
            cv2.rectangle(frame_bgr, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame_bgr,
                f"{name} ({sim:.2f})",
                (x1, max(0, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

        # Optional: show in a window while processing
        cv2.imshow("Video face recognition (press q to stop)", frame_bgr)
        if writer is not None:
            writer.write(frame_bgr)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    cap.release()
    if writer is not None:
        writer.release()
    cv2.destroyAllWindows()
    print("Video processing finished.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python video_recognizer.py <input_video> [output_video]")
        sys.exit(1)

    input_video = Path(sys.argv[1])
    if len(sys.argv) >= 3:
        output_video = Path(sys.argv[2])
    else:
        output_video = None

    process_video(input_video, output_video, threshold=0.5)
