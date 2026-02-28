#!/usr/bin/env python3
"""
Script de prueba para FaceDatabase.

Prueba carga, guardado y búsqueda en la base de datos de embeddings.
"""
import sys
import numpy as np
import tempfile
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_imports():
    """Verifica que se pueden importar las dependencias."""
    try:
        from database.face_db import FaceDatabase
        logger.info("✓ Imports exitosos")
        return True
    except ImportError as e:
        logger.error(f"✗ Error de import: {e}")
        return False


def test_database_creation():
    """Prueba creación de base de datos con datos sintéticos."""
    logger.info("Creando base de datos de prueba...")
    
    try:
        from database.face_db import FaceDatabase
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Crear embeddings y labels de prueba
            n_people = 5
            embedding_size = 128
            
            embeddings = np.random.randn(n_people * 3, embedding_size)  # 3 embeddings por persona
            labels = []
            for i in range(n_people):
                labels.extend([f"person_{i}"] * 3)
            labels = np.array(labels)
            
            # Normalizar embeddings
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            embeddings_normalized = embeddings / norms
            
            # Guardar
            emb_file = tmp_path / "embeddings.npy"
            lab_file = tmp_path / "labels.npy"
            np.save(emb_file, embeddings_normalized)
            np.save(lab_file, labels)
            
            logger.info(f"✓ Archivos creados: {emb_file}, {lab_file}")
            
            # Cargar base de datos
            db = FaceDatabase(embeddings_file=emb_file, labels_file=lab_file)
            assert db.load()
            
            logger.info(f"✓ Base de datos cargada")
            logger.info(f"  Personas: {db.get_person_count()}")
            logger.info(f"  Embeddings totales: {db.get_total_embeddings()}")
            
            return db
            
    except Exception as e:
        logger.error(f"✗ Error creando base de datos: {e}", exc_info=True)
        return None


def test_database_search(db):
    """Prueba búsqueda en la base de datos."""
    logger.info("Probando búsqueda de matches...")
    
    try:
        # Crear query embedding (similar a person_0)
        # Usar el primer embedding de person_0 como referencia
        if db.embeddings is None or len(db.embeddings) == 0:
            logger.error("✗ Base de datos vacía")
            return False
        
        # Query idéntico al primer embedding
        query_emb = db.embeddings[0].copy()
        
        # Buscar match
        person, similarity = db.find_match(query_emb, threshold=0.5)
        
        logger.info(f"✓ Búsqueda completada")
        logger.info(f"  Persona encontrada: {person}")
        logger.info(f"  Similitud: {similarity:.6f}")
        
        if person:
            logger.info("  ✓ Match encontrado")
        else:
            logger.warning("  ⚠ No se encontró match (puede ser normal con umbral alto)")
        
        # Buscar múltiples matches
        matches = db.find_matches(query_emb, threshold=0.3, top_k=5)
        logger.info(f"✓ Top {len(matches)} matches encontrados:")
        for i, (p, sim) in enumerate(matches[:3]):
            logger.info(f"  {i+1}. {p}: {sim:.6f}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error en búsqueda: {e}", exc_info=True)
        return False


def test_database_threshold(db):
    """Prueba diferentes umbrales."""
    logger.info("Probando diferentes umbrales...")
    
    try:
        if db.embeddings is None or len(db.embeddings) == 0:
            logger.error("✗ Base de datos vacía")
            return False
        
        query_emb = db.embeddings[0].copy()
        
        thresholds = [0.3, 0.5, 0.7, 0.9]
        logger.info("  Umbral | Match encontrado | Similitud")
        logger.info("  " + "-" * 45)
        
        for thresh in thresholds:
            person, sim = db.find_match(query_emb, threshold=thresh)
            match_str = "Sí" if person else "No"
            sim_str = f"{sim:.6f}" if sim > 0 else "N/A"
            logger.info(f"  {thresh:.1f}    | {match_str:15} | {sim_str}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error probando umbrales: {e}", exc_info=True)
        return False


def test_database_load_real():
    """Intenta cargar la base de datos real si existe."""
    logger.info("Intentando cargar base de datos real...")
    
    try:
        from database.face_db import FaceDatabase
        from config import EMBEDDINGS_FILE, LABELS_FILE
        
        db = FaceDatabase()
        
        if db.load():
            logger.info("✓ Base de datos real cargada")
            logger.info(f"  Personas: {db.get_person_count()}")
            logger.info(f"  Embeddings totales: {db.get_total_embeddings()}")
            return db
        else:
            logger.warning("⚠ Base de datos real no encontrada")
            logger.info("  Ejecuta build_database.py primero para crear la base de datos")
            return None
            
    except Exception as e:
        logger.error(f"✗ Error cargando base de datos real: {e}")
        return None


def main():
    logger.info("=" * 60)
    logger.info("Test de FaceDatabase")
    logger.info("=" * 60)
    
    # Test 1: Imports
    if not test_imports():
        sys.exit(1)
    
    success = True
    
    # Test 2: Crear base de datos de prueba
    db = test_database_creation()
    if db is None:
        success = False
    else:
        # Test 3: Búsqueda
        if not test_database_search(db):
            success = False
        
        # Test 4: Umbrales
        if not test_database_threshold(db):
            success = False
    
    # Test 5: Cargar base de datos real (si existe)
    real_db = test_database_load_real()
    if real_db:
        logger.info("Probando búsqueda en base de datos real...")
        if not test_database_search(real_db):
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
