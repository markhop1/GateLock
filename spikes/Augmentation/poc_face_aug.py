import os
import glob
import argparse
import numpy as np
from PIL import Image
from tqdm import tqdm

import torch
import torch.nn.functional as F
from facenet_pytorch import MTCNN, InceptionResnetV1

import albumentations as A
import cv2
from sklearn.metrics.pairwise import cosine_similarity


def l2_normalize(x: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    return x / (np.linalg.norm(x) + eps)



def build_augmenter():
    # Aumentaciones centradas en iluminación + degradaciones realistas moderadas
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
    Gate muy simple: evita caras demasiado oscuras o demasiado quemadas.
    face_rgb: HxWx3 uint8
    """
    gray = cv2.cvtColor(face_rgb, cv2.COLOR_RGB2GRAY)
    mean = float(gray.mean())
    # % de píxeles casi negros / casi blancos
    near_black = float((gray < 10).mean())
    near_white = float((gray > 245).mean())

    if mean < 35 or mean > 220:
        return False
    if near_black > 0.25:
        return False
    if near_white > 0.25:
        return False
    return True


@torch.no_grad()
def embed_face_tensor(resnet, face_tensor: torch.Tensor, device: str) -> np.ndarray:
    """
    face_tensor: (1,3,160,160) float
    """
    face_tensor = face_tensor.to(device)
    emb = resnet(face_tensor)  # (1,512)
    emb = F.normalize(emb, p=2, dim=1)
    return emb.squeeze(0).detach().cpu().numpy()


def list_identities(root_dir: str):
    identities = []
    for d in sorted(os.listdir(root_dir)):
        p = os.path.join(root_dir, d)
        if os.path.isdir(p):
            identities.append(d)
    return identities


def list_images_for_identity(root_dir: str, identity: str):
    exts = ("*.jpg", "*.jpeg", "*.png", "*.webp", "*.bmp")
    files = []
    for e in exts:
        files.extend(glob.glob(os.path.join(root_dir, identity, e)))
    return sorted(files)


def pil_to_rgb_np(pil_img: Image.Image) -> np.ndarray:
    return np.array(pil_img.convert("RGB"))


def rgb_np_to_pil(rgb: np.ndarray) -> Image.Image:
    return Image.fromarray(rgb.astype(np.uint8), mode="RGB")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, required=True, help="Carpeta con subcarpetas por persona")
    parser.add_argument("--aug_per_image", type=int, default=20, help="Aumentaciones por imagen")
    parser.add_argument("--max_images_per_id", type=int, default=10, help="Máx imágenes base por identidad")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    device = args.device
    print(f"Device: {device}")

    # 1) Detector/aligner de cara
    mtcnn = MTCNN(
        image_size=160,
        margin=14,
        min_face_size=40,
        thresholds=[0.6, 0.7, 0.7],
        post_process=True,  # normaliza a [-1,1] para FaceNet
        device=device,
        keep_all=False,
    )

    # 2) Modelo de embedding (FaceNet-like)
    resnet = InceptionResnetV1(pretrained="vggface2").eval().to(device)

    aug = build_augmenter()

    identities = list_identities(args.data_dir)
    if not identities:
        raise RuntimeError("No se encontraron subcarpetas de identidad dentro de data_dir.")

    per_id_agg = {}         # identity -> embedding agregado (512,)
    per_id_embs = {}        # identity -> lista de embeddings individuales (para análisis)
    per_id_used = {}        # identity -> contadores

    # === Extracción + aumentación + embeddings ===
    for ident in tqdm(identities, desc="Procesando identidades"):
        img_files = list_images_for_identity(args.data_dir, ident)[: args.max_images_per_id]
        if not img_files:
            continue

        collected = []
        used_faces = 0
        skipped = 0

        for fpath in img_files:
            try:
                pil = Image.open(fpath).convert("RGB")
            except Exception:
                skipped += 1
                continue

            # Detecta y devuelve cara alineada como tensor (1,3,160,160) o None
            face_tensor = mtcnn(pil)
            if face_tensor is None:
                skipped += 1
                continue

            # Embedding de la original
            orig_emb = embed_face_tensor(resnet, face_tensor.unsqueeze(0), device)
            collected.append(orig_emb)
            used_faces += 1

            # Para aumentaciones: aplicamos aug sobre la imagen original (RGB),
            # luego volvemos a detectar/recortar cara. Esto simula el pipeline real.
            base_rgb = pil_to_rgb_np(pil)

            for _ in range(args.aug_per_image):
                aug_rgb = aug(image=base_rgb)["image"]

                if not quality_gate(aug_rgb):
                    continue

                aug_pil = rgb_np_to_pil(aug_rgb)
                aug_face_tensor = mtcnn(aug_pil)
                if aug_face_tensor is None:
                    continue

                aug_emb = embed_face_tensor(resnet, aug_face_tensor.unsqueeze(0), device)
                collected.append(aug_emb)

        if len(collected) == 0:
            continue

        # Agregado: media + L2
        mat = np.stack(collected, axis=0)  # (K,512)
        agg = mat.mean(axis=0)
        agg = l2_normalize(agg)

        per_id_agg[ident] = agg
        per_id_embs[ident] = mat
        per_id_used[ident] = {"base_images": len(img_files), "faces_used": used_faces, "skipped": skipped, "total_embs": len(collected)}

    # === Evaluación mínima: intra vs inter ===
    id_list = sorted(per_id_embs.keys())
    if len(id_list) < 2:
        print("Necesitas al menos 2 identidades con embeddings para evaluar.")
        return

    intra_sims = []
    inter_sims = []

    # Intra: similitudes dentro de la misma identidad (entre embeddings individuales)
    for ident in id_list:
        embs = per_id_embs[ident]
        if embs.shape[0] < 2:
            continue
        sims = cosine_similarity(embs, embs)
        # coge la parte superior sin diagonal
        iu = np.triu_indices_from(sims, k=1)
        intra_sims.extend(sims[iu].tolist())

    # Inter: similitud entre agregados de distintas identidades
    agg_mat = np.stack([per_id_agg[i] for i in id_list], axis=0)
    sims_agg = cosine_similarity(agg_mat, agg_mat)
    iu = np.triu_indices_from(sims_agg, k=1)
    inter_sims = sims_agg[iu].tolist()

    def summarize(x):
        if len(x) == 0:
            return {"n": 0}
        x = np.array(x, dtype=float)
        return {
            "n": int(x.size),
            "mean": float(x.mean()),
            "p05": float(np.quantile(x, 0.05)),
            "p50": float(np.quantile(x, 0.50)),
            "p95": float(np.quantile(x, 0.95)),
        }

    print("\n=== Resumen por identidad ===")
    for ident in id_list[:20]:
        print(f"{ident}: {per_id_used[ident]}")

    print("\n=== Métricas (similitud coseno) ===")
    print("INTRA (misma persona, pares entre embeddings individuales):", summarize(intra_sims))
    print("INTER (distinta persona, pares entre embeddings agregados):", summarize(inter_sims))

    # Un umbral “naive” sugerido: punto medio entre medianas intra/inter (solo orientativo)
    if len(intra_sims) and len(inter_sims):
        thr = 0.5 * (np.median(intra_sims) + np.median(inter_sims))
        print(f"\nUmbral orientativo (no calibrado): {thr:.3f}")

    # Guardar embeddings agregados
    out_path = os.path.join(args.data_dir, "embeddings_agg.npy")
    np.save(out_path, {"ids": id_list, "embeddings": np.stack([per_id_agg[i] for i in id_list])})
    print(f"\nGuardado: {out_path}")


if __name__ == "__main__":
    main()
