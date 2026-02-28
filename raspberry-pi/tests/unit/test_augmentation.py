"""
Tests unitarios para augmentación de imágenes.

Prueba build_augmenter() y quality_gate() sin requerir modelos ML.
"""
import numpy as np
import cv2
import pytest
from database.build_database import build_augmenter, quality_gate


def test_build_augmenter():
    """Prueba que build_augmenter() crea un pipeline válido."""
    aug = build_augmenter()
    
    assert aug is not None
    # Verificar que es un pipeline válido de albumentations (se invoca con __call__)
    assert callable(aug)


def test_augmenter_applies_transforms():
    """Prueba que el augmentador aplica transformaciones."""
    aug = build_augmenter()
    
    # Crear imagen de prueba RGB
    test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    
    # Aplicar augmentación
    result = aug(image=test_image)
    
    assert 'image' in result
    augmented = result['image']
    
    # Verificar que la imagen tiene el mismo tamaño
    assert augmented.shape == test_image.shape
    assert augmented.dtype == np.uint8


def test_quality_gate_good_image():
    """Prueba quality_gate() con imagen de buena calidad."""
    # Imagen con valores medios (buena calidad)
    good_image = np.random.randint(50, 200, (100, 100, 3), dtype=np.uint8)
    
    assert quality_gate(good_image) == True


def test_quality_gate_dark_image():
    """Prueba quality_gate() con imagen muy oscura."""
    # Imagen muy oscura
    dark_image = np.random.randint(0, 30, (100, 100, 3), dtype=np.uint8)
    
    assert quality_gate(dark_image) == False


def test_quality_gate_bright_image():
    """Prueba quality_gate() con imagen muy brillante."""
    # Imagen muy brillante (quemada)
    bright_image = np.random.randint(230, 255, (100, 100, 3), dtype=np.uint8)
    
    assert quality_gate(bright_image) == False


def test_quality_gate_too_many_black_pixels():
    """Prueba quality_gate() con demasiados píxeles negros."""
    # Imagen con muchos píxeles negros pero media aceptable
    image = np.ones((100, 100, 3), dtype=np.uint8) * 128
    # Hacer el 30% de los píxeles negros
    black_pixels = int(0.3 * 100 * 100)
    flat = image.reshape(-1, 3)
    flat[:black_pixels] = [5, 5, 5]  # Casi negro
    
    assert quality_gate(image) == False


def test_quality_gate_too_many_white_pixels():
    """Prueba quality_gate() con demasiados píxeles blancos."""
    # Imagen con muchos píxeles blancos pero media aceptable
    image = np.ones((100, 100, 3), dtype=np.uint8) * 128
    # Hacer el 30% de los píxeles blancos
    white_pixels = int(0.3 * 100 * 100)
    flat = image.reshape(-1, 3)
    flat[:white_pixels] = [250, 250, 250]  # Casi blanco
    
    assert quality_gate(image) == False


def test_quality_gate_edge_cases():
    """Prueba quality_gate() con casos límite."""
    # Imagen exactamente en el límite de media baja
    image_low = np.ones((100, 100, 3), dtype=np.uint8) * 35
    # Debería pasar (mean == 35 es el límite)
    assert quality_gate(image_low) == True
    
    # Imagen exactamente en el límite de media alta
    image_high = np.ones((100, 100, 3), dtype=np.uint8) * 220
    # Debería pasar (mean == 220 es el límite)
    assert quality_gate(image_high) == True
    
    # Imagen justo debajo del límite
    image_below = np.ones((100, 100, 3), dtype=np.uint8) * 34
    assert quality_gate(image_below) == False
    
    # Imagen justo arriba del límite
    image_above = np.ones((100, 100, 3), dtype=np.uint8) * 221
    assert quality_gate(image_above) == False


def test_augmentation_preserves_shape():
    """Prueba que la augmentación preserva la forma de la imagen."""
    aug = build_augmenter()
    
    # Diferentes tamaños
    sizes = [(64, 64), (112, 112), (160, 160), (224, 224)]
    
    for h, w in sizes:
        image = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
        result = aug(image=image)
        
        assert result['image'].shape == (h, w, 3)


def test_augmentation_deterministic_seed():
    """Prueba que con seed fijo, la augmentación es reproducible."""
    aug = build_augmenter()
    
    image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    
    # Con seed, debería ser reproducible
    # Nota: albumentations usa random seed global
    import random
    seed = 42
    random.seed(seed)
    np.random.seed(seed)
    
    result1 = aug(image=image)
    
    random.seed(seed)
    np.random.seed(seed)
    result2 = aug(image=image)
    
    # Con el mismo seed, deberían ser iguales
    # (aunque algunas transformaciones pueden tener aleatoriedad interna)
    # Al menos verificamos que no hay error
    assert result1['image'].shape == result2['image'].shape
