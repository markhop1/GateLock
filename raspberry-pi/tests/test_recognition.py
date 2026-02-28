#!/usr/bin/env python3
"""
Script de prueba para el reconocedor MobileFaceNet.

Prueba la extracción de embeddings usando MobileFaceNet.
"""
import argparse
import sys
import cv2
import numpy as np
from pathlib import Path
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_imports():
    """Verifica que se pueden importar las dependencias."""
    try:
        from recognition.face_recognizer import MobileFaceNetRecognizer
        logger.info("✓ Imports exitosos")
        return True
    except ImportError as e:
        logger.error(f"✗ Error de import: {e}")
        logger.error("Instala las dependencias con: pip install tensorflow")
        return False


def test_recognizer_initialization():
    """Prueba la inicialización del reconocedor."""
    try:
        from recognition.face_recognizer import MobileFaceNetRecognizer
        
        logger.info("Inicializando reconocedor MobileFaceNet...")
        recognizer = MobileFaceNetRecognizer()
        recognizer.initialize()
        
        embedding_size = recognizer.get_embedding_size()
        logger.info(f"✓ Reconocedor inicializado correctamente")
        logger.info(f"  Tamaño de embedding: {embedding_size}")
        return recognizer
    except Exception as e:
        logger.error(f"✗ Error al inicializar reconocedor: {e}")
        logger.error("Nota: Si no tienes un modelo pre-entrenado, se creará uno básico")
        return None


def test_embedding_extraction(recognizer, image_path: Path):
    """Prueba extracción de embedding desde una imagen."""
    logger.info(f"Probando extracción de embedding en: {image_path}")
    
    if not image_path.exists():
        logger.error(f"✗ Imagen no encontrada: {image_path}")
        return False
    
    try:
        # Cargar imagen
        image_bgr = cv2.imread(str(image_path))
        if image_bgr is None:
            logger.error(f"✗ No se pudo cargar la imagen: {image_path}")
            return False
        
        # Convertir a RGB
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        logger.info(f"Imagen cargada: {image_rgb.shape}")
        
        # Extraer embedding
        start_time = time.time()
        embedding = recognizer.extract_embedding(image_rgb)
        elapsed = time.time() - start_time
        
        # Verificar embedding
        embedding_size = recognizer.get_embedding_size()
        
        logger.info(f"✓ Embedding extraído exitosamente")
        logger.info(f"  Tiempo de inferencia: {elapsed*1000:.2f} ms")
        logger.info(f"  Tamaño del embedding: {len(embedding)}")
        logger.info(f"  Tamaño esperado: {embedding_size}")
        logger.info(f"  Norma L2 del embedding: {np.linalg.norm(embedding):.6f}")
        logger.info(f"  Rango de valores: [{np.min(embedding):.4f}, {np.max(embedding):.4f}]")
        
        # Verificar que está normalizado
        norm = np.linalg.norm(embedding)
        if abs(norm - 1.0) < 0.01:
            logger.info("  ✓ Embedding está normalizado (L2)")
        else:
            logger.warning(f"  ⚠ Embedding no está completamente normalizado (norma: {norm:.6f})")
        
        # Verificar tamaño
        if len(embedding) == embedding_size:
            logger.info("  ✓ Tamaño del embedding correcto")
        else:
            logger.error(f"  ✗ Tamaño incorrecto: esperado {embedding_size}, obtenido {len(embedding)}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error durante extracción: {e}", exc_info=True)
        return False


def test_multiple_extractions(recognizer, image_path: Path, n=5):
    """Prueba múltiples extracciones para medir consistencia."""
    logger.info(f"Probando {n} extracciones para medir consistencia...")
    
    try:
        image_bgr = cv2.imread(str(image_path))
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        
        embeddings = []
        times = []
        
        for i in range(n):
            start = time.time()
            emb = recognizer.extract_embedding(image_rgb)
            elapsed = time.time() - start
            
            embeddings.append(emb)
            times.append(elapsed)
        
        # Verificar consistencia (mismo embedding para misma imagen)
        embeddings = np.array(embeddings)
        mean_emb = embeddings.mean(axis=0)
        
        # Calcular similitud entre extracciones
        similarities = []
        for i in range(n):
            for j in range(i+1, n):
                sim = np.dot(embeddings[i], embeddings[j])
                similarities.append(sim)
        
        logger.info(f"✓ {n} extracciones completadas")
        logger.info(f"  Tiempo promedio: {np.mean(times)*1000:.2f} ms")
        logger.info(f"  Tiempo std: {np.std(times)*1000:.2f} ms")
        logger.info(f"  Similitud promedio entre extracciones: {np.mean(similarities):.6f}")
        logger.info(f"  Similitud mínima: {np.min(similarities):.6f}")
        
        # Las extracciones deberían ser idénticas (o muy similares)
        if np.min(similarities) > 0.99:
            logger.info("  ✓ Extracciones consistentes")
        else:
            logger.warning("  ⚠ Hay variación entre extracciones")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error en test de consistencia: {e}", exc_info=True)
        return False


def main():
    parser = argparse.ArgumentParser(description="Prueba el reconocedor MobileFaceNet")
    parser.add_argument(
        '--image',
        type=str,
        required=True,
        help='Ruta a imagen de rostro para probar'
    )
    parser.add_argument(
        '--consistency',
        action='store_true',
        help='Ejecutar test de consistencia (múltiples extracciones)'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Test de Reconocimiento MobileFaceNet")
    logger.info("=" * 60)
    
    # Test 1: Imports
    if not test_imports():
        sys.exit(1)
    
    # Test 2: Inicialización
    recognizer = test_recognizer_initialization()
    if recognizer is None:
        sys.exit(1)
    
    success = True
    
    # Test 3: Extracción de embedding
    image_path = Path(args.image)
    if not test_embedding_extraction(recognizer, image_path):
        success = False
    
    # Test 4: Consistencia (opcional)
    if args.consistency and success:
        if not test_multiple_extractions(recognizer, image_path):
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
