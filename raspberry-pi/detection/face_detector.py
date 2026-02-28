"""
Wrapper para detección de rostros usando RetinaFace (implementado vía InsightFace).

RetinaFace es un detector de rostros de una sola etapa que proporciona:
- Detección de bounding boxes
- Localización de landmarks (5 puntos)
- Score de confianza

Métricas oficiales: WIDER FACE hard test set - AP 91.4%
Paper: arXiv:1905.00641 (CVPR 2020)
"""
import cv2
import numpy as np
from typing import List, Tuple, Optional
import logging

try:
    from insightface.app import FaceAnalysis
    INSIGHTFACE_AVAILABLE = True
except ImportError:
    INSIGHTFACE_AVAILABLE = False
    logging.warning("InsightFace no está disponible. Instala con: pip install insightface")

from config import RETINAFACE_MODEL_NAME, RETINAFACE_DET_SIZE, FACE_DETECTION_CONFIDENCE

logger = logging.getLogger(__name__)


class FaceDetection:
    """Bounding box de una detección de rostro."""
    def __init__(
        self,
        bbox: np.ndarray,
        landmarks: Optional[np.ndarray] = None,
        confidence: float = 1.0,
        embedding: Optional[np.ndarray] = None,
    ):
        """
        Args:
            bbox: Array [x1, y1, x2, y2] con coordenadas del bounding box
            landmarks: Array [N, 2] con coordenadas de landmarks (5 puntos para RetinaFace)
            confidence: Score de confianza de la detección
            embedding: Embedding L2-normalizado (de InsightFace) si disponible
        """
        self.bbox = bbox.astype(int)  # [x1, y1, x2, y2]
        self.landmarks = landmarks  # [5, 2] o None
        self.confidence = float(confidence)
        self.embedding = embedding  # De InsightFace normed_embedding cuando disponible
        
    @property
    def x1(self) -> int:
        return int(self.bbox[0])
    
    @property
    def y1(self) -> int:
        return int(self.bbox[1])
    
    @property
    def x2(self) -> int:
        return int(self.bbox[2])
    
    @property
    def y2(self) -> int:
        return int(self.bbox[3])
    
    @property
    def width(self) -> int:
        return self.x2 - self.x1
    
    @property
    def height(self) -> int:
        return self.y2 - self.y1
    
    def get_face_crop(self, frame: np.ndarray) -> np.ndarray:
        """Extrae el crop del rostro del frame."""
        h, w = frame.shape[:2]
        x1 = max(0, self.x1)
        y1 = max(0, self.y1)
        x2 = min(w, self.x2)
        y2 = min(h, self.y2)
        return frame[y1:y2, x1:x2]


class RetinaFaceDetector:
    """
    Detector de rostros usando RetinaFace (vía InsightFace).
    
    RetinaFace proporciona detección de alta precisión con landmarks de 5 puntos.
    """
    
    def __init__(self, model_name: str = RETINAFACE_MODEL_NAME, det_size: Tuple[int, int] = RETINAFACE_DET_SIZE):
        """
        Inicializa el detector RetinaFace.
        
        Args:
            model_name: Nombre del modelo InsightFace (por defecto 'buffalo_s' que incluye RetinaFace)
            det_size: Tamaño de detección (width, height). Menor tamaño = más rápido pero menos preciso
        """
        if not INSIGHTFACE_AVAILABLE:
            raise ImportError(
                "InsightFace no está instalado. "
                "Instala con: pip install insightface onnxruntime"
            )
        
        self.model_name = model_name
        self.det_size = det_size
        self.app = None
        self._initialized = False
        
    def initialize(self, ctx_id: int = 0):
        """
        Inicializa el modelo de detección.
        
        Args:
            ctx_id: ID del contexto (0 para CPU, -1 para GPU si está disponible)
        """
        if self._initialized:
            return
        
        logger.info(f"Inicializando RetinaFace detector (modelo: {self.model_name}, det_size: {self.det_size})")
        
        try:
            self.app = FaceAnalysis(
                name=self.model_name,
                providers=["CPUExecutionProvider"] if ctx_id == 0 else ["CUDAExecutionProvider", "CPUExecutionProvider"]
            )
            self.app.prepare(ctx_id=ctx_id, det_size=self.det_size)
            self._initialized = True
            logger.info("RetinaFace detector inicializado correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar RetinaFace: {e}")
            raise
    
    def detect_faces(self, frame: np.ndarray, min_confidence: float = FACE_DETECTION_CONFIDENCE) -> List[FaceDetection]:
        """
        Detecta rostros en un frame.
        
        Args:
            frame: Frame BGR de OpenCV (numpy array)
            min_confidence: Umbral mínimo de confianza para filtrar detecciones
            
        Returns:
            Lista de objetos FaceDetection
        """
        if not self._initialized:
            self.initialize()
        
        if frame is None or frame.size == 0:
            return []
        
        # InsightFace espera RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        try:
            # Detectar rostros
            faces = self.app.get(frame_rgb)
            
            detections = []
            for face in faces:
                # Filtrar por confianza
                if face.det_score < min_confidence:
                    continue
                
                # RetinaFace proporciona bbox como [x1, y1, x2, y2]
                bbox = face.bbox[:4]  # [x1, y1, x2, y2]
                
                # Landmarks (5 puntos: ojos, nariz, comisuras)
                landmarks = None
                if hasattr(face, 'kps') and face.kps is not None:
                    landmarks = face.kps.astype(np.float32)  # [5, 2]
                
                # Embedding de InsightFace (MBF/MobileFaceNet) si disponible
                embedding = None
                if hasattr(face, 'normed_embedding') and face.normed_embedding is not None:
                    embedding = np.asarray(face.normed_embedding)
                
                detection = FaceDetection(
                    bbox=bbox,
                    landmarks=landmarks,
                    confidence=float(face.det_score),
                    embedding=embedding,
                )
                detections.append(detection)
            
            return detections
            
        except Exception as e:
            logger.error(f"Error durante la detección: {e}")
            return []
    
    def extract_embedding_from_face(self, face_image_rgb: np.ndarray) -> Optional[np.ndarray]:
        """
        Extrae embedding de una imagen de rostro (crop) usando InsightFace.
        Útil para imágenes aumentadas en build_database.
        
        Args:
            face_image_rgb: Imagen del rostro en RGB (H, W, 3)
            
        Returns:
            Embedding L2-normalizado o None si no se detecta rostro
        """
        if not self._initialized:
            self.initialize()
        try:
            faces = self.app.get(face_image_rgb)
            if not faces:
                return None
            face = faces[0]
            if hasattr(face, 'normed_embedding') and face.normed_embedding is not None:
                return np.asarray(face.normed_embedding)
            return None
        except Exception:
            return None

    def detect_largest_face(self, frame: np.ndarray, min_confidence: float = FACE_DETECTION_CONFIDENCE) -> Optional[FaceDetection]:
        """
        Detecta el rostro más grande en el frame.
        
        Args:
            frame: Frame BGR de OpenCV
            min_confidence: Umbral mínimo de confianza
            
        Returns:
            FaceDetection del rostro más grande o None
        """
        detections = self.detect_faces(frame, min_confidence)
        
        if not detections:
            return None
        
        # Encontrar el más grande por área
        largest = max(detections, key=lambda d: d.width * d.height)
        return largest
    
    def __del__(self):
        """Cleanup al destruir el objeto."""
        self.app = None
