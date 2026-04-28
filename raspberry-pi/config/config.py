"""
Configuración centralizada para el sistema de reconocimiento facial.
"""
import os
from pathlib import Path
from typing import Optional

# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar .env si existe
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

# Configuración de API
API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:5000/api")
API_USERNAME: Optional[str] = os.getenv("API_USERNAME", None)
API_PASSWORD: Optional[str] = os.getenv("API_PASSWORD", None)
API_TIMEOUT_SECONDS: int = int(os.getenv("API_TIMEOUT_SECONDS", "30"))

# Configuración de cámara
CAMERA_INDEX: int = int(os.getenv("CAMERA_INDEX", "0"))

# Configuración de reconocimiento
RECOGNITION_THRESHOLD: float = float(os.getenv("RECOGNITION_THRESHOLD", "0.35"))
FACE_DETECTION_CONFIDENCE: float = float(os.getenv("FACE_DETECTION_CONFIDENCE", "0.5"))

# Configuración de video
CLIP_DURATION_SECONDS: int = int(os.getenv("CLIP_DURATION_SECONDS", "10"))
VIDEO_OUTPUT_DIR: Path = Path(os.getenv("VIDEO_OUTPUT_DIR", str(BASE_DIR / "videos")))
VIDEO_FPS: int = int(os.getenv("VIDEO_FPS", "30"))
VIDEO_BUFFER_SECONDS: int = int(os.getenv("VIDEO_BUFFER_SECONDS", "5"))  # Segundos antes de la detección

# Configuración de base de datos
DATABASE_DIR: Path = Path(os.getenv("DATABASE_DIR", str(BASE_DIR / "database")))
KNOWN_FACES_DIR: Path = Path(os.getenv("KNOWN_FACES_DIR", str(BASE_DIR / "known_faces")))
EMBEDDINGS_FILE: Path = DATABASE_DIR / "face_embeddings.npy"
LABELS_FILE: Path = DATABASE_DIR / "face_labels.npy"

# Configuración de augmentación
AUG_PER_IMAGE: int = int(os.getenv("AUG_PER_IMAGE", "20"))
MAX_IMAGES_PER_ID: int = int(os.getenv("MAX_IMAGES_PER_ID", "10"))

# Configuración de modelos
# RetinaFace (detección) - usando InsightFace
RETINAFACE_MODEL_NAME: str = os.getenv("RETINAFACE_MODEL_NAME", "buffalo_l")
RETINAFACE_DET_SIZE: tuple = tuple(map(int, os.getenv("RETINAFACE_DET_SIZE", "640,640").split(",")))

# MobileFaceNet (reconocimiento) - usando TensorFlow/Keras
MOBILEFACENET_MODEL_PATH: Optional[str] = os.getenv("MOBILEFACENET_MODEL_PATH", None)
MOBILEFACENET_INPUT_SIZE: tuple = (112, 112)  # Tamaño estándar de entrada para MobileFaceNet

# Configuración de logging
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE: Optional[Path] = Path(os.getenv("LOG_FILE", str(BASE_DIR / "logs" / "gatelock.log"))) if os.getenv("LOG_FILE") else None

# Configuración de autenticación
TOKEN_CACHE_DIR: Path = Path.home() / ".gatelock"
TOKEN_CACHE_FILE: Path = TOKEN_CACHE_DIR / "token.json"

# Rate limiting para alertas (evitar múltiples alertas de la misma persona)
ALERT_COOLDOWN_SECONDS: int = int(os.getenv("ALERT_COOLDOWN_SECONDS", "60"))

# Crear directorios necesarios
VIDEO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_DIR.mkdir(parents=True, exist_ok=True)
KNOWN_FACES_DIR.mkdir(parents=True, exist_ok=True)
TOKEN_CACHE_DIR.mkdir(parents=True, exist_ok=True)
if LOG_FILE:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
