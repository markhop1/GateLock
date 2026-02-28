"""
Reconocimiento facial usando MobileFaceNet (TensorFlow/Keras).

MobileFaceNet es un modelo ligero optimizado para dispositivos móviles y embebidos.
Métricas oficiales: LFW 99.55% accuracy, MegaFace 92.59% TAR@FAR1e-6
Paper: arXiv:1804.07573 (CCBR 2018)
"""
from __future__ import annotations

import numpy as np
import cv2
import logging
from typing import Optional, Tuple
from pathlib import Path

try:
    import tensorflow as tf
    from tensorflow import keras
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logging.warning("TensorFlow no está disponible. Instala con: pip install tensorflow")

from config import MOBILEFACENET_MODEL_PATH, MOBILEFACENET_INPUT_SIZE
from detection.face_detector import FaceDetection

logger = logging.getLogger(__name__)


class MobileFaceNetRecognizer:
    """
    Reconocedor facial usando MobileFaceNet.
    
    Extrae embeddings de 128 dimensiones (o según el modelo) de rostros detectados.
    """
    
    def __init__(self, model_path: Optional[str] = MOBILEFACENET_MODEL_PATH, input_size: Tuple[int, int] = MOBILEFACENET_INPUT_SIZE):
        """
        Inicializa el reconocedor MobileFaceNet.
        
        Args:
            model_path: Ruta al modelo pre-entrenado (.h5, .pb, o directorio SavedModel)
                       Si es None, intentará cargar un modelo por defecto o crear uno básico
            input_size: Tamaño de entrada del modelo (height, width). Por defecto (112, 112)
        """
        if not TENSORFLOW_AVAILABLE:
            raise ImportError(
                "TensorFlow no está instalado. "
                "Instala con: pip install tensorflow"
            )
        
        self.model_path = Path(model_path) if model_path else None
        self.input_size = input_size
        self.model: Optional[keras.Model] = None
        self.embedding_size = 128  # Tamaño estándar de embedding de MobileFaceNet
        self._initialized = False
    
    def initialize(self):
        """Inicializa el modelo MobileFaceNet."""
        if self._initialized:
            return
        
        logger.info(f"Inicializando MobileFaceNet (input_size: {self.input_size})")
        
        try:
            if self.model_path and self.model_path.exists():
                # Cargar modelo desde archivo
                logger.info(f"Cargando modelo desde: {self.model_path}")
                self.model = keras.models.load_model(str(self.model_path))
                # Obtener tamaño de embedding desde la última capa
                output_shape = self.model.output_shape
                if isinstance(output_shape, list):
                    output_shape = output_shape[0]
                if len(output_shape) > 1:
                    self.embedding_size = output_shape[-1]
                logger.info(f"Modelo cargado. Tamaño de embedding: {self.embedding_size}")
            else:
                # Crear modelo básico si no hay archivo
                logger.warning(
                    f"Modelo no encontrado en {self.model_path}. "
                    "Creando modelo básico. Para mejor rendimiento, proporciona un modelo pre-entrenado."
                )
                self.model = self._create_basic_model()
            
            self._initialized = True
            logger.info("MobileFaceNet inicializado correctamente")
            
        except Exception as e:
            logger.error(f"Error al inicializar MobileFaceNet: {e}")
            raise
    
    def _create_basic_model(self) -> keras.Model:
        """
        Crea un modelo básico de MobileFaceNet.
        
        Nota: Este es un modelo simplificado. Para producción, usa un modelo pre-entrenado.
        """
        # Arquitectura simplificada de MobileFaceNet
        inputs = keras.Input(shape=(*self.input_size, 3))
        
        # Bloque inicial
        x = keras.layers.Conv2D(64, 3, padding='same', use_bias=False)(inputs)
        x = keras.layers.BatchNormalization()(x)
        x = keras.layers.ReLU()(x)
        x = keras.layers.DepthwiseConv2D(3, padding='same', use_bias=False)(x)
        x = keras.layers.BatchNormalization()(x)
        x = keras.layers.ReLU()(x)
        x = keras.layers.Conv2D(64, 1, padding='same', use_bias=False)(x)
        x = keras.layers.BatchNormalization()(x)
        
        # Bloques móviles
        for filters in [128, 256, 512]:
            x = self._mobile_block(x, filters)
        
        # Global average pooling
        x = keras.layers.GlobalAveragePooling2D()(x)
        
        # Embedding layer
        x = keras.layers.Dense(self.embedding_size, use_bias=False)(x)
        x = keras.layers.BatchNormalization()(x)
        
        model = keras.Model(inputs=inputs, outputs=x)
        return model
    
    def _mobile_block(self, x, filters: int):
        """Bloque móvil de MobileFaceNet."""
        # Depthwise separable convolution
        x = keras.layers.DepthwiseConv2D(3, padding='same', use_bias=False)(x)
        x = keras.layers.BatchNormalization()(x)
        x = keras.layers.ReLU()(x)
        x = keras.layers.Conv2D(filters, 1, padding='same', use_bias=False)(x)
        x = keras.layers.BatchNormalization()(x)
        return x
    
    def extract_embedding(self, face_image: np.ndarray) -> np.ndarray:
        """
        Extrae embedding de una imagen de rostro.
        
        Args:
            face_image: Imagen del rostro en RGB (H, W, 3) o BGR
            
        Returns:
            Embedding normalizado (L2) de shape [embedding_size]
        """
        if not self._initialized:
            self.initialize()
        
        # Preprocesar imagen
        processed = self._preprocess_face(face_image)
        
        # Extraer embedding
        embedding = self.model.predict(processed, verbose=0)
        embedding = embedding.flatten()
        
        # Normalizar L2
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding
    
    def _preprocess_face(self, face_image: np.ndarray) -> np.ndarray:
        """
        Preprocesa una imagen de rostro para el modelo.
        
        Args:
            face_image: Imagen RGB o BGR
            
        Returns:
            Imagen preprocesada lista para el modelo
        """
        # Convertir BGR a RGB si es necesario
        if len(face_image.shape) == 3 and face_image.shape[2] == 3:
            # Asumir BGR si los valores están en rango [0, 255]
            if face_image.dtype == np.uint8:
                face_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
        
        # Redimensionar a tamaño de entrada
        face_resized = cv2.resize(face_image, (self.input_size[1], self.input_size[0]))
        
        # Normalizar a [-1, 1] o [0, 1] según el modelo
        # MobileFaceNet típicamente usa normalización a [-1, 1]
        face_normalized = (face_resized.astype(np.float32) / 127.5) - 1.0
        
        # Agregar dimensión de batch
        face_batch = np.expand_dims(face_normalized, axis=0)
        
        return face_batch
    
    def recognize_face(self, face_detection: FaceDetection, frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Reconoce un rostro detectado extrayendo su embedding.
        
        Prefiere el embedding de InsightFace si la detección lo incluye (más preciso).
        Si no, usa MobileFaceNet (requiere modelo pre-entrenado para que sea útil).
        
        Args:
            face_detection: Objeto FaceDetection con la detección
            frame: Frame completo en BGR
            
        Returns:
            Tupla (face_crop, embedding) donde:
            - face_crop: Imagen recortada del rostro
            - embedding: Embedding normalizado del rostro
        """
        # Extraer crop del rostro
        face_crop = face_detection.get_face_crop(frame)
        
        if face_crop.size == 0:
            return face_crop, np.zeros(self.embedding_size)
        
        # Usar embedding de InsightFace si está disponible (MBF pre-entrenado)
        if getattr(face_detection, 'embedding', None) is not None:
            emb = np.asarray(face_detection.embedding).flatten()
            if len(emb) > 0:
                return face_crop, emb
        
        # Fallback a MobileFaceNet (requiere modelo pre-entrenado)
        face_rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
        embedding = self.extract_embedding(face_rgb)
        
        return face_crop, embedding
    
    def get_embedding_size(self) -> int:
        """Retorna el tamaño del embedding."""
        if not self._initialized:
            self.initialize()
        return self.embedding_size
    
    def __del__(self):
        """Cleanup al destruir el objeto."""
        self.model = None
