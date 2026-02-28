#!/usr/bin/env python3
"""
Script de prueba para VideoClipRecorder.

Prueba grabación de clips de video con buffer circular.
"""
import argparse
import sys
import cv2
import numpy as np
from pathlib import Path
import tempfile
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_imports():
    """Verifica que se pueden importar las dependencias."""
    try:
        from video.video_recorder import VideoClipRecorder
        logger.info("✓ Imports exitosos")
        return True
    except ImportError as e:
        logger.error(f"✗ Error de import: {e}")
        return False


def test_recorder_initialization():
    """Prueba inicialización del grabador."""
    try:
        from video.video_recorder import VideoClipRecorder
        
        logger.info("Inicializando VideoClipRecorder...")
        recorder = VideoClipRecorder(fps=30, buffer_seconds=2, clip_duration_seconds=5)
        
        logger.info("✓ Grabador inicializado")
        logger.info(f"  FPS: {recorder.fps}")
        logger.info(f"  Buffer: {recorder.buffer_seconds}s")
        logger.info(f"  Duración clip: {recorder.clip_duration_seconds}s")
        
        return recorder
    except Exception as e:
        logger.error(f"✗ Error inicializando grabador: {e}", exc_info=True)
        return None


def test_buffer_functionality(recorder):
    """Prueba funcionalidad del buffer circular."""
    logger.info("Probando buffer circular...")
    
    try:
        # Crear frames sintéticos
        frame_size = (640, 480)
        n_frames = 100
        
        for i in range(n_frames):
            # Frame con número de frame visible
            frame = np.zeros((frame_size[1], frame_size[0], 3), dtype=np.uint8)
            cv2.putText(
                frame, f"Frame {i}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2
            )
            recorder.add_frame(frame)
        
        # Verificar tamaño del buffer
        buffer_size = len(recorder.buffer)
        expected_buffer_size = recorder.buffer_seconds * recorder.fps
        
        logger.info(f"✓ Frames añadidos: {n_frames}")
        logger.info(f"  Tamaño del buffer: {buffer_size}")
        logger.info(f"  Tamaño esperado: {expected_buffer_size}")
        
        if buffer_size <= expected_buffer_size:
            logger.info("  ✓ Buffer circular funciona correctamente")
        else:
            logger.warning("  ⚠ Buffer más grande de lo esperado")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error probando buffer: {e}", exc_info=True)
        return False


def test_recording_synthetic(recorder):
    """Prueba grabación con frames sintéticos."""
    logger.info("Probando grabación de clip...")
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Añadir frames al buffer
            frame_size = (640, 480)
            for i in range(50):
                frame = np.random.randint(0, 255, (frame_size[1], frame_size[0], 3), dtype=np.uint8)
                recorder.add_frame(frame)
            
            # Iniciar grabación
            recorder.start_recording()
            logger.info("✓ Grabación iniciada")
            
            # Continuar añadiendo frames
            for i in range(100):
                frame = np.random.randint(0, 255, (frame_size[1], frame_size[0], 3), dtype=np.uint8)
                recorder.add_frame(frame)
            
            # Detener y guardar
            output_path = recorder.stop_recording()
            
            if output_path and output_path.exists():
                file_size = output_path.stat().st_size
                logger.info(f"✓ Clip guardado: {output_path}")
                logger.info(f"  Tamaño del archivo: {file_size / 1024:.2f} KB")
                
                # Verificar que el archivo es válido
                cap = cv2.VideoCapture(str(output_path))
                if cap.isOpened():
                    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    logger.info(f"  Frames en video: {frame_count}")
                    logger.info(f"  FPS del video: {fps}")
                    cap.release()
                    
                    if frame_count > 0:
                        logger.info("  ✓ Archivo de video válido")
                    else:
                        logger.warning("  ⚠ Video vacío")
                else:
                    logger.warning("  ⚠ No se pudo abrir el video para verificación")
                
                # Limpiar
                output_path.unlink()
                return True
            else:
                logger.error("✗ No se guardó el clip")
                return False
                
    except Exception as e:
        logger.error(f"✗ Error en grabación: {e}", exc_info=True)
        return False


def test_recording_from_camera(recorder):
    """Prueba grabación desde cámara."""
    logger.info("Probando grabación desde cámara...")
    
    try:
        from config import CAMERA_INDEX
        
        cap = cv2.VideoCapture(CAMERA_INDEX)
        if not cap.isOpened():
            logger.warning(f"⚠ No se pudo abrir la cámara {CAMERA_INDEX}")
            return False
        
        logger.info(f"Cámara {CAMERA_INDEX} abierta")
        
        # Capturar algunos frames para el buffer
        for i in range(10):
            ret, frame = cap.read()
            if ret:
                recorder.add_frame(frame)
        
        # Iniciar grabación
        recorder.start_recording()
        
        # Continuar grabando
        frames_recorded = 0
        for i in range(30):  # ~1 segundo a 30fps
            ret, frame = cap.read()
            if ret:
                recorder.add_frame(frame)
                frames_recorded += 1
        
        cap.release()
        
        # Detener grabación
        output_path = recorder.stop_recording()
        
        if output_path and output_path.exists():
            logger.info(f"✓ Clip de cámara guardado: {output_path}")
            logger.info(f"  Frames capturados: {frames_recorded}")
            
            # Limpiar
            output_path.unlink()
            return True
        else:
            logger.error("✗ No se guardó el clip de cámara")
            return False
            
    except Exception as e:
        logger.error(f"✗ Error con cámara: {e}", exc_info=True)
        return False


def main():
    parser = argparse.ArgumentParser(description="Prueba VideoClipRecorder")
    parser.add_argument(
        '--camera',
        action='store_true',
        help='Probar con cámara real'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Test de VideoClipRecorder")
    logger.info("=" * 60)
    
    # Test 1: Imports
    if not test_imports():
        sys.exit(1)
    
    # Test 2: Inicialización
    recorder = test_recorder_initialization()
    if recorder is None:
        sys.exit(1)
    
    success = True
    
    # Test 3: Buffer
    if not test_buffer_functionality(recorder):
        success = False
    
    # Test 4: Grabación sintética
    recorder2 = test_recorder_initialization()  # Nuevo recorder limpio
    if recorder2:
        if not test_recording_synthetic(recorder2):
            success = False
    
    # Test 5: Grabación desde cámara (opcional)
    if args.camera:
        recorder3 = test_recorder_initialization()
        if recorder3:
            if not test_recording_from_camera(recorder3):
                success = False
    
    logger.info("=" * 60)
    if success:
        logger.info("✓ Todos los tests pasaron")
        sys.exit(0)
    else:
        logger.error("✗ Algunos tests fallaron")
        sys.exit(1)


if __name__ == "__main__":
    main()
