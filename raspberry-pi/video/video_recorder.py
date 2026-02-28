"""
Grabación de clips de video con buffer circular.

Mantiene un buffer de los últimos N frames para poder guardar clips que incluyan
momentos antes de la detección de un rostro.
"""
import re
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import logging
from collections import deque

from config import CLIP_DURATION_SECONDS, VIDEO_OUTPUT_DIR, VIDEO_FPS, VIDEO_BUFFER_SECONDS

logger = logging.getLogger(__name__)


class VideoClipRecorder:
    """
    Graba clips de video con buffer circular.
    
    Estrategia:
    - Mantiene un buffer circular de los últimos N frames (VIDEO_BUFFER_SECONDS)
    - Cuando se detecta un rostro, continúa grabando hasta completar CLIP_DURATION_SECONDS
    - Guarda el clip completo incluyendo el buffer previo
    """
    
    def __init__(
        self,
        fps: int = VIDEO_FPS,
        buffer_seconds: int = VIDEO_BUFFER_SECONDS,
        clip_duration_seconds: int = CLIP_DURATION_SECONDS,
        output_dir: Path = VIDEO_OUTPUT_DIR
    ):
        """
        Inicializa el grabador de clips.
        
        Args:
            fps: Frames por segundo del video
            buffer_seconds: Segundos de buffer previo a mantener
            clip_duration_seconds: Duración total del clip a guardar
            output_dir: Directorio donde guardar los clips
        """
        self.fps = fps
        self.buffer_seconds = buffer_seconds
        self.clip_duration_seconds = clip_duration_seconds
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Buffer circular
        buffer_frames = int(buffer_seconds * fps)
        self.buffer: deque = deque(maxlen=buffer_frames)
        
        # Estado de grabación
        self.is_recording = False
        self.recording_frames: List[np.ndarray] = []
        self.frame_size: Optional[tuple] = None  # (width, height)
        
        logger.info(
            f"VideoClipRecorder inicializado: "
            f"fps={fps}, buffer={buffer_seconds}s, clip={clip_duration_seconds}s"
        )
    
    def add_frame(self, frame: np.ndarray):
        """
        Añade un frame al buffer y a la grabación activa si está grabando.
        
        Args:
            frame: Frame BGR de OpenCV
        """
        if frame is None or frame.size == 0:
            return
        
        # Guardar tamaño del frame
        if self.frame_size is None:
            h, w = frame.shape[:2]
            self.frame_size = (w, h)
        
        # Añadir al buffer circular
        self.buffer.append(frame.copy())
        
        # Si está grabando, añadir a la grabación activa
        if self.is_recording:
            self.recording_frames.append(frame.copy())
    
    def start_recording(self):
        """Inicia la grabación de un clip."""
        if self.is_recording:
            logger.warning("Ya se está grabando un clip")
            return
        
        self.is_recording = True
        self.recording_frames = []
        
        # Incluir frames del buffer previo
        for frame in self.buffer:
            self.recording_frames.append(frame.copy())
        
        logger.info(f"Iniciando grabación de clip (buffer: {len(self.buffer)} frames)")
    
    def stop_recording(self, identity: Optional[str] = None) -> Optional[Path]:
        """
        Detiene la grabación y guarda el clip.
        
        Args:
            identity: Nombre de la persona reconocida (opcional). Si se proporciona,
                      se incluye en el nombre del archivo. Si no, se usa "unknown".
        
        Returns:
            Ruta al archivo guardado o None si no hay frames suficientes
        """
        if not self.is_recording:
            return None
        
        self.is_recording = False
        
        if len(self.recording_frames) == 0:
            logger.warning("No hay frames para guardar")
            return None
        
        # Calcular frames necesarios
        total_frames_needed = int(self.clip_duration_seconds * self.fps)
        
        # Si tenemos menos frames, usar los que tenemos
        # Si tenemos más, truncar al inicio (mantener los últimos)
        if len(self.recording_frames) > total_frames_needed:
            self.recording_frames = self.recording_frames[-total_frames_needed:]
        
        # Guardar clip
        output_path = self._save_clip(self.recording_frames, identity)
        
        # Limpiar
        self.recording_frames = []
        
        return output_path
    
    def _sanitize_identity(self, identity: Optional[str]) -> str:
        """Sanitiza una identidad para uso seguro en nombres de archivo."""
        if not identity or not identity.strip():
            return "unknown"
        # Reemplazar espacios por _, eliminar caracteres no seguros
        sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", identity.strip())
        return sanitized[:50] if len(sanitized) > 50 else sanitized

    def _save_clip(self, frames: List[np.ndarray], identity: Optional[str] = None) -> Path:
        """
        Guarda un clip de video desde una lista de frames.
        
        Args:
            frames: Lista de frames BGR
            identity: Nombre de la persona reconocida (opcional). Se incluye en el nombre.
            
        Returns:
            Ruta al archivo guardado
        """
        if len(frames) == 0 or self.frame_size is None:
            raise ValueError("No hay frames para guardar o tamaño de frame no definido")
        
        # Generar nombre con identidad si está disponible
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        ident_part = self._sanitize_identity(identity)
        filename = f"clip_{ident_part}_{timestamp}.mp4"
        output_path = self.output_dir / filename
        
        # Configurar codec y writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(
            str(output_path),
            fourcc,
            self.fps,
            self.frame_size
        )
        
        if not writer.isOpened():
            raise RuntimeError(f"No se pudo abrir el VideoWriter para {output_path}")
        
        # Escribir frames
        for frame in frames:
            # Asegurar que el frame tiene el tamaño correcto
            if frame.shape[:2][::-1] != self.frame_size:
                frame = cv2.resize(frame, self.frame_size)
            writer.write(frame)
        
        writer.release()
        
        logger.info(f"Clip guardado: {output_path} ({len(frames)} frames, {len(frames)/self.fps:.2f}s)")
        return output_path
    
    def should_continue_recording(self) -> bool:
        """
        Verifica si debe continuar grabando basado en la duración del clip.
        
        Returns:
            True si debe continuar, False si ya tiene suficientes frames
        """
        if not self.is_recording:
            return False
        
        frames_recorded = len(self.recording_frames)
        frames_needed = int(self.clip_duration_seconds * self.fps)
        
        return frames_recorded < frames_needed
    
    def get_recording_duration(self) -> float:
        """
        Retorna la duración actual de la grabación en segundos.
        
        Returns:
            Duración en segundos
        """
        if not self.is_recording:
            return 0.0
        return len(self.recording_frames) / self.fps
    
    def reset(self):
        """Reinicia el grabador (limpia buffer y estado)."""
        self.buffer.clear()
        self.is_recording = False
        self.recording_frames = []
        self.frame_size = None
        logger.debug("VideoClipRecorder reiniciado")
