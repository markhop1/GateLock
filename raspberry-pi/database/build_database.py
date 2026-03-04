"""
Script para construir la base de datos de embeddings faciales.

Usa RetinaFace (InsightFace) para detección y embeddings.
Por defecto utiliza los embeddings de InsightFace (MBF/MobileFaceNet pre-entrenado),
más precisos que un MobileFaceNet sin modelo. Fallback a MobileFaceNet si no hay embedding.
"""
import os
import glob
import argparse
import numpy as np
from pathlib import Path
from tqdm import tqdm
import cv2
import logging

import albumentations as A
from PIL import Image

from config import (
    KNOWN_FACES_DIR, DATABASE_DIR, EMBEDDINGS_FILE, LABELS_FILE,
    AUG_PER_IMAGE, MAX_IMAGES_PER_ID
)
from detection.face_detector import RetinaFaceDetector
from recognition.face_recognizer import MobileFaceNetRecognizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def l2_normalize(x: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    """Normaliza un vector usando L2."""
    return x / (np.linalg.norm(x) + eps)


def build_augmenter():
    """
    Construye el pipeline de augmentación.
    
    Aumentaciones centradas en iluminación + degradaciones realistas moderadas.
    """
    return A.Compose(
        [
            A.RandomBrightnessContrast(brightness_limit=0.35, contrast_limit=0.25, p=0.9),
            A.RandomGamma(gamma_limit=(70, 150), p=0.7),
            A.HueSaturationValue(hue_shift_limit=5, sat_shift_limit=20, val_shift_limit=10, p=0.6),
            A.OneOf(
                [
                    A.GaussianBlur(blur_limit=(3, 7), p=1.0),
                    A.MotionBlur(blur_limit=7, p=1.0),
                ],
                p=0.25,
            ),
            A.GaussNoise(std_range=(0.01, 0.05), mean_range=(0.0, 0.0), per_channel=True, p=0.25),
            A.ImageCompression(quality_range=(35, 95), compression_type="jpeg", p=0.25),
        ]
    )


def quality_gate(face_rgb: np.ndarray) -> bool:
    """
    Filtro de calidad: evita caras demasiado oscuras o demasiado quemadas.
    
    Args:
        face_rgb: Imagen RGB del rostro (HxWx3 uint8)
        
    Returns:
        True si la imagen pasa el filtro de calidad
    """
    gray = cv2.cvtColor(face_rgb, cv2.COLOR_RGB2GRAY)
    mean = float(gray.mean())
    near_black = float((gray < 10).mean())
    near_white = float((gray > 245).mean())
    
    if mean < 35 or mean > 220:
        return False
    if near_black > 0.25:
        return False
    if near_white > 0.25:
        return False
    return True


def list_identities(root_dir: Path) -> list:
    """Lista todas las identidades (carpetas) en el directorio."""
    identities = []
    for d in sorted(root_dir.iterdir()):
        if d.is_dir():
            identities.append(d.name)
    return identities


def list_images_for_identity(root_dir: Path, identity: str) -> list:
    """Lista todas las imágenes de una identidad."""
    identity_dir = root_dir / identity
    exts = ("*.jpg", "*.jpeg", "*.png", "*.webp", "*.bmp")
    files = []
    for ext in exts:
        files.extend(glob.glob(str(identity_dir / ext)))
    return sorted(files)


def main():
    parser = argparse.ArgumentParser(
        description="Construye base de datos de embeddings faciales con augmentación"
    )
    parser.add_argument(
        "--data_dir",
        type=str,
        default=str(KNOWN_FACES_DIR),
        help="Directorio con subcarpetas por persona"
    )
    parser.add_argument(
        "--aug_per_image",
        type=int,
        default=AUG_PER_IMAGE,
        help="Número de aumentaciones por imagen"
    )
    parser.add_argument(
        "--max_images_per_id",
        type=int,
        default=MAX_IMAGES_PER_ID,
        help="Máximo número de imágenes base por identidad"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=str(DATABASE_DIR),
        help="Directorio de salida para embeddings y labels"
    )
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not data_dir.exists():
        logger.error(f"Directorio no encontrado: {data_dir}")
        return
    
    # Inicializar modelos
    logger.info("Inicializando modelos...")
    detector = RetinaFaceDetector()
    detector.initialize()
    
    recognizer = MobileFaceNetRecognizer()
    recognizer.initialize()
    
    # Inicializar augmentación
    aug = build_augmenter()
    
    # Listar identidades
    identities = list_identities(data_dir)
    if not identities:
        logger.error(f"No se encontraron subcarpetas de identidad en {data_dir}")
        return
    
    logger.info(f"Encontradas {len(identities)} identidades")
    
    per_id_agg = {}  # identity -> embedding agregado
    per_id_embs = {}  # identity -> lista de embeddings individuales
    per_id_stats = {}  # identity -> estadísticas
    
    # Procesar cada identidad
    for ident in tqdm(identities, desc="Procesando identidades"):
        img_files = list_images_for_identity(data_dir, ident)[:args.max_images_per_id]
        if not img_files:
            logger.warning(f"No se encontraron imágenes para {ident}")
            continue
        
        collected = []
        used_faces = 0
        skipped = 0
        
        for img_path in img_files:
            try:
                # Cargar imagen
                img_bgr = cv2.imread(str(img_path))
                if img_bgr is None:
                    skipped += 1
                    continue
                
                # Detectar rostro
                detections = detector.detect_faces(img_bgr)
                if not detections:
                    skipped += 1
                    continue
                
                # Usar el rostro más grande
                largest = max(detections, key=lambda d: d.width * d.height)
                
                # Extraer crop del rostro
                face_crop = largest.get_face_crop(img_bgr)
                if face_crop.size == 0:
                    skipped += 1
                    continue
                
                # Convertir a RGB
                face_rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
                
                # Preferir embedding de InsightFace si está disponible (más preciso)
                use_insightface = getattr(largest, 'embedding', None) is not None
                
                if use_insightface:
                    orig_emb = np.asarray(largest.embedding).flatten()
                else:
                    orig_emb = recognizer.extract_embedding(face_rgb)
                
                collected.append(orig_emb)
                used_faces += 1
                
                # Aplicar augmentación
                for _ in range(args.aug_per_image):
                    aug_rgb = aug(image=face_rgb)["image"]
                    
                    # Filtrar por calidad
                    if not quality_gate(aug_rgb):
                        continue
                    
                    # Extraer embedding: InsightFace para crops aumentados, o MobileFaceNet
                    # Importante: no mezclar dimensiones (InsightFace=512 vs MobileFaceNet=128)
                    if use_insightface:
                        aug_emb = detector.extract_embedding_from_face(aug_rgb)
                        if aug_emb is None:
                            continue  # Omitir si falla; evita mezclar 512d con 128d
                        aug_emb = np.asarray(aug_emb).flatten()
                    else:
                        aug_emb = recognizer.extract_embedding(aug_rgb)
                    collected.append(aug_emb)
                
            except Exception as e:
                logger.warning(f"Error procesando {img_path}: {e}")
                skipped += 1
                continue
        
        if len(collected) == 0:
            logger.warning(f"No se generaron embeddings para {ident}")
            continue
        
        # Agregar embeddings (media + L2 normalization)
        mat = np.stack(collected, axis=0)  # (K, embedding_size)
        agg = mat.mean(axis=0)
        agg = l2_normalize(agg)
        
        augs_used = len(collected) - used_faces
        per_id_agg[ident] = agg
        per_id_embs[ident] = mat
        per_id_stats[ident] = {
            "base_images": len(img_files),
            "faces_used": used_faces,
            "augmentations_used": augs_used,
            "skipped": skipped,
            "total_embs": len(collected)
        }
    
    if not per_id_agg:
        logger.error("No se generaron embeddings para ninguna identidad")
        return
    
    # Guardar embeddings agregados y labels
    id_list = sorted(per_id_agg.keys())
    embeddings_array = np.stack([per_id_agg[i] for i in id_list], axis=0)
    labels_array = np.array(id_list)
    
    embeddings_path = output_dir / EMBEDDINGS_FILE.name
    labels_path = output_dir / LABELS_FILE.name
    
    np.save(embeddings_path, embeddings_array)
    np.save(labels_path, labels_array)
    
    logger.info(f"\n=== Resumen ===")
    logger.info(f"Base de datos creada:")
    logger.info(f"  Embeddings: {embeddings_path}")
    logger.info(f"  Labels: {labels_path}")
    logger.info(f"  Total personas: {len(id_list)}")
    logger.info(f"  Total embeddings agregados: {embeddings_array.shape[0]}")
    
    total_augs = sum(per_id_stats[i]["augmentations_used"] for i in id_list)
    logger.info(f"  Augmentaciones utilizadas: {total_augs} embeddings de imágenes aumentadas")
    logger.info(f"\n=== Estadísticas por identidad ===")
    for ident in id_list[:20]:  # Mostrar primeras 20
        stats = per_id_stats[ident]
        logger.info(
            f"{ident}: {stats['faces_used']} rostros, {stats['augmentations_used']} augment., "
            f"{stats['total_embs']} embeddings totales "
            f"({stats['skipped']} imágenes omitidas)"
        )
    
    # Evaluación básica: similitud intra vs inter
    if len(id_list) >= 2:
        logger.info(f"\n=== Evaluación básica ===")
        
        # Similitud intra (dentro de la misma persona)
        intra_sims = []
        for ident in id_list:
            embs = per_id_embs[ident]
            if embs.shape[0] < 2:
                continue
            # Calcular similitud coseno entre pares
            sims = np.dot(embs, embs.T)
            # Obtener parte superior sin diagonal
            iu = np.triu_indices_from(sims, k=1)
            intra_sims.extend(sims[iu].tolist())
        
        # Similitud inter (entre diferentes personas)
        inter_sims = []
        agg_mat = embeddings_array
        sims_agg = np.dot(agg_mat, agg_mat.T)
        iu = np.triu_indices_from(sims_agg, k=1)
        inter_sims = sims_agg[iu].tolist()
        
        if intra_sims and inter_sims:
            intra_mean = np.mean(intra_sims)
            inter_mean = np.mean(inter_sims)
            logger.info(f"Similitud intra (misma persona): media={intra_mean:.3f}")
            logger.info(f"Similitud inter (diferentes personas): media={inter_mean:.3f}")
            
            # Umbral sugerido
            thr = 0.5 * (np.median(intra_sims) + np.median(inter_sims))
            logger.info(f"Umbral sugerido (no calibrado): {thr:.3f}")


if __name__ == "__main__":
    main()
