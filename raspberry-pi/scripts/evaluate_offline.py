#!/usr/bin/env python3
"""
Evaluación offline del sistema de reconocimiento facial GateLock.

Pipeline:
  1. Lee fotos organizadas por persona desde un directorio local.
  2. Divide aleatoriamente en enrollment (gallery) y probe.
  3. Construye embeddings del gallery con InsightFace buffalo_l.
  4. Evalúa cada foto del probe:
       a. Métricas a umbral fijo → TP / FP / FN / TN, Precision, Recall, F1, Accuracy
       b. Pares genuine/impostor → ROC, AUC, EER (curva suave, no escalera)
  5. Genera un Excel con 5 hojas y gráficas.

Uso (ejecutar desde ~/GateLock/raspberry-pi):

  # Descarga LFW automáticamente y evalúa
  python scripts/evaluate_offline.py \\
      --download-lfw ~/data/lfw \\
      --output       ~/resultados/evaluacion_noaug.xlsx \\
      --max-people 50 --min-photos 8

  # Con datos ya descargados
  python scripts/evaluate_offline.py \\
      --data-dir  ~/data/lfw \\
      --output    ~/resultados/evaluacion_noaug.xlsx

  # Con augmentación (para comparar)
  python scripts/evaluate_offline.py \\
      --data-dir      ~/data/lfw \\
      --output        ~/resultados/evaluacion_aug.xlsx \\
      --augment --aug-per-image 10

Descarga de LFW:
  El script intenta primero http://vis-www.cs.umass.edu/lfw/lfw.tgz.
  Si falla, usa scikit-learn como fallback (mirror Figshare, ~233 MB).
  Instalar fallback: pip install scikit-learn pillow

Requisitos: insightface  openpyxl  opencv-python  numpy  tqdm
            albumentations  (solo con --augment)
            scikit-learn pillow  (fallback de descarga)
"""

from __future__ import annotations

import argparse
import logging
import math
import random
import sys
import tarfile
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from tqdm import tqdm
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference, ScatterChart, Series
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from insightface.app import FaceAnalysis
from config import RETINAFACE_MODEL_NAME, RETINAFACE_DET_SIZE

try:
    import albumentations as A
    from insightface.utils import face_align as _face_align
    ALBUMENTATIONS_AVAILABLE = True
except ImportError:
    ALBUMENTATIONS_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Constantes de estilo Excel ────────────────────────────────────────────────
COLOR_HEADER = "1F4E79"
COLOR_BLUE   = "2F75B6"
COLOR_ORANGE = "C55A11"
COLOR_ALT    = "F2F2F2"
CLF_COLORS   = {"TP": "C6EFCE", "FP": "FFC7CE", "FN": "FFEB9C", "TN": "DDEBF7"}
SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}

LFW_URL = "http://vis-www.cs.umass.edu/lfw/lfw.tgz"


# ══════════════════════════════════════════════════════════════════════════════
# Descarga de LFW
# ══════════════════════════════════════════════════════════════════════════════

def _download_lfw_sklearn(dest: Path, max_people: int, min_photos: int) -> None:
    """
    Fallback: descarga LFW via scikit-learn desde Figshare (~233 MB, versión funneled).
    Requiere: pip install scikit-learn pillow
    """
    try:
        from sklearn.datasets import fetch_lfw_people
        from PIL import Image as PILImage
    except ImportError:
        raise RuntimeError(
            "scikit-learn y/o pillow no están instalados.\n"
            "  pip install scikit-learn pillow\n"
            "O descarga LFW manualmente desde Kaggle y cópialo a la Pi:\n"
            "  https://www.kaggle.com/datasets/jessicali9530/lfw-dataset"
        )

    logger.info("Descargando LFW via scikit-learn (mirror Figshare) ...")
    lfw = fetch_lfw_people(
        min_faces_per_person=min_photos,
        resize=1.0,
        color=True,
        download_if_missing=True,
    )

    # lfw.images: [N, H, W, 3]  float32 en [0,1]  ó  uint8
    # lfw.target: índice de clase por muestra
    # lfw.target_names: nombres de personas
    logger.info(f"  → {len(lfw.target_names)} personas, {len(lfw.images)} fotos descargadas")

    # Contar fotos por persona y limitar a max_people (los que más fotos tienen)
    from collections import Counter
    counts  = Counter(lfw.target)
    top_ids = {idx for idx, _ in counts.most_common(max_people)}

    saved = 0
    for i, (img, t) in enumerate(tqdm(zip(lfw.images, lfw.target), total=len(lfw.images), desc="Guardando")):
        if t not in top_ids:
            continue
        person_dir = dest / lfw.target_names[t]
        person_dir.mkdir(parents=True, exist_ok=True)
        img_u8 = (img * 255).clip(0, 255).astype("uint8") if img.dtype != "uint8" else img
        PILImage.fromarray(img_u8).save(person_dir / f"{i:05d}.jpg")
        saved += 1

    logger.info(f"  → {saved} fotos guardadas en {dest}")


def download_lfw(dest: Path, max_people: int, min_photos: int) -> None:
    """
    Descarga LFW y organiza las fotos en dest/person_name/foto.jpg.
    Intenta primero la URL directa de UMass; si falla, usa scikit-learn (Figshare).
    """
    dest.mkdir(parents=True, exist_ok=True)

    # ── ¿Ya está descargado? ──────────────────────────────────────────────────
    existing = [d for d in dest.iterdir() if d.is_dir()]
    if existing:
        logger.info(f"Directorio ya contiene {len(existing)} carpetas, usando caché: {dest}")
        return

    # ── Intentar descarga directa ─────────────────────────────────────────────
    tgz_path = dest / "lfw.tgz"
    direct_ok = False

    if not tgz_path.exists():
        logger.info(f"Intentando descarga directa desde {LFW_URL} ...")
        try:
            def _progress(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if total_size > 0:
                    pct = min(100, downloaded * 100 // total_size)
                    print(f"\r  {pct}% ({downloaded // 1_048_576} MB / {total_size // 1_048_576} MB)", end="")

            urllib.request.urlretrieve(LFW_URL, tgz_path, reporthook=_progress)
            print()
            direct_ok = True
            logger.info("Descarga directa completada.")
        except Exception as e:
            logger.warning(f"Descarga directa fallida ({e}). Usando mirror scikit-learn (Figshare) ...")
            if tgz_path.exists():
                tgz_path.unlink()
    else:
        direct_ok = True

    if not direct_ok:
        _download_lfw_sklearn(dest, max_people, min_photos)
        return

    # ── Extraer .tgz ─────────────────────────────────────────────────────────
    logger.info("Extrayendo y filtrando personas ...")
    by_person: dict[str, list] = defaultdict(list)
    with tarfile.open(tgz_path, "r:gz") as tar:
        for m in tar.getmembers():
            parts = Path(m.name).parts
            if len(parts) < 3 or not m.name.lower().endswith(tuple(SUPPORTED_EXTS)):
                continue
            by_person[parts[1]].append(m)

    qualified = {p: ms for p, ms in by_person.items() if len(ms) >= min_photos}
    selected  = dict(sorted(qualified.items(), key=lambda x: -len(x[1]))[:max_people])
    logger.info(f"  → {len(selected)} personas con >= {min_photos} fotos")

    with tarfile.open(tgz_path, "r:gz") as tar:
        for person, members in tqdm(selected.items(), desc="Extrayendo"):
            person_dir = dest / person
            person_dir.mkdir(exist_ok=True)
            for m in members:
                f = tar.extractfile(m)
                if f:
                    (person_dir / Path(m.name).name).write_bytes(f.read())

    logger.info(f"LFW preparado en: {dest}")


# ══════════════════════════════════════════════════════════════════════════════
# Carga de datos
# ══════════════════════════════════════════════════════════════════════════════

def load_data(data_dir: Path, min_photos: int, max_people: Optional[int]) -> dict[str, list[Path]]:
    data: dict[str, list[Path]] = {}
    for person_dir in sorted(data_dir.iterdir()):
        if not person_dir.is_dir():
            continue
        photos = sorted(p for p in person_dir.iterdir() if p.suffix.lower() in SUPPORTED_EXTS)
        if len(photos) >= min_photos:
            data[person_dir.name] = photos

    if max_people and len(data) > max_people:
        data = dict(sorted(data.items(), key=lambda x: -len(x[1]))[:max_people])

    return data


def split_data(
    data: dict[str, list[Path]], enroll_ratio: float, seed: int
) -> tuple[dict[str, list[Path]], dict[str, list[Path]]]:
    rng = random.Random(seed)
    gallery: dict[str, list[Path]] = {}
    probe:   dict[str, list[Path]] = {}
    for person, photos in data.items():
        shuffled = photos.copy()
        rng.shuffle(shuffled)
        n = max(1, math.ceil(len(shuffled) * enroll_ratio))
        gallery[person] = shuffled[:n]
        probe[person]   = shuffled[n:]
    return gallery, probe


# ══════════════════════════════════════════════════════════════════════════════
# InsightFace
# ══════════════════════════════════════════════════════════════════════════════

def build_face_app() -> FaceAnalysis:
    app = FaceAnalysis(name=RETINAFACE_MODEL_NAME, providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=0, det_size=RETINAFACE_DET_SIZE)
    return app


def get_embedding(app: FaceAnalysis, img_bgr: np.ndarray) -> Optional[np.ndarray]:
    """Devuelve embedding L2-normalizado 512D o None si no hay cara."""
    faces = app.get(img_bgr)
    if not faces:
        return None
    face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
    return face.normed_embedding.astype(np.float32)


# ── Augmentación ──────────────────────────────────────────────────────────────

def _build_augmenter():
    return A.Compose([
        A.RandomBrightnessContrast(brightness_limit=0.35, contrast_limit=0.25, p=0.9),
        A.RandomGamma(gamma_limit=(70, 150), p=0.7),
        A.HueSaturationValue(hue_shift_limit=5, sat_shift_limit=20, val_shift_limit=10, p=0.6),
        A.OneOf([
            A.GaussianBlur(blur_limit=(3, 7), p=1.0),
            A.MotionBlur(blur_limit=7, p=1.0),
        ], p=0.25),
        A.GaussNoise(std_range=(0.01, 0.05), mean_range=(0.0, 0.0), per_channel=True, p=0.25),
        A.ImageCompression(quality_range=(35, 95), compression_type="jpeg", p=0.25),
    ])


def _augment_embeddings(
    app: FaceAnalysis, img_bgr: np.ndarray, augmenter, n: int
) -> list[np.ndarray]:
    faces = app.get(img_bgr)
    if not faces:
        return []
    face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
    crop     = _face_align.norm_crop(img_bgr, face.kps)        # 112×112 BGR
    crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)

    embs = []
    for _ in range(n):
        aug_rgb = augmenter(image=crop_rgb)["image"]
        aug_bgr = cv2.cvtColor(aug_rgb, cv2.COLOR_RGB2BGR)
        emb = get_embedding(app, aug_bgr)
        if emb is not None:
            embs.append(emb)
    return embs


# ══════════════════════════════════════════════════════════════════════════════
# Construcción de gallery y evaluación
# ══════════════════════════════════════════════════════════════════════════════

def build_gallery(
    app: FaceAnalysis,
    gallery_data: dict[str, list[Path]],
    augment: bool,
    aug_per_image: int,
) -> dict[str, np.ndarray]:
    """
    Devuelve {persona: embedding_medio_L2normalizado}.
    Si augment=True, añade aug_per_image embeddings augmentados por foto.
    """
    if augment and not ALBUMENTATIONS_AVAILABLE:
        logger.warning("albumentations no instalado — ignorando --augment")
        augment = False

    augmenter = _build_augmenter() if augment else None
    gallery_embs: dict[str, np.ndarray] = {}
    skipped = 0

    for person, photos in tqdm(gallery_data.items(), desc="Gallery"):
        embs: list[np.ndarray] = []
        for photo_path in photos:
            img_bgr = cv2.imread(str(photo_path))
            if img_bgr is None:
                skipped += 1
                continue
            emb = get_embedding(app, img_bgr)
            if emb is None:
                skipped += 1
                continue
            embs.append(emb)
            if augment and augmenter is not None:
                embs.extend(_augment_embeddings(app, img_bgr, augmenter, aug_per_image))

        if embs:
            mean_emb = np.mean(embs, axis=0)
            norm = np.linalg.norm(mean_emb)
            gallery_embs[person] = mean_emb / norm if norm > 1e-12 else mean_emb

    if skipped:
        logger.warning(f"  Gallery: {skipped} imágenes omitidas (sin cara / no legibles)")
    return gallery_embs


def run_probe(
    app: FaceAnalysis,
    probe_data: dict[str, list[Path]],
    gallery_embs: dict[str, np.ndarray],
    threshold: float,
) -> list[dict]:
    """
    Evalúa cada foto del probe.
    Devuelve lista de eventos con similitudes frente a todo el gallery.
    """
    gallery_names  = sorted(gallery_embs.keys())
    gallery_matrix = np.stack([gallery_embs[n] for n in gallery_names])  # [N, 512]

    results: list[dict] = []
    skipped = 0

    for true_person, photos in tqdm(probe_data.items(), desc="Probe"):
        is_enrolled = true_person in gallery_embs
        for photo_path in photos:
            img_bgr = cv2.imread(str(photo_path))
            if img_bgr is None:
                skipped += 1
                continue
            emb = get_embedding(app, img_bgr)
            if emb is None:
                skipped += 1
                continue

            sims      = gallery_matrix @ emb            # cosine similarity
            best_idx  = int(np.argmax(sims))
            best_sim  = float(sims[best_idx])
            best_name = gallery_names[best_idx]

            matched   = 1 if best_sim >= threshold else 0
            predicted = best_name if matched else "UNKNOWN"

            results.append({
                "photo":           photo_path.name,
                "true_person":     true_person,
                "predicted_person": predicted,
                "best_match":      best_name,
                "similarity":      round(best_sim, 4),
                "matched":         matched,
                "threshold":       threshold,
                "is_enrolled":     is_enrolled,
                # Similitudes completas — usadas para pares genuine/impostor
                "_sims": dict(zip(gallery_names, sims.tolist())),
            })

    if skipped:
        logger.warning(f"  Probe: {skipped} imágenes omitidas (sin cara / no legibles)")
    return results


# ══════════════════════════════════════════════════════════════════════════════
# Pares genuine / impostor y métricas
# ══════════════════════════════════════════════════════════════════════════════

def build_pairs(results: list[dict]) -> list[dict]:
    """
    Por cada foto del probe genera un par por cada persona del gallery:
      genuine  (label=1): true_person == gallery_person
      impostor (label=0): true_person != gallery_person
    """
    pairs: list[dict] = []
    for r in results:
        tp = r["true_person"]
        for gp, sim in r["_sims"].items():
            pairs.append({
                "label":       1 if tp == gp else 0,
                "similarity":  float(sim),
                "true_person": tp,
            })
    return pairs


def _pct(num: float, den: float) -> float:
    return round(num / den, 4) if den else 0.0


def compute_roc(pairs: list[dict]) -> list[dict]:
    y_true  = [p["label"]      for p in pairs]
    y_score = [p["similarity"] for p in pairs]
    total_p = sum(y_true)
    total_n = len(y_true) - total_p
    points: list[dict] = []
    for i in range(101):
        thr = round(i / 100, 2)
        tp  = sum(1 for yt, ys in zip(y_true, y_score) if yt == 1 and ys >= thr)
        fp  = sum(1 for yt, ys in zip(y_true, y_score) if yt == 0 and ys >= thr)
        fn  = total_p - tp
        tn  = total_n - fp
        points.append({
            "threshold": thr,
            "TPR":       _pct(tp, total_p),
            "FPR":       _pct(fp, total_n),
            "FAR":       _pct(fp, total_n),
            "FRR":       _pct(fn, total_p) if total_p else 0.0,
            "TP": tp, "FP": fp, "FN": fn, "TN": tn,
        })
    return points


def compute_auc(roc: list[dict]) -> float:
    pts  = sorted(roc, key=lambda x: x["FPR"])
    area = 0.0
    for i in range(1, len(pts)):
        dx    = pts[i]["FPR"] - pts[i - 1]["FPR"]
        dy    = (pts[i]["TPR"] + pts[i - 1]["TPR"]) / 2
        area += dx * dy
    return round(abs(area), 4)


def compute_eer(roc: list[dict]) -> tuple[float, float]:
    """Devuelve (EER, umbral_EER)."""
    best = min(roc, key=lambda x: abs(x["FAR"] - x["FRR"]))
    return round((best["FAR"] + best["FRR"]) / 2, 4), best["threshold"]


def _classify(row: dict) -> str:
    is_enrolled = row["is_enrolled"]
    matched     = row["matched"]
    pred        = row["predicted_person"]
    true        = row["true_person"]
    if matched == 1 and is_enrolled and pred == true:
        return "TP"
    if matched == 1 and (not is_enrolled or pred != true):
        return "FP"
    if matched == 0 and is_enrolled:
        return "FN"
    if matched == 0 and not is_enrolled:
        return "TN"
    return ""


# ══════════════════════════════════════════════════════════════════════════════
# Excel helpers
# ══════════════════════════════════════════════════════════════════════════════

def _header_row(ws, row: int, headers: list) -> None:
    fill = PatternFill("solid", fgColor=COLOR_HEADER)
    font = Font(bold=True, color="FFFFFF")
    for col, h in enumerate(headers, start=1):
        cell = ws.cell(row=row, column=col, value=h)
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal="center")


def _auto_width(ws, max_width: int = 30) -> None:
    for col_cells in ws.columns:
        width  = max(len(str(c.value or "")) for c in col_cells)
        letter = get_column_letter(col_cells[0].column)
        ws.column_dimensions[letter].width = min(width + 2, max_width)


# ══════════════════════════════════════════════════════════════════════════════
# Hojas Excel
# ══════════════════════════════════════════════════════════════════════════════

def sheet_raw(wb: Workbook, results: list[dict]) -> None:
    ws = wb.create_sheet("Datos Brutos")
    headers = [
        "photo", "true_person", "predicted_person", "best_match",
        "similarity", "matched", "threshold", "clasificacion",
    ]
    _header_row(ws, 1, headers)
    alt = PatternFill("solid", fgColor=COLOR_ALT)
    for i, r in enumerate(results, start=2):
        clf  = _classify(r)
        vals = [
            r["photo"], r["true_person"], r["predicted_person"], r["best_match"],
            r["similarity"], r["matched"], r["threshold"], clf,
        ]
        for col, val in enumerate(vals, start=1):
            cell = ws.cell(row=i, column=col, value=val)
            if clf in CLF_COLORS:
                cell.fill = PatternFill("solid", fgColor=CLF_COLORS[clf])
            elif i % 2 == 0:
                cell.fill = alt
    _auto_width(ws)


def sheet_summary(
    wb: Workbook,
    results: list[dict],
    auc_val: float,
    eer_val: float,
    eer_thresh: float,
    n_genuine: int,
    n_impostor: int,
    threshold: float,
    augment: bool,
) -> None:
    ws = wb.create_sheet("Resumen Global")

    counts: dict[str, int] = defaultdict(int)
    for r in results:
        counts[_classify(r)] += 1

    tp = counts["TP"]; fp = counts["FP"]
    fn = counts["FN"]; tn = counts["TN"]
    total     = tp + fp + fn + tn
    precision = _pct(tp, tp + fp)
    recall    = _pct(tp, tp + fn)
    f1        = round(2 * precision * recall / (precision + recall), 4) if (precision + recall) else 0.0
    accuracy  = _pct(tp + tn, total)
    far_fixed = _pct(fp, fp + tn)
    frr_fixed = _pct(fn, fn + tp)

    ws.cell(row=1, column=1, value="Evaluación Offline — Resumen").font = Font(bold=True, size=13)
    ws.merge_cells("A1:C1")

    rows = [
        ("Configuración", ""),
        ("Umbral fijo", threshold),
        ("Augmentación", "Sí" if augment else "No"),
        ("Fotos probe evaluadas", total),
        ("Pares genuine/impostor", f"{n_genuine} / {n_impostor}"),
        ("", ""),
        ("Métricas (umbral fijo)", ""),
        ("TP",        tp),
        ("FP",        fp),
        ("FN",        fn),
        ("TN",        tn),
        ("Precisión", precision),
        ("Recall",    recall),
        ("F1-Score",  f1),
        ("Accuracy",  accuracy),
        ("FAR",       far_fixed),
        ("FRR",       frr_fixed),
        ("", ""),
        ("Métricas ROC (pares genuine/impostor)", ""),
        ("AUC",               auc_val),
        ("EER",               eer_val),
        ("Umbral en EER",     eer_thresh),
    ]

    for i, (name, val) in enumerate(rows, start=3):
        if val == "" and name.startswith("Métricas"):
            ws.cell(row=i, column=1, value=name).font = Font(bold=True, color="1F4E79")
        elif name == "Configuración":
            ws.cell(row=i, column=1, value=name).font = Font(bold=True, color="1F4E79")
        else:
            ws.cell(row=i, column=1, value=name).font = Font(bold=True)
            ws.cell(row=i, column=2, value=val)

    _auto_width(ws)


def sheet_per_person(wb: Workbook, results: list[dict]) -> None:
    ws = wb.create_sheet("Por Persona")
    headers = [
        "Persona", "Fotos probe", "TP", "FP", "FN",
        "Precisión", "Recall", "F1-Score", "Sim. media TP",
    ]
    _header_row(ws, 1, headers)

    by:   dict[str, dict]  = defaultdict(lambda: defaultdict(int))
    sims: dict[str, list]  = defaultdict(list)
    for r in results:
        clf    = _classify(r)
        person = r["true_person"]
        by[person]["total"] += 1
        if clf:
            by[person][clf] += 1
        if clf == "TP":
            sims[person].append(r["similarity"])

    alt = PatternFill("solid", fgColor=COLOR_ALT)
    for i, person in enumerate(sorted(by), start=2):
        d    = by[person]
        tp   = d["TP"];  fp = d["FP"];  fn = d["FN"]
        prec = _pct(tp, tp + fp)
        rec  = _pct(tp, tp + fn)
        f1   = round(2 * prec * rec / (prec + rec), 4) if (prec + rec) else 0.0
        avg  = round(float(np.mean(sims[person])), 4) if sims[person] else 0.0
        vals = [person, d["total"], tp, fp, fn, prec, rec, f1, avg]
        for col, val in enumerate(vals, start=1):
            cell = ws.cell(row=i, column=col, value=val)
            if i % 2 == 0:
                cell.fill = alt

    _auto_width(ws)

    # Gráfica recall por persona (top 20)
    n_rows = min(20, len(by))
    if n_rows >= 2:
        bar = BarChart()
        bar.type      = "col"
        bar.grouping  = "clustered"
        bar.title     = "Recall por persona (top 20)"
        bar.y_axis.title = "Recall"
        bar.y_axis.scaling.min = 0
        bar.y_axis.scaling.max = 1.0
        bar.add_data(Reference(ws, min_col=7, min_row=1, max_row=1 + n_rows), titles_from_data=True)
        bar.set_categories(Reference(ws, min_col=1, min_row=2, max_row=1 + n_rows))
        bar.series[0].graphicalProperties.solidFill = COLOR_BLUE
        bar.width  = 20
        bar.height = 14
        ws.add_chart(bar, "K2")


def sheet_distributions(wb: Workbook, pairs: list[dict]) -> None:
    """
    Tabla de similitudes para pares genuine e impostor.
    Con muchos pares se samplea aleatoriamente para no saturar el Excel.
    """
    ws = wb.create_sheet("Distribución Similitudes")

    genuine   = [p for p in pairs if p["label"] == 1]
    impostor  = [p for p in pairs if p["label"] == 0]
    MAX_ROWS  = 5000

    # Samplear si hay demasiados impostores
    if len(impostor) > MAX_ROWS:
        rng      = random.Random(42)
        impostor = rng.sample(impostor, MAX_ROWS)

    all_pairs = genuine + impostor
    random.Random(42).shuffle(all_pairs)

    headers = ["Tipo", "Similitud", "true_person"]
    _header_row(ws, 1, headers)

    fill_g = PatternFill("solid", fgColor="C6EFCE")
    fill_i = PatternFill("solid", fgColor="FFC7CE")

    for i, p in enumerate(all_pairs, start=2):
        label = "Genuine" if p["label"] == 1 else "Impostor"
        ws.cell(row=i, column=1, value=label)
        ws.cell(row=i, column=2, value=round(p["similarity"], 4))
        ws.cell(row=i, column=3, value=p["true_person"])
        fill = fill_g if p["label"] == 1 else fill_i
        for col in range(1, 4):
            ws.cell(row=i, column=col).fill = fill

    _auto_width(ws)

    # Nota: usa Excel → Insertar gráfico de histograma para visualizar esta hoja


def sheet_roc(
    wb: Workbook,
    roc: list[dict],
    auc_val: float,
    eer_val: float,
    eer_thresh: float,
) -> None:
    ws = wb.create_sheet("Curva ROC")

    # Resumen en cabecera
    ws.cell(row=1, column=1, value=f"AUC = {auc_val}").font = Font(bold=True, size=12)
    ws.cell(row=1, column=4, value=f"EER = {eer_val}  (umbral = {eer_thresh})").font = Font(bold=True, size=12)

    headers = ["Umbral", "TPR", "FPR", "FAR", "FRR", "TP", "FP", "FN", "TN"]
    _header_row(ws, 2, headers)

    alt = PatternFill("solid", fgColor=COLOR_ALT)
    for i, pt in enumerate(roc, start=3):
        vals = [
            pt["threshold"], pt["TPR"], pt["FPR"],
            pt["FAR"], pt["FRR"],
            pt["TP"], pt["FP"], pt["FN"], pt["TN"],
        ]
        for col, val in enumerate(vals, start=1):
            cell = ws.cell(row=i, column=col, value=val)
            if i % 2 == 0:
                cell.fill = alt

    _auto_width(ws)
    last = 2 + len(roc)

    # ── Gráfica ROC (FPR vs TPR) ──────────────────────────────────────────────
    ch_roc = ScatterChart()
    ch_roc.scatterStyle         = "lineMarker"
    ch_roc.title                = f"Curva ROC — AUC = {auc_val}"
    ch_roc.style                = 10
    ch_roc.x_axis.title         = "FPR (False Positive Rate)"
    ch_roc.y_axis.title         = "TPR (True Positive Rate / Recall)"
    ch_roc.x_axis.scaling.min   = 0;  ch_roc.x_axis.scaling.max = 1
    ch_roc.y_axis.scaling.min   = 0;  ch_roc.y_axis.scaling.max = 1

    s = Series(
        Reference(ws, min_col=2, min_row=3, max_row=last),
        Reference(ws, min_col=3, min_row=3, max_row=last),
        title="ROC",
    )
    s.graphicalProperties.line.solidFill = COLOR_BLUE
    s.graphicalProperties.line.width     = 20000
    ch_roc.series.append(s)
    ch_roc.width = 18;  ch_roc.height = 16
    ws.add_chart(ch_roc, "K2")

    # ── Gráfica FAR / FRR vs umbral ───────────────────────────────────────────
    ch_det = ScatterChart()
    ch_det.scatterStyle         = "lineMarker"
    ch_det.title                = f"FAR / FRR vs Umbral — EER = {eer_val} (umbral = {eer_thresh})"
    ch_det.style                = 10
    ch_det.x_axis.title         = "Umbral de similitud coseno"
    ch_det.y_axis.title         = "Tasa de error"
    ch_det.x_axis.scaling.min   = 0;  ch_det.x_axis.scaling.max = 1
    ch_det.y_axis.scaling.min   = 0

    thresh_ref = Reference(ws, min_col=1, min_row=3, max_row=last)
    for col_idx, lbl, color in [
        (4, "FAR (False Acceptance Rate)", "FF0000"),
        (5, "FRR (False Rejection Rate)",  "0070C0"),
    ]:
        s2 = Series(
            Reference(ws, min_col=col_idx, min_row=3, max_row=last),
            thresh_ref,
            title=lbl,
        )
        s2.graphicalProperties.line.solidFill = color
        s2.graphicalProperties.line.width     = 18000
        ch_det.series.append(s2)

    ch_det.width = 18;  ch_det.height = 16
    ws.add_chart(ch_det, "K26")


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluación offline del reconocimiento facial con InsightFace buffalo_l",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    # Datos
    data_group = parser.add_mutually_exclusive_group(required=True)
    data_group.add_argument(
        "--data-dir", type=Path,
        help="Directorio con fotos organizadas por persona (person_name/foto.jpg)",
    )
    data_group.add_argument(
        "--download-lfw", type=Path, metavar="DEST_DIR",
        help="Descarga LFW en DEST_DIR (sin TensorFlow) y lo usa como --data-dir",
    )

    # Salida
    parser.add_argument("--output", type=Path, required=True,
                        help="Ruta de salida del Excel (.xlsx)")

    # Split
    parser.add_argument("--enroll-ratio", type=float, default=0.5,
                        help="Fracción de fotos para enrollment (default: 0.5 = 50%%)")
    parser.add_argument("--min-photos", type=int, default=6,
                        help="Mínimo de fotos por persona para incluirla (default: 6)")
    parser.add_argument("--max-people", type=int, default=None,
                        help="Máximo de personas a usar (default: todas)")

    # Evaluación
    parser.add_argument("--threshold", type=float, default=0.30,
                        help="Umbral de similitud fijo para métricas TP/FP (default: 0.30)")

    # Augmentación
    parser.add_argument("--augment", action="store_true",
                        help="Aplicar augmentación al set de enrollment")
    parser.add_argument("--aug-per-image", type=int, default=10,
                        help="Imágenes aumentadas por foto de enrollment (default: 10)")

    # Reproducibilidad
    parser.add_argument("--seed", type=int, default=42,
                        help="Semilla aleatoria para el split (default: 42)")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # ── Preparar datos ────────────────────────────────────────────────────────
    if args.download_lfw:
        data_dir = args.download_lfw
        logger.info("Modo --download-lfw: descargando LFW si no existe ...")
        download_lfw(
            dest        = data_dir,
            max_people  = args.max_people or 100,
            min_photos  = args.min_photos,
        )
    else:
        data_dir = args.data_dir

    logger.info(f"Cargando datos desde: {data_dir}")
    data = load_data(data_dir, args.min_photos, args.max_people)
    if not data:
        logger.error(
            f"No se encontraron personas con >= {args.min_photos} fotos en {data_dir}"
        )
        sys.exit(1)

    total_photos = sum(len(v) for v in data.values())
    logger.info(f"  → {len(data)} personas | {total_photos} fotos totales")

    gallery_data, probe_data = split_data(data, args.enroll_ratio, args.seed)
    n_gallery = sum(len(v) for v in gallery_data.values())
    n_probe   = sum(len(v) for v in probe_data.values())
    logger.info(f"  → Enrollment: {n_gallery} fotos | Probe: {n_probe} fotos")

    # ── Modelo InsightFace ────────────────────────────────────────────────────
    logger.info("Inicializando InsightFace buffalo_l ...")
    app = build_face_app()

    # ── Gallery ───────────────────────────────────────────────────────────────
    aug_label = "con augmentación" if args.augment else "sin augmentación"
    logger.info(f"Construyendo gallery embeddings ({aug_label}) ...")
    gallery_embs = build_gallery(app, gallery_data, args.augment, args.aug_per_image)
    logger.info(f"  → {len(gallery_embs)} personas con embedding válido")

    if len(gallery_embs) < 2:
        logger.error("Se necesitan >= 2 personas en el gallery para generar pares impostor.")
        sys.exit(1)

    # ── Probe ─────────────────────────────────────────────────────────────────
    logger.info("Evaluando probe ...")
    results = run_probe(app, probe_data, gallery_embs, args.threshold)
    logger.info(f"  → {len(results)} fotos probe procesadas")

    # ── ROC con pares genuine/impostor ────────────────────────────────────────
    logger.info("Calculando pares genuine/impostor y curva ROC ...")
    pairs      = build_pairs(results)
    n_genuine  = sum(1 for p in pairs if p["label"] == 1)
    n_impostor = sum(1 for p in pairs if p["label"] == 0)
    roc        = compute_roc(pairs)
    auc_val    = compute_auc(roc)
    eer_val, eer_thresh = compute_eer(roc)

    logger.info(f"  → {n_genuine} pares genuine | {n_impostor} pares impostor")
    logger.info(f"  → AUC = {auc_val} | EER = {eer_val} (umbral = {eer_thresh})")

    # ── Excel ─────────────────────────────────────────────────────────────────
    logger.info("Generando Excel ...")
    wb = Workbook()
    del wb["Sheet"]

    sheet_raw(wb, results)
    sheet_summary(
        wb, results, auc_val, eer_val, eer_thresh,
        n_genuine, n_impostor, args.threshold, args.augment,
    )
    sheet_per_person(wb, results)
    sheet_distributions(wb, pairs)
    sheet_roc(wb, roc, auc_val, eer_val, eer_thresh)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(args.output)
    logger.info(f"Excel guardado: {args.output}")


if __name__ == "__main__":
    main()
