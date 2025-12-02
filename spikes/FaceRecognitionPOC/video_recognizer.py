# video_recognizer.py
import sys
from pathlib import Path
import argparse

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


def process_video(
    video_path: Path,
    output_path: Path | None = None,
    display: bool = False,
    skip_frames: int = 1,
    resize_width: int = 0,
    threshold: float = 0.5,
):
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

    if skip_frames < 1:
        skip_frames = 1

    writer = None
    frame_index = 0
    summary_counts: dict[str, int] = {}

    print("Starting video processing...")

    while True:
        ret, frame_bgr = cap.read()
        if not ret:
            break

        frame_index += 1

        if frame_index % skip_frames != 0:
            # Fast path: skip processing this frame
            if display:
                cv2.imshow("Video face recognition", frame_bgr)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            if writer is not None:
                writer.write(frame_bgr)
            continue

        processed_frame = frame_bgr

        if resize_width > 0:
            h, w = processed_frame.shape[:2]
            if w != resize_width:
                scale = resize_width / float(w)
                new_h = int(h * scale)
                processed_frame = cv2.resize(processed_frame, (resize_width, new_h))

        frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
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

            summary_counts[name] = summary_counts.get(name, 0) + 1

            x1, y1, x2, y2 = face.bbox.astype(int)
            cv2.rectangle(processed_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                processed_frame,
                f"{name} ({sim:.2f})",
                (x1, max(0, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

        if display:
            cv2.imshow("Video face recognition", processed_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        if output_path is not None:
            if writer is None:
                height, width = processed_frame.shape[:2]
                fps = cap.get(cv2.CAP_PROP_FPS)
                if fps <= 0:
                    fps = 25.0
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
            writer.write(processed_frame)

    cap.release()
    if writer is not None:
        writer.release()
    if display:
        cv2.destroyAllWindows()

    print("Video processing finished.")

    print()
    if not summary_counts:
        print("No faces recognized.")
        return

    known = {k: v for k, v in summary_counts.items() if k != "Unknown"}
    unknown_count = summary_counts.get("Unknown", 0)

    print("We found these persons:")
    if known:
        for name, count in sorted(known.items(), key=lambda x: -x[1]):
            print(f"  {name}: {count} detections")
    else:
        print("  (no known persons)")

    if unknown_count > 0:
        print(f"  Unknown: {unknown_count} detections")


def parse_args():
    parser = argparse.ArgumentParser(description="Video face recognition with InsightFace.")
    parser.add_argument("input_video", type=str, help="Path to input video.")
    parser.add_argument(
        "--output-video",
        type=str,
        default=None,
        help="Path to save annotated video. If omitted, no video is written.",
    )
    parser.add_argument(
        "--display",
        action="store_true",
        help="Display video while processing.",
    )
    parser.add_argument(
        "--skip-frames",
        type=int,
        default=1,
        help="Process every N-th frame (default: 1, no skipping).",
    )
    parser.add_argument(
        "--resize-width",
        type=int,
        default=0,
        help="Resize frames to this width while processing. 0 disables resizing.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Similarity threshold for recognition.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    input_video = Path(args.input_video)
    output_video = Path(args.output_video) if args.output_video is not None else None

    process_video(
        video_path=input_video,
        output_path=output_video,
        display=args.display,
        skip_frames=args.skip_frames,
        resize_width=args.resize_width,
        threshold=args.threshold,
    )
