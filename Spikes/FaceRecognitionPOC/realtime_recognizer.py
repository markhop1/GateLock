import sys
from pathlib import Path

import cv2
import numpy as np
from insightface.app import FaceAnalysis


def ensure_normed_embedding(face):
    emb = getattr(face, "normed_embedding", None)
    if emb is None:
        emb = face.embedding
        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm
    return emb


def load_db(base_dir: Path):
    emb_path = base_dir / "face_embeddings.npy"
    labels_path = base_dir / "face_labels.npy"

    if not emb_path.exists() or not labels_path.exists():
        print("❌ No se encontraron los archivos de base de datos:")
        print(f"   {emb_path}")
        print(f"   {labels_path}")
        print("   Ejecuta primero: python build_db.py")
        sys.exit(1)

    embeddings = np.load(emb_path)
    labels = np.load(labels_path)

    if embeddings.ndim != 2:
        raise ValueError("Los embeddings deben tener forma (N, D).")

    # Asegurarnos de que están normalizados
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    embeddings = embeddings / norms

    return embeddings, labels


def recognize_face(face_emb, known_embeddings, known_labels, threshold=0.5):
    """
    face_emb: vector normalizado (D,)
    known_embeddings: matriz (N, D)
    Devuelve (nombre, similitud)
    """
    # Producto escalar = similitud de coseno (si están normalizados)
    sims = known_embeddings @ face_emb
    best_idx = int(np.argmax(sims))
    best_sim = float(sims[best_idx])

    if best_sim >= threshold:
        return known_labels[best_idx], best_sim
    else:
        return "Desconocido", best_sim


def main():
    base_dir = Path(__file__).resolve().parent

    # 1) Cargar base de datos
    print("📂 Cargando base de datos de caras...")
    known_embeddings, known_labels = load_db(base_dir)
    print(f"✅ Base cargada con {known_embeddings.shape[0]} embeddings.")

    # 2) Inicializar InsightFace
    print("🔧 Cargando modelo InsightFace (buffalo_s)...")
    app = FaceAnalysis(
        name="buffalo_s",
        providers=["CPUExecutionProvider"],
    )
    app.prepare(ctx_id=0, det_size=(320, 320))
    print("✅ Modelo cargado.")

    # 3) Abrir cámara
    print("📷 Abriendo cámara (VideoCapture 0)...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ No se pudo abrir la cámara. Revisa el índice (0, 1, ...) o permisos.")
        sys.exit(1)

    print("▶️ Reconocimiento facial en tiempo real iniciado.")
    print("   Pulsa 'q' en la ventana para salir.")

    while True:
        ret, frame_bgr = cap.read()
        if not ret:
            print("⚠️ No se pudo leer frame de la cámara.")
            break

        # InsightFace espera RGB
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        # Detectar caras
        faces = app.get(frame_rgb)

        for face in faces:
            emb = ensure_normed_embedding(face)
            if emb is None:
                continue

            # Asegurarnos de que está normalizado
            emb = emb.astype(np.float32)
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm

            name, sim = recognize_face(emb, known_embeddings, known_labels, threshold=0.5)

            # Dibujar bbox y texto
            x1, y1, x2, y2 = face.bbox.astype(int)
            cv2.rectangle(frame_bgr, (x1, y1), (x2, y2), (0, 255, 0), 2)

            text = f"{name} ({sim:.2f})"
            cv2.putText(
                frame_bgr,
                text,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

        cv2.imshow("Reconocimiento facial - q para salir", frame_bgr)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("👋 Programa terminado.")


if __name__ == "__main__":
    main()
