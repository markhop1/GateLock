"""
Tests unitarios para la lógica de FaceDatabase.

Prueba normalización, similitud coseno y búsqueda sin requerir archivos reales.
"""
import numpy as np
import pytest
import tempfile
from pathlib import Path
from database.face_db import FaceDatabase


def l2_normalize(x: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    """Función helper para normalización L2."""
    return x / (np.linalg.norm(x) + eps)


def test_l2_normalization():
    """Prueba normalización L2."""
    # Vector de prueba
    vec = np.array([3.0, 4.0, 0.0])
    normalized = l2_normalize(vec)
    
    # Verificar que tiene norma 1
    norm = np.linalg.norm(normalized)
    assert abs(norm - 1.0) < 1e-10
    
    # Verificar dirección (proporcional al original)
    assert np.allclose(normalized[:2], vec[:2] / 5.0)


def test_l2_normalize_zero_vector():
    """Prueba normalización de vector cero."""
    vec = np.array([0.0, 0.0, 0.0])
    normalized = l2_normalize(vec)
    
    # Debería manejar vector cero sin error
    assert not np.any(np.isnan(normalized))
    assert not np.any(np.isinf(normalized))


def test_cosine_similarity():
    """Prueba cálculo de similitud coseno."""
    # Vectores normalizados
    vec1 = np.array([1.0, 0.0, 0.0])
    vec2 = np.array([0.0, 1.0, 0.0])
    vec3 = np.array([1.0, 0.0, 0.0])  # Igual a vec1
    
    # Similitud coseno = producto punto para vectores normalizados
    sim_orthogonal = np.dot(vec1, vec2)
    sim_same = np.dot(vec1, vec3)
    
    assert abs(sim_orthogonal) < 1e-10  # Ortogonales
    assert abs(sim_same - 1.0) < 1e-10  # Idénticos


def test_face_database_find_match():
    """Prueba búsqueda de matches con datos sintéticos."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Crear embeddings y labels de prueba
        embeddings = np.array([
            [1.0, 0.0, 0.0],  # Persona 1
            [0.0, 1.0, 0.0],  # Persona 2
            [0.0, 0.0, 1.0],  # Persona 3
        ])
        labels = np.array(['person1', 'person2', 'person3'])
        
        # Normalizar embeddings
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings_normalized = embeddings / norms
        
        # Guardar archivos temporales
        emb_file = tmp_path / "embeddings.npy"
        lab_file = tmp_path / "labels.npy"
        np.save(emb_file, embeddings_normalized)
        np.save(lab_file, labels)
        
        # Crear base de datos y cargar
        db = FaceDatabase(embeddings_file=emb_file, labels_file=lab_file)
        assert db.load()
        
        # Buscar match con embedding idéntico
        query_emb = np.array([1.0, 0.0, 0.0])
        person, sim = db.find_match(query_emb, threshold=0.5)
        
        assert person == 'person1'
        assert sim >= 0.5
        
        # Buscar match con embedding diferente (no debería encontrar)
        query_emb2 = np.array([0.5, 0.5, 0.0])
        person2, sim2 = db.find_match(query_emb2, threshold=0.9)
        
        # Con umbral alto, no debería encontrar match
        assert person2 is None or sim2 < 0.9


def test_face_database_find_matches():
    """Prueba búsqueda de múltiples matches."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Crear embeddings de prueba
        embeddings = np.array([
            [1.0, 0.0, 0.0],
            [0.9, 0.1, 0.0],  # Similar a [1,0,0]
            [0.0, 1.0, 0.0],
        ])
        labels = np.array(['person1', 'person1_variant', 'person2'])
        
        # Normalizar
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings_normalized = embeddings / norms
        
        # Guardar
        emb_file = tmp_path / "embeddings.npy"
        lab_file = tmp_path / "labels.npy"
        np.save(emb_file, embeddings_normalized)
        np.save(lab_file, labels)
        
        # Cargar y buscar
        db = FaceDatabase(embeddings_file=emb_file, labels_file=lab_file)
        db.load()
        
        query_emb = np.array([1.0, 0.0, 0.0])
        matches = db.find_matches(query_emb, threshold=0.5, top_k=3)
        
        assert len(matches) >= 1
        # El primer match debería ser el más similar
        assert matches[0][0] in ['person1', 'person1_variant']


def test_face_database_empty_embedding():
    """Prueba manejo de embedding vacío."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        embeddings = np.array([[1.0, 0.0], [0.0, 1.0]])
        labels = np.array(['p1', 'p2'])
        
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings_normalized = embeddings / norms
        
        emb_file = tmp_path / "embeddings.npy"
        lab_file = tmp_path / "labels.npy"
        np.save(emb_file, embeddings_normalized)
        np.save(lab_file, labels)
        
        db = FaceDatabase(embeddings_file=emb_file, labels_file=lab_file)
        db.load()
        
        # Embedding vacío
        empty_emb = np.array([])
        person, sim = db.find_match(empty_emb)
        
        assert person is None
        assert sim == 0.0


def test_face_database_zero_embedding():
    """Prueba manejo de embedding con todos ceros."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        embeddings = np.array([[1.0, 0.0], [0.0, 1.0]])
        labels = np.array(['p1', 'p2'])
        
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings_normalized = embeddings / norms
        
        emb_file = tmp_path / "embeddings.npy"
        lab_file = tmp_path / "labels.npy"
        np.save(emb_file, embeddings_normalized)
        np.save(lab_file, labels)
        
        db = FaceDatabase(embeddings_file=emb_file, labels_file=lab_file)
        db.load()
        
        # Embedding cero
        zero_emb = np.array([0.0, 0.0])
        person, sim = db.find_match(zero_emb)
        
        assert person is None
        assert sim == 0.0


def test_face_database_threshold():
    """Prueba que el umbral funciona correctamente."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        embeddings = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ])
        labels = np.array(['person1', 'person2'])
        
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings_normalized = embeddings / norms
        
        emb_file = tmp_path / "embeddings.npy"
        lab_file = tmp_path / "labels.npy"
        np.save(emb_file, embeddings_normalized)
        np.save(lab_file, labels)
        
        db = FaceDatabase(embeddings_file=emb_file, labels_file=lab_file)
        db.load()
        
        # Query: [0.6, 0.4, 0] tiene similitud coseno ~0.83 con [1,0,0]
        # Con threshold 0.5 encuentra, con 0.99 no
        query = np.array([0.6, 0.4, 0.0])
        
        # Con umbral bajo, debería encontrar
        person_low, sim_low = db.find_match(query, threshold=0.5)
        assert person_low is not None
        
        # Con umbral muy alto, no debería encontrar
        person_high, sim_high = db.find_match(query, threshold=0.99)
        assert person_high is None
