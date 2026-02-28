"""
Tests unitarios para funciones utilitarias.

Prueba funciones helper como l2_normalize y otras utilidades.
"""
import numpy as np
import pytest
from database.build_database import l2_normalize


def test_l2_normalize_basic():
    """Prueba normalización L2 básica."""
    vec = np.array([3.0, 4.0, 0.0])
    normalized = l2_normalize(vec)
    
    # Verificar norma unitaria
    norm = np.linalg.norm(normalized)
    assert abs(norm - 1.0) < 1e-10
    
    # Verificar dirección correcta
    expected = vec / np.linalg.norm(vec)
    assert np.allclose(normalized, expected)


def test_l2_normalize_zero_vector():
    """Prueba normalización de vector cero."""
    vec = np.zeros(5)
    normalized = l2_normalize(vec)
    
    # Debería manejar sin error (usando eps)
    assert not np.any(np.isnan(normalized))
    assert not np.any(np.isinf(normalized))


def test_l2_normalize_single_element():
    """Prueba normalización de vector con un solo elemento."""
    vec = np.array([5.0])
    normalized = l2_normalize(vec)
    
    assert abs(normalized[0] - 1.0) < 1e-10 or abs(normalized[0] + 1.0) < 1e-10


def test_l2_normalize_negative_values():
    """Prueba normalización con valores negativos."""
    vec = np.array([-3.0, 4.0, 0.0])
    normalized = l2_normalize(vec)
    
    norm = np.linalg.norm(normalized)
    assert abs(norm - 1.0) < 1e-10
    
    # La dirección debería preservarse
    assert normalized[0] < 0
    assert normalized[1] > 0


def test_l2_normalize_high_dimensional():
    """Prueba normalización en alta dimensionalidad."""
    vec = np.random.randn(512)  # Típico tamaño de embedding
    normalized = l2_normalize(vec)
    
    norm = np.linalg.norm(normalized)
    assert abs(norm - 1.0) < 1e-10


def test_l2_normalize_eps_parameter():
    """Prueba que el parámetro eps funciona correctamente."""
    vec = np.array([1e-15, 1e-15, 1e-15])  # Vector muy pequeño
    
    # Con eps por defecto debería funcionar
    normalized = l2_normalize(vec)
    assert not np.any(np.isnan(normalized))
    assert not np.any(np.isinf(normalized))
    
    # Con eps personalizado
    normalized_custom = l2_normalize(vec, eps=1e-10)
    assert not np.any(np.isnan(normalized_custom))


def test_l2_normalize_preserves_direction():
    """Prueba que la normalización preserva la dirección."""
    vec1 = np.array([1.0, 2.0, 3.0])
    vec2 = np.array([2.0, 4.0, 6.0])  # Múltiplo de vec1
    
    norm1 = l2_normalize(vec1)
    norm2 = l2_normalize(vec2)
    
    # Deberían tener la misma dirección (normalizados)
    assert np.allclose(norm1, norm2)


def test_l2_normalize_array_of_vectors():
    """Prueba normalización de múltiples vectores."""
    # Matriz de embeddings (N, D)
    embeddings = np.random.randn(10, 128)
    
    # Normalizar cada fila
    normalized = np.array([l2_normalize(emb) for emb in embeddings])
    
    # Verificar que cada fila tiene norma 1
    norms = np.linalg.norm(normalized, axis=1)
    assert np.allclose(norms, 1.0)


def test_l2_normalize_edge_cases():
    """Prueba casos límite de normalización."""
    # Vector con un solo valor no cero
    vec_single = np.array([0.0, 0.0, 5.0])
    norm_single = l2_normalize(vec_single)
    assert abs(norm_single[2] - 1.0) < 1e-10
    
    # Vector muy grande
    vec_large = np.array([1e10, 1e10, 0.0])
    norm_large = l2_normalize(vec_large)
    norm_check = np.linalg.norm(norm_large)
    assert abs(norm_check - 1.0) < 1e-5  # Tolerancia más amplia para valores grandes
    
    # Vector muy pequeño pero no cero
    vec_tiny = np.array([1e-10, 1e-10, 1e-10])
    norm_tiny = l2_normalize(vec_tiny)
    assert not np.any(np.isnan(norm_tiny))
    assert not np.any(np.isinf(norm_tiny))
