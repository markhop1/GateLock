"""
Hilo de captura de cámara independiente.

Lee frames a velocidad constante sin bloquearse por la detección/reconocimiento.
Así el preview y la grabación mantienen FPS uniforme aunque el procesamiento sea lento.
"""
import threading
import queue
import logging
import time
from typing import Optional, Callable, Any

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class CameraCaptureThread(threading.Thread):
    """
    Hilo que lee frames de la cámara a máxima velocidad.
    
    - Alimenta al video recorder con cada frame (captura constante)
    - Entrega el frame más reciente al loop principal para detección
    """

    def __init__(
        self,
        camera: cv2.VideoCapture,
        video_recorder: Any,
        target_fps: int = 30,
        daemon: bool = True,
    ):
        super().__init__(daemon=daemon)
        self.camera = camera
        self.video_recorder = video_recorder
        self.frame_interval = 1.0 / target_fps if target_fps > 0 else 0.033
        self._frame_queue: queue.Queue = queue.Queue(maxsize=1)
        self._running = True
        self._last_frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()

    def stop(self):
        """Solicita detener el hilo."""
        self._running = False

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """
        Obtiene el frame más reciente para procesamiento.
        No bloquea: devuelve el último frame disponible.
        """
        try:
            return self._frame_queue.get_nowait()
        except queue.Empty:
            with self._lock:
                return self._last_frame.copy() if self._last_frame is not None else None

    def run(self):
        """Loop de captura: lee a target_fps para video con velocidad uniforme."""
        next_time = time.time()
        while self._running:
            now = time.time()
            if now < next_time:
                time.sleep(min(0.005, next_time - now))
                continue

            ret, frame = self.camera.read()
            if not ret:
                time.sleep(0.01)
                continue

            next_time += self.frame_interval
            if next_time < time.time():
                next_time = time.time()

            # Solo el hilo de captura añade frames (evita duplicados)
            self.video_recorder.add_frame(frame)

            with self._lock:
                self._last_frame = frame.copy()

            try:
                self._frame_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self._frame_queue.put_nowait(frame.copy())
            except queue.Full:
                pass

        logger.debug("Hilo de captura detenido")
