#!/usr/bin/env python3
"""
Script de prueba para el detector RetinaFace.

Prueba la detección de rostros usando RetinaFace (vía InsightFace).
"""
import argparse
import sys
import cv2
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_imports():
    """Verifica que se pueden importar las dependencias."""
    try:
        from detection.face_detector import RetinaFaceDetector, FaceDetection
        logger.info("✓ Imports exitosos")
        return True
    except ImportError as e:
        logger.error(f"✗ Error de import: {e}")
        logger.error("Instala las dependencias con: pip install insightface onnxruntime")
        return False


def test_detector_initialization():
    """Prueba la inicialización del detector."""
    try:
        from detection.face_detector import RetinaFaceDetector
        
        logger.info("Inicializando detector RetinaFace...")
        detector = RetinaFaceDetector()
        detector.initialize()
        logger.info("✓ Detector inicializado correctamente")
        return detector
    except Exception as e:
        logger.error(f"✗ Error al inicializar detector: {e}")
        return None


def test_detection_from_image(detector, image_path: Path):
    """Prueba detección desde una imagen."""
    logger.info(f"Probando detección en imagen: {image_path}")
    
    if not image_path.exists():
        logger.error(f"✗ Imagen no encontrada: {image_path}")
        return False
    
    try:
        # Cargar imagen
        frame = cv2.imread(str(image_path))
        if frame is None:
            logger.error(f"✗ No se pudo cargar la imagen: {image_path}")
            return False
        
        logger.info(f"Imagen cargada: {frame.shape}")
        
        # Detectar rostros
        detections = detector.detect_faces(frame)
        
        logger.info(f"✓ Detecciones encontradas: {len(detections)}")
        
        if detections:
            for i, det in enumerate(detections):
                logger.info(
                    f"  Detección {i+1}: "
                    f"bbox=({det.x1}, {det.y1}, {det.x2}, {det.y2}), "
                    f"confianza={det.confidence:.3f}"
                )
            
            # Estadísticas
            confidences = [d.confidence for d in detections]
            logger.info(f"  Confianza promedio: {np.mean(confidences):.3f}")
            logger.info(f"  Confianza máxima: {np.max(confidences):.3f}")
            logger.info(f"  Confianza mínima: {np.min(confidences):.3f}")
        else:
            logger.warning("  No se detectaron rostros")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error durante detección: {e}", exc_info=True)
        return False


def test_detection_from_camera(detector):
    """Prueba detección desde cámara."""
    logger.info("Probando detección desde cámara...")
    
    try:
        from config import CAMERA_INDEX
        
        cap = cv2.VideoCapture(CAMERA_INDEX)
        if not cap.isOpened():
            logger.error(f"✗ No se pudo abrir la cámara {CAMERA_INDEX}")
            return False
        
        logger.info(f"Cámara {CAMERA_INDEX} abierta")
        
        # Capturar algunos frames
        frames_tested = 0
        detections_found = 0
        
        for i in range(10):  # Probar 10 frames
            ret, frame = cap.read()
            if not ret:
                logger.warning(f"  Frame {i+1}: No se pudo leer")
                continue
            
            frames_tested += 1
            detections = detector.detect_faces(frame)
            
            if detections:
                detections_found += len(detections)
                logger.info(f"  Frame {i+1}: {len(detections)} rostro(s) detectado(s)")
        
        cap.release()
        
        logger.info(f"✓ Frames probados: {frames_tested}")
        logger.info(f"✓ Total detecciones: {detections_found}")
        
        if frames_tested == 0:
            logger.error("✗ No se pudieron leer frames de la cámara")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error con cámara: {e}", exc_info=True)
        return False


def main():
    parser = argparse.ArgumentParser(description="Prueba el detector RetinaFace")
    parser.add_argument(
        '--image',
        type=str,
        help='Ruta a imagen de prueba'
    )
    parser.add_argument(
        '--camera',
        action='store_true',
        help='Probar con cámara'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Test de Detección RetinaFace")
    logger.info("=" * 60)
    
    # Test 1: Imports
    if not test_imports():
        sys.exit(1)
    
    # Test 2: Inicialización
    detector = test_detector_initialization()
    if detector is None:
        sys.exit(1)
    
    success = True
    
    # Test 3: Detección desde imagen (si se proporciona)
    if args.image:
        image_path = Path(args.image)
        if not test_detection_from_image(detector, image_path):
            success = False
    
    # Test 4: Detección desde cámara (si se solicita)
    if args.camera:
        if not test_detection_from_camera(detector):
            success = False
    
    # Si no se especificó ninguna opción, probar con imagen de prueba si existe
    if not args.image and not args.camera:
        test_image = Path(__file__).parent / "fixtures" / "test_images" / "test_face.jpg"
        if test_image.exists():
            logger.info("Probando con imagen de prueba por defecto...")
            if not test_detection_from_image(detector, test_image):
                success = False
        else:
            logger.warning("No se proporcionó --image ni --camera, y no hay imagen de prueba")
            logger.info("Usa --image <ruta> o --camera para probar")
    
    logger.info("=" * 60)
    if success:
        logger.info("✓ Todos los tests pasaron")
        sys.exit(0)
    else:
        logger.error("✗ Algunos tests fallaron")
        sys.exit(1)


if __name__ == "__main__":
    main()
