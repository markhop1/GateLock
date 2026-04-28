"""
Gestión de base de datos de embeddings faciales.

Maneja la carga, almacenamiento y búsqueda de embeddings normalizados.
"""
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, List
import logging

from config import EMBEDDINGS_FILE, LABELS_FILE

logger = logging.getLogger(__name__)


class FaceDatabase:
    """
    Base de datos de embeddings faciales.
    
    Almacena embeddings normalizados (L2) y permite búsqueda por similitud coseno.
    """
    
    def __init__(self, embeddings_file: Path = EMBEDDINGS_FILE, labels_file: Path = LABELS_FILE):
        """
        Inicializa la base de datos.
        
        Args:
            embeddings_file: Ruta al archivo .npy con embeddings (shape: [N, D])
            labels_file: Ruta al archivo .npy con labels (shape: [N])
        """
        self.embeddings_file = Path(embeddings_file)
        self.labels_file = Path(labels_file)
        self.embeddings: Optional[np.ndarray] = None  # [N, D] normalizados
        self.labels: Optional[np.ndarray] = None  # [N] con nombres
        self._loaded = False
    
    def load(self) -> bool:
        """
        Carga embeddings y labels desde archivos.
        
        Returns:
            True si se cargaron correctamente, False en caso contrario
        """
        if self._loaded:
            return True
        
        if not self.embeddings_file.exists() or not self.labels_file.exists():
            logger.warning(
                f"Archivos de base de datos no encontrados:\n"
                f"  {self.embeddings_file}\n"
                f"  {self.labels_file}\n"
                f"Ejecuta build_database.py primero."
            )
            return False
        
        try:
            # Cargar embeddings y labels
            self.embeddings = np.load(self.embeddings_file)
            self.labels = np.load(self.labels_file)
            
            # Validar formato
            if self.embeddings.ndim != 2:
                raise ValueError(f"Embeddings deben tener shape (N, D), pero tienen {self.embeddings.shape}")
            
            if len(self.labels) != len(self.embeddings):
                raise ValueError(
                    f"Número de labels ({len(self.labels)}) no coincide con embeddings ({len(self.embeddings)})"
                )
            
            # Normalizar embeddings (L2)
            norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1.0  # Evitar división por cero
            self.embeddings = self.embeddings / norms
            
            self._loaded = True
            logger.info(f"Base de datos cargada: {len(self.embeddings)} embeddings de {len(np.unique(self.labels))} personas")
            return True
            
        except Exception as e:
            logger.error(f"Error al cargar base de datos: {e}")
            self.embeddings = None
            self.labels = None
            return False
    
    def find_match(
        self, 
        embedding: np.ndarray, 
        threshold: float = 0.5,
        top_k: int = 1
    ) -> Tuple[Optional[str], float]:
        """
        Busca la mejor coincidencia para un embedding.
        
        Args:
            embedding: Embedding a buscar (shape: [D] o [1, D])
            threshold: Umbral mínimo de similitud coseno
            top_k: Número de mejores coincidencias a considerar
            
        Returns:
            Tupla (nombre_persona, similitud) o (None, similitud) si no hay match
        """
        if not self._loaded:
            if not self.load():
                return None, 0.0
        
        if self.embeddings is None or len(self.embeddings) == 0:
            return None, 0.0
        
        # Normalizar embedding de entrada
        embedding = np.asarray(embedding).flatten()
        norm = np.linalg.norm(embedding)
        if norm == 0:
            return None, 0.0
        embedding = embedding / norm
        
        # Calcular similitud coseno (producto punto con embeddings normalizados)
        similarities = self.embeddings @ embedding  # [N]
        
        # Encontrar mejor match
        best_idx = int(np.argmax(similarities))
        best_sim = float(similarities[best_idx])

        logger.debug(
            "best_sim=%.4f (threshold=%.4f, label=%s, match=%s)",
            best_sim,
            threshold,
            self.labels[best_idx],
            best_sim >= threshold,
        )

        if best_sim < threshold:
            return None, best_sim
        
        person_name = str(self.labels[best_idx])
        return person_name, best_sim
    
    def find_matches(
        self,
        embedding: np.ndarray,
        threshold: float = 0.5,
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Busca las mejores coincidencias para un embedding.
        
        Args:
            embedding: Embedding a buscar (shape: [D])
            threshold: Umbral mínimo de similitud coseno
            top_k: Número máximo de resultados
            
        Returns:
            Lista de tuplas (nombre_persona, similitud) ordenadas por similitud descendente
        """
        if not self._loaded:
            if not self.load():
                return []
        
        if self.embeddings is None or len(self.embeddings) == 0:
            return []
        
        # Normalizar embedding de entrada
        embedding = np.asarray(embedding).flatten()
        norm = np.linalg.norm(embedding)
        if norm == 0:
            return []
        embedding = embedding / norm
        
        # Calcular similitud coseno
        similarities = self.embeddings @ embedding  # [N]
        
        # Obtener top_k índices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        matches = []
        for idx in top_indices:
            sim = float(similarities[idx])
            if sim >= threshold:
                person_name = str(self.labels[idx])
                matches.append((person_name, sim))
        
        return matches
    
    def get_person_count(self) -> int:
        """Retorna el número de personas únicas en la base de datos."""
        if not self._loaded:
            if not self.load():
                return 0
        return len(np.unique(self.labels)) if self.labels is not None else 0
    
    def get_total_embeddings(self) -> int:
        """Retorna el número total de embeddings."""
        if not self._loaded:
            if not self.load():
                return 0
        return len(self.embeddings) if self.embeddings is not None else 0
    
    def is_loaded(self) -> bool:
        """Verifica si la base de datos está cargada."""
        return self._loaded
