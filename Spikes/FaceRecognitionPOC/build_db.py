import os
from pathlib import Path

import cv2
import numpy as np
from insightface.app import FaceAnalysis


def ensure_normed_embedding(face):
    """
    Devuelve un embedding L2-normalizado (norma = 1).
    Usa face.normed_embedding si existe, si no, normaliza face.embedding.
    """
    emb = getattr(face, "normed_embedding", None)
    if emb is None:
        emb = face.embedding
        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm
    return emb


def main():
    # Carpeta raíz del proyecto (donde está este script)
    base_dir = Path(__file__).resolve().parent

    # Carpeta con las fotos de entrenamiento
    known_faces_dir = base_dir / "known_faces"

    if not known_faces_dir.exists():
        print(f"❌ Carpeta no encontrada: {known_faces_dir}")
        print("Crea 'known_faces/<nombre_persona>/' con algunas fotos dentro.")
        return

    # Inicializar InsightFace
    print("🔧 Cargando modelo InsightFace (buffalo_s)...")
    app = FaceAnalysis(
        name="buffalo_s",
        providers=["CPUExecutionProvider"],  # Solo CPU en la Raspberry
    )
    app.prepare(ctx_id=0, det_size=(320, 320))
    print("✅ Modelo cargado.")

    embeddings = []
    labels = []

    # Recorrer subcarpetas: cada una es una persona
    for person_dir in sorted(known_faces_dir.iterdir()):
        if not person_dir.is_dir():
            continue

        person_name = person_dir.name
        print(f"\n👤 Procesando persona: {person_name}")

        # Recorrer imágenes de esa persona
        for img_path in sorted(person_dir.iterdir()):
            if not img_path.is_file():
                continue

            if img_path.suffix.lower() not in [".jpg", ".jpeg", ".png", ".bmp"]:
                continue

            print(f"  🖼️  Imagen: {img_path.name}")

            img_bgr = cv2.imread(str(img_path))
            if img_bgr is None:
                print("   ⚠️ No se pudo leer la imagen, la salto.")
                continue

            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

            # Detectar caras
            faces = app.get(img_rgb)

            if len(faces) == 0:
                print("   ⚠️ No se detectó ninguna cara en esta imagen, la salto.")
                continue

            # Para simplificar: nos quedamos con la cara con mayor puntuación
            faces_sorted = sorted(faces, key=lambda f: f.det_score, reverse=True)
            best_face = faces_sorted[0]

            emb = ensure_normed_embedding(best_face)
            if emb is None:
                print("   ⚠️ No se pudo obtener embedding, salto esta imagen.")
                continue

            embeddings.append(emb)
            labels.append(person_name)

    if not embeddings:
        print("\n❌ No se generó ningún embedding. Revisa tus imágenes.")
        return

    embeddings = np.stack(embeddings, axis=0)
    labels = np.array(labels)

    # Guardar en disco
    emb_path = base_dir / "face_embeddings.npy"
    labels_path = base_dir / "face_labels.npy"

    np.save(emb_path, embeddings)
    np.save(labels_path, labels)

    print("\n✅ Base de datos creada correctamente:")
    print(f"   → Embeddings: {emb_path}")
    print(f"   → Labels:     {labels_path}")
    print(f"   Número total de caras registradas: {embeddings.shape[0]}")


if __name__ == "__main__":
    main()
