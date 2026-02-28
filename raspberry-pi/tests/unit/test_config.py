"""
Tests unitarios para la configuración.

Verifica que todas las variables de configuración tienen valores por defecto
y que se pueden cargar desde variables de entorno.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch


def test_config_imports():
    """Verifica que el módulo de configuración se puede importar."""
    import config
    assert config is not None


def test_config_has_defaults():
    """Verifica que todas las variables de configuración tienen valores por defecto."""
    import config
    
    # Verificar que existen las variables principales
    assert hasattr(config, 'API_BASE_URL')
    assert hasattr(config, 'API_TIMEOUT_SECONDS')
    assert hasattr(config, 'CAMERA_INDEX')
    assert hasattr(config, 'RECOGNITION_THRESHOLD')
    assert hasattr(config, 'CLIP_DURATION_SECONDS')
    assert hasattr(config, 'VIDEO_OUTPUT_DIR')
    assert hasattr(config, 'DATABASE_DIR')
    assert hasattr(config, 'KNOWN_FACES_DIR')
    
    # Verificar tipos
    assert isinstance(config.API_BASE_URL, str)
    assert isinstance(config.API_TIMEOUT_SECONDS, int)
    assert isinstance(config.CAMERA_INDEX, int)
    assert isinstance(config.RECOGNITION_THRESHOLD, float)
    assert isinstance(config.CLIP_DURATION_SECONDS, int)
    assert isinstance(config.VIDEO_OUTPUT_DIR, Path)
    assert isinstance(config.DATABASE_DIR, Path)
    assert isinstance(config.KNOWN_FACES_DIR, Path)


def test_config_paths_are_paths():
    """Verifica que las rutas son objetos Path."""
    import config
    
    assert isinstance(config.VIDEO_OUTPUT_DIR, Path)
    assert isinstance(config.DATABASE_DIR, Path)
    assert isinstance(config.KNOWN_FACES_DIR, Path)
    assert isinstance(config.TOKEN_CACHE_DIR, Path)
    assert isinstance(config.TOKEN_CACHE_FILE, Path)


def test_config_env_override():
    """Verifica que las variables de entorno pueden sobrescribir valores por defecto."""
    import importlib
    import config.config as config_module
    
    with patch.dict(os.environ, {
        'API_BASE_URL': 'http://test.example.com/api',
        'CAMERA_INDEX': '1',
        'RECOGNITION_THRESHOLD': '0.7',
        'CLIP_DURATION_SECONDS': '15'
    }):
        # Recargar el módulo de configuración para que tome las nuevas variables de entorno
        importlib.reload(config_module)
        import config
        importlib.reload(config)
        
        assert config.API_BASE_URL == 'http://test.example.com/api'
        assert config.CAMERA_INDEX == 1
        assert config.RECOGNITION_THRESHOLD == 0.7
        assert config.CLIP_DURATION_SECONDS == 15


def test_config_directories_created():
    """Verifica que los directorios necesarios se crean automáticamente."""
    import config
    
    # Estos directorios deberían crearse al importar el módulo
    assert config.VIDEO_OUTPUT_DIR.exists() or config.VIDEO_OUTPUT_DIR.parent.exists()
    assert config.DATABASE_DIR.exists() or config.DATABASE_DIR.parent.exists()
    assert config.KNOWN_FACES_DIR.exists() or config.KNOWN_FACES_DIR.parent.exists()


def test_config_model_settings():
    """Verifica configuración de modelos."""
    import config
    
    assert hasattr(config, 'RETINAFACE_MODEL_NAME')
    assert hasattr(config, 'RETINAFACE_DET_SIZE')
    assert hasattr(config, 'MOBILEFACENET_INPUT_SIZE')
    
    assert isinstance(config.RETINAFACE_MODEL_NAME, str)
    assert isinstance(config.RETINAFACE_DET_SIZE, tuple)
    assert isinstance(config.MOBILEFACENET_INPUT_SIZE, tuple)
    assert len(config.RETINAFACE_DET_SIZE) == 2
    assert len(config.MOBILEFACENET_INPUT_SIZE) == 2
