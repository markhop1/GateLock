"""
Programa principal del sistema de reconocimiento facial para Raspberry Pi.

Detecta rostros en tiempo real, graba clips de video cuando detecta un rostro,
identifica a la persona comparando con la base de datos, y envía alertas al backend.
"""
import cv2
import numpy as np
import logging
import signal
import sys
import time
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime, timedelta

from config import (
    CAMERA_INDEX, RECOGNITION_THRESHOLD, API_BASE_URL, API_USERNAME, API_PASSWORD,
    ALERT_COOLDOWN_SECONDS, LOG_LEVEL, LOG_FILE
)
from detection.face_detector import RetinaFaceDetector, FaceDetection
from recognition.face_recognizer import MobileFaceNetRecognizer
from database.face_db import FaceDatabase
from video.video_recorder import VideoClipRecorder
from api.auth import APIAuth
from api.client import GateLockAPI

# Configurar logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        *([logging.FileHandler(LOG_FILE)] if LOG_FILE else [])
    ]
)
logger = logging.getLogger(__name__)


class FaceRecognitionSystem:
    """
    Sistema principal de reconocimiento facial.
    
    Orquesta detección, reconocimiento, grabación de video y envío de alertas.
    """
    
    def __init__(self):
        """Inicializa todos los componentes del sistema."""
        logger.info("Inicializando sistema de reconocimiento facial...")
        
        # Componentes de visión
        self.detector = RetinaFaceDetector()
        self.recognizer = MobileFaceNetRecognizer()
        self.database = FaceDatabase()
        
        # Componente de video
        self.video_recorder = VideoClipRecorder()
        
        # Componentes de API
        self.auth = APIAuth()
        self.api = GateLockAPI(auth=self.auth)
        
        # Estado
        self.camera: Optional[cv2.VideoCapture] = None
        self.running = False
        self.last_alert_time: Dict[str, datetime] = {}  # person_name -> timestamp
        self.last_alert_any_time: Optional[datetime] = None  # Cooldown global (cualquier persona)
        self.last_recognized_in_session: Optional[str] = None  # Última persona reconocida en esta grabación
        self.last_similarity: float = 0.0  # Similitud del último reconocimiento
        
        # Señal de shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def initialize(self):
        """Inicializa todos los componentes."""
        logger.info("Inicializando componentes...")
        
        # Inicializar detector
        try:
            self.detector.initialize()
            logger.info("Detector RetinaFace inicializado")
        except Exception as e:
            logger.error(f"Error al inicializar detector: {e}")
            raise
        
        # Inicializar reconocedor
        try:
            self.recognizer.initialize()
            logger.info("Reconocedor MobileFaceNet inicializado")
        except Exception as e:
            logger.error(f"Error al inicializar reconocedor: {e}")
            raise
        
        # Cargar base de datos
        if not self.database.load():
            logger.error("No se pudo cargar la base de datos. Ejecuta build_database.py primero.")
            raise RuntimeError("Base de datos no disponible")
        
        logger.info(f"Base de datos cargada: {self.database.get_person_count()} personas")
        
        # Inicializar cámara
        try:
            self.camera = cv2.VideoCapture(CAMERA_INDEX)
            if not self.camera.isOpened():
                raise RuntimeError(f"No se pudo abrir la cámara {CAMERA_INDEX}")
            
            # Configurar resolución (opcional, para mejor rendimiento)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            logger.info(f"Cámara {CAMERA_INDEX} inicializada")
        except Exception as e:
            logger.error(f"Error al inicializar cámara: {e}")
            raise
        
        # Autenticación con backend
        if API_USERNAME and API_PASSWORD:
            logger.info("Autenticando con backend...")
            if not self.auth.login(API_USERNAME, API_PASSWORD):
                logger.warning("No se pudo autenticar con el backend. Las alertas no se enviarán.")
            else:
                logger.info("Autenticación exitosa")
                if not self.api.test_connection():
                    logger.warning("Backend no alcanzable. Las alertas podrían fallar si la red no está disponible.")
                else:
                    logger.info("Conexión con backend verificada")
        else:
            logger.warning("Credenciales de API no configuradas. Las alertas no se enviarán.")
    
    def _signal_handler(self, signum, frame):
        """Maneja señales de shutdown."""
        logger.info(f"Señal {signum} recibida. Cerrando...")
        self.running = False
    
    def _check_cooldown(self, person_name: str) -> bool:
        """
        Verifica si ha pasado suficiente tiempo desde la última alerta.
        Aplica cooldown global (cualquier persona) y por persona.
        
        Args:
            person_name: Nombre de la persona
            
        Returns:
            True si puede enviar alerta, False si está en cooldown
        """
        now = datetime.now()
        
        # Cooldown global: no enviar si hubo cualquier alerta hace menos de X segundos
        if self.last_alert_any_time is not None:
            elapsed_any = (now - self.last_alert_any_time).total_seconds()
            if elapsed_any < ALERT_COOLDOWN_SECONDS:
                return False
        
        # Cooldown por persona
        if person_name in self.last_alert_time:
            elapsed = (now - self.last_alert_time[person_name]).total_seconds()
            if elapsed < ALERT_COOLDOWN_SECONDS:
                return False
        
        return True
    
    def _process_detection(self, detection: FaceDetection, frame: np.ndarray) -> Optional[str]:
        """
        Procesa una detección de rostro: reconoce y envía alerta si es necesario.
        
        Args:
            detection: Detección de rostro
            frame: Frame completo
            
        Returns:
            Nombre de la persona reconocida o None
        """
        try:
            # Extraer embedding del rostro
            face_crop, embedding = self.recognizer.recognize_face(detection, frame)
            
            if embedding is None or len(embedding) == 0:
                return None
            
            # Buscar en base de datos
            person_name, similarity = self.database.find_match(embedding, threshold=RECOGNITION_THRESHOLD)
            
            if person_name and similarity >= RECOGNITION_THRESHOLD:
                logger.info(f"Persona reconocida: {person_name} (similitud: {similarity:.3f})")
                self.last_recognized_in_session = person_name
                self.last_similarity = similarity
                
                # Verificar cooldown
                if not self._check_cooldown(person_name):
                    logger.debug(f"Alerta para {person_name} en cooldown")
                    return person_name
                
                # Enviar alerta (guarda clip y sube)
                self._send_alert(person_name, similarity)
                
                # Actualizar tiempos de última alerta (global y por persona)
                now = datetime.now()
                self.last_alert_time[person_name] = now
                self.last_alert_any_time = now
                self.last_recognized_in_session = None  # Sesión completada
                
                return person_name
            
            return None
            
        except Exception as e:
            logger.error(f"Error procesando detección: {e}")
            return None
    
    def _send_alert(
        self,
        person_name: str,
        similarity: float,
        video_path: Optional[Path] = None,
    ):
        """
        Envía una alerta al backend.
        
        Args:
            person_name: Nombre de la persona reconocida
            similarity: Similitud del reconocimiento
            video_path: Ruta al clip ya guardado (opcional). Si es None, detiene la grabación.
        """
        try:
            if video_path is None:
                video_path = self.video_recorder.stop_recording(identity=person_name)
            
            if not video_path:
                logger.warning("No hay clip de video para enviar")
                return
            
            # Subir video
            logger.info(f"Subiendo video: {video_path}")
            video_url = self.api.upload_video(video_path)
            
            if not video_url:
                logger.error("No se pudo subir el video")
                return
            
            # Crear alerta
            message = f"Persona reconocida: {person_name} (similitud: {similarity:.2%})"
            alert = self.api.create_alert(
                person_name=person_name,
                video_url=video_url,
                message=message
            )
            
            if alert:
                logger.info(f"Alerta enviada exitosamente: {alert.get('id')}")
                
                # Opcional: eliminar video local después de subir
                # video_path.unlink()
            else:
                logger.error("No se pudo crear la alerta")
                
        except Exception as e:
            logger.error(f"Error enviando alerta: {e}")
    
    def run(self, show_preview: bool = False):
        """
        Ejecuta el loop principal de reconocimiento.
        
        Args:
            show_preview: Si True, muestra ventana con preview
        """
        if not self.camera:
            raise RuntimeError("Cámara no inicializada")
        
        self.running = True
        logger.info("Iniciando loop de reconocimiento...")
        
        frame_count = 0
        last_detection_time = None
        
        try:
            while self.running:
                ret, frame = self.camera.read()
                if not ret:
                    logger.warning("No se pudo leer frame de la cámara")
                    time.sleep(0.1)
                    continue
                
                frame_count += 1
                
                # Detectar rostros
                detections = self.detector.detect_faces(frame)
                
                # Añadir frame al grabador
                self.video_recorder.add_frame(frame)
                
                if detections:
                    # Si no estábamos grabando, iniciar grabación
                    if not self.video_recorder.is_recording:
                        self.last_recognized_in_session = None
                        self.last_similarity = 0.0
                        self.video_recorder.start_recording()
                        logger.info("Rostro detectado, iniciando grabación...")
                    
                    last_detection_time = time.time()
                    
                    # Procesar cada detección
                    for detection in detections:
                        person_name = self._process_detection(detection, frame)
                        
                        # Dibujar en preview si está habilitado
                        if show_preview:
                            x1, y1, x2, y2 = detection.x1, detection.y1, detection.x2, detection.y2
                            color = (0, 255, 0) if person_name else (0, 0, 255)
                            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                            
                            label = person_name if person_name else "Unknown"
                            cv2.putText(
                                frame, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
                            )
                    
                    # Si ya tenemos suficientes frames (10s), guardar clip aunque siga detectando
                    if (
                        self.video_recorder.is_recording
                        and not self.video_recorder.should_continue_recording()
                    ):
                        identity = self.last_recognized_in_session or "unknown"
                        path = self.video_recorder.stop_recording(identity=identity)
                        if path:
                            # Si reconocimos y no estábamos en cooldown, enviar alerta
                            if (
                                self.last_recognized_in_session
                                and self._check_cooldown(self.last_recognized_in_session)
                            ):
                                now = datetime.now()
                                self.last_alert_time[self.last_recognized_in_session] = now
                                self.last_alert_any_time = now
                                self._send_alert(
                                    self.last_recognized_in_session,
                                    self.last_similarity,
                                    video_path=path,
                                )
                        self.last_recognized_in_session = None
                        self.last_similarity = 0.0
                        last_detection_time = None
                else:
                    # Si estábamos grabando y no hay detecciones, verificar si completar
                    if self.video_recorder.is_recording:
                        if last_detection_time:
                            elapsed = time.time() - last_detection_time
                            if elapsed > 2.0:  # 2 segundos sin detecciones
                                if not self.video_recorder.should_continue_recording():
                                    # Tenemos suficientes frames, guardar clip
                                    identity = self.last_recognized_in_session or "unknown"
                                    path = self.video_recorder.stop_recording(identity=identity)
                                    if path and self.last_recognized_in_session and self._check_cooldown(
                                        self.last_recognized_in_session
                                    ):
                                        now = datetime.now()
                                        self.last_alert_time[self.last_recognized_in_session] = now
                                        self.last_alert_any_time = now
                                        self._send_alert(
                                            self.last_recognized_in_session,
                                            self.last_similarity,
                                            video_path=path,
                                        )
                                    self.last_recognized_in_session = None
                                    self.last_similarity = 0.0
                                    last_detection_time = None
                
                # Mostrar preview
                if show_preview:
                    cv2.imshow("Face Recognition", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        logger.info("Tecla 'q' presionada. Cerrando...")
                        self.running = False
                
                # Log periódico
                if frame_count % 300 == 0:  # Cada 300 frames
                    logger.debug(f"Frames procesados: {frame_count}")
        
        except KeyboardInterrupt:
            logger.info("Interrupción de teclado recibida")
        except Exception as e:
            logger.error(f"Error en loop principal: {e}", exc_info=True)
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Limpia recursos al cerrar."""
        logger.info("Limpiando recursos...")
        
        if self.video_recorder.is_recording:
            self.video_recorder.stop_recording()
        
        if self.camera:
            self.camera.release()
        
      cv2.destroyAllWindows()
        
        logger.info("Recursos liberados")


def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sistema de reconocimiento facial para Raspberry Pi")
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Mostrar preview de la cámara"
    )
    args = parser.parse_args()
    
    system = FaceRecognitionSystem()
    
    try:
        system.initialize()
        system.run(show_preview=args.preview)
    except Exception as e:
        logger.error(f"Error fatal: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
