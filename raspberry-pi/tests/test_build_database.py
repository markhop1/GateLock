#!/usr/bin/env python3
"""
Script de prueba para construcción completa de base de datos.

Prueba build_database.py con imágenes de prueba.
"""
import sys
import tempfile
import shutil
from pathlib import Path
import numpy as np
import cv2
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_imports():
    """Verifica que se pueden importar las dependencias."""
    try:
        from database.build_database import main as build_main
        import database.build_database
        logger.info("✓ Imports exitosos")
        return True
    except ImportError as e:
        logger.error(f"✗ Error de import: {e}")
        return False


def get_fixtures_dir() -> Path:
    """Return path to tests/fixtures/test_images."""
    return Path(__file__).resolve().parent / "fixtures" / "test_images"


def has_real_face_fixtures(fixtures_dir: Path) -> bool:
    """Check if fixtures dir has real face images (subdirs with jpg/png)."""
    if not fixtures_dir.exists():
        return False
    for subdir in fixtures_dir.iterdir():
        if subdir.is_dir():
            images = list(subdir.glob("*.jpg")) + list(subdir.glob("*.png"))
            if images:
                return True
    return False


def create_test_images(test_dir: Path, n_people=2, n_images_per_person=3):
    """Crea imágenes de prueba sintéticas."""
    logger.info(f"Creando {n_people} personas con {n_images_per_person} imágenes cada una...")
    
    for person_id in range(n_people):
        person_dir = test_dir / f"person_{person_id}"
        person_dir.mkdir(parents=True, exist_ok=True)
        
        for img_id in range(n_images_per_person):
            # Crear imagen sintética con "rostro" (círculo)
            img = np.random.randint(50, 200, (200, 200, 3), dtype=np.uint8)
            
            # Dibujar "rostro" simple (círculo)
            center = (100, 100)
            cv2.circle(img, center, 50, (200, 180, 160), -1)  # Cara
            cv2.circle(img, (85, 90), 5, (0, 0, 0), -1)  # Ojo izquierdo
            cv2.circle(img, (115, 90), 5, (0, 0, 0), -1)  # Ojo derecho
            cv2.ellipse(img, (100, 110), (20, 10), 0, 0, 180, (0, 0, 0), 2)  # Boca
            
            img_path = person_dir / f"image_{img_id}.jpg"
            cv2.imwrite(str(img_path), img)
    
    logger.info(f"✓ Imágenes de prueba creadas en {test_dir}")


def test_build_database_with_test_images():
    """Prueba construcción de BD con imágenes de prueba."""
    logger.info("Probando construcción de base de datos...")
    
    try:
        import tempfile
        import sys
        from database.build_database import main
        
        fixtures_dir = get_fixtures_dir()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_images_dir = tmp_path / "known_faces"
            test_images_dir.mkdir()
            output_dir = tmp_path / "database_output"
            output_dir.mkdir()
            
            # Use real fixtures if available (LFW), else synthetic (RetinaFace won't detect)
            if has_real_face_fixtures(fixtures_dir):
                logger.info(f"Usando imágenes reales de {fixtures_dir}")
                for person_dir in fixtures_dir.iterdir():
                    if person_dir.is_dir():
                        dest = test_images_dir / person_dir.name
                        shutil.copytree(person_dir, dest)
            else:
                logger.info("No hay fixtures reales, creando imágenes sintéticas...")
                create_test_images(test_images_dir, n_people=2, n_images_per_person=3)
            
            max_imgs = 5 if has_real_face_fixtures(fixtures_dir) else 3
            
            # Ejecutar build_database.py con argumentos
            original_argv = sys.argv
            
            try:
                sys.argv = [
                    'build_database.py',
                    '--data_dir', str(test_images_dir),
                    '--output_dir', str(output_dir),
                    '--aug_per_image', '5',
                    '--max_images_per_id', str(max_imgs)
                ]
                
                # Ejecutar main
                main()
                
                # Verificar que se crearon los archivos
                embeddings_file = output_dir / "face_embeddings.npy"
                labels_file = output_dir / "face_labels.npy"
                
                if embeddings_file.exists() and labels_file.exists():
                    logger.info("✓ Archivos de base de datos creados")
                    
                    # Verificar contenido
                    embeddings = np.load(embeddings_file)
                    labels = np.load(labels_file)
                    
                    logger.info(f"  Embeddings shape: {embeddings.shape}")
                    logger.info(f"  Labels shape: {labels.shape}")
                    logger.info(f"  Personas únicas: {len(np.unique(labels))}")
                    
                    # Validaciones básicas
                    assert embeddings.ndim == 2, "Embeddings deben ser 2D"
                    assert len(labels) == len(embeddings), "Número de labels debe coincidir con embeddings"
                    assert len(np.unique(labels)) >= 1, "Debe haber al menos una persona"
                    
                    logger.info("✓ Validaciones de formato pasadas")
                    return True
                else:
                    logger.error("✗ Archivos de base de datos no creados")
                    return False
                    
            finally:
                sys.argv = original_argv
                
    except Exception as e:
        logger.error(f"✗ Error construyendo base de datos: {e}", exc_info=True)
        return False


def test_build_database_real():
    """Intenta construir BD con imágenes reales si existen."""
    logger.info("Intentando construir BD con imágenes reales...")
    
    try:
        from config import KNOWN_FACES_DIR
        
        if not KNOWN_FACES_DIR.exists():
            logger.warning(f"⚠ Directorio de imágenes reales no encontrado: {KNOWN_FACES_DIR}")
            logger.info("  Crea el directorio y añade imágenes para probar")
            return None
        
        # Verificar que hay imágenes
        identities = []
        for d in KNOWN_FACES_DIR.iterdir():
            if d.is_dir():
                images = list(d.glob("*.jpg")) + list(d.glob("*.png"))
                if images:
                    identities.append(d.name)
        
        if not identities:
            logger.warning("⚠ No se encontraron imágenes en known_faces/")
            return None
        
        logger.info(f"Encontradas {len(identities)} identidades con imágenes")
        logger.info("  Para construir la BD real, ejecuta: python database/build_database.py")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error verificando imágenes reales: {e}")
        return None


def main():
    logger.info("=" * 60)
    logger.info("Test de Construcción de Base de Datos")
    logger.info("=" * 60)
    
    # Test 1: Imports
    if not test_imports():
        sys.exit(1)
    
    success = True
    
    # Test 2: Construcción con imágenes de prueba
    if not test_build_database_with_test_images():
        success = False
    
    # Test 3: Verificar imágenes reales (información)
    test_build_database_real()
    
    logger.info("=" * 60)
    if success:
        logger.info("✓ Todos los tests pasaron")
        sys.exit(0)
    else:
        logger.error("✗ Algunos tests fallaron")
        sys.exit(1)


if __name__ == "__main__":
    main()
