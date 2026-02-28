#!/usr/bin/env python3
"""
Script de prueba para cliente API.

Prueba subida de videos y creación de alertas usando mock server o backend real.
"""
import argparse
import sys
import tempfile
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_imports():
    """Verifica que se pueden importar las dependencias."""
    try:
        from api.client import GateLockAPI
        from api.auth import APIAuth
        logger.info("✓ Imports exitosos")
        return True
    except ImportError as e:
        logger.error(f"✗ Error de import: {e}")
        return False


def test_client_initialization():
    """Prueba inicialización del cliente API."""
    try:
        from api.client import GateLockAPI
        from api.auth import APIAuth
        
        logger.info("Inicializando GateLockAPI...")
        auth = APIAuth()
        api = GateLockAPI(auth=auth)
        
        logger.info("✓ GateLockAPI inicializado")
        logger.info(f"  Base URL: {api.base_url}")
        
        return api
    except Exception as e:
        logger.error(f"✗ Error inicializando cliente: {e}", exc_info=True)
        return None


def test_connection(api):
    """Prueba conexión con el backend."""
    logger.info("Probando conexión con backend...")
    
    try:
        if api.test_connection():
            logger.info("✓ Conexión exitosa con backend")
            return True
        else:
            logger.warning("⚠ No se pudo conectar con el backend")
            logger.info("  Asegúrate de que el backend esté corriendo")
            return False
    except Exception as e:
        logger.error(f"✗ Error probando conexión: {e}")
        return False


def test_video_upload_mock(api):
    """Prueba subida de video usando mock."""
    logger.info("Probando subida de video (mock)...")
    
    try:
        import responses
        
        # Crear archivo de video de prueba pequeño
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            # Escribir algunos bytes (simulando video)
            tmp.write(b'fake video content' * 100)
            tmp_path = Path(tmp.name)
        
        # Mock de respuesta
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                f"{api.base_url}/videos/upload",
                json={"videoUrl": "/uploads/videos/test123.mp4"},
                status=201
            )
            
            # Mock del token
            api.auth._token = "mock_token"
            api.auth._token_expires_at = 9999999999.0
            
            video_url = api.upload_video(tmp_path)
            
            if video_url:
                logger.info(f"✓ Video subido (mock): {video_url}")
                tmp_path.unlink()
                return True
            else:
                logger.error("✗ Subida de video falló (mock)")
                tmp_path.unlink()
                return False
                
    except ImportError:
        logger.warning("⚠ responses no disponible, saltando test mock")
        logger.info("  Instala con: pip install responses")
        return None
    except Exception as e:
        logger.error(f"✗ Error en test mock: {e}", exc_info=True)
        if 'tmp_path' in locals():
            tmp_path.unlink()
        return False


def test_video_upload_real(api):
    """Prueba subida de video real."""
    logger.info("Probando subida de video real...")
    
    try:
        # Verificar autenticación
        if not api.auth.is_authenticated():
            logger.warning("⚠ No hay token de autenticación")
            logger.info("  Ejecuta test_api_auth.py primero o configura credenciales")
            return None
        
        # Crear archivo de video de prueba pequeño
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            # Escribir algunos bytes
            tmp.write(b'fake video content' * 100)
            tmp_path = Path(tmp.name)
        
        logger.info(f"Subiendo archivo de prueba: {tmp_path}")
        video_url = api.upload_video(tmp_path)
        
        if video_url:
            logger.info(f"✓ Video subido exitosamente: {video_url}")
            tmp_path.unlink()
            return True
        else:
            logger.error("✗ Subida de video falló")
            tmp_path.unlink()
            return False
            
    except Exception as e:
        logger.error(f"✗ Error subiendo video: {e}", exc_info=True)
        if 'tmp_path' in locals():
            tmp_path.unlink()
        return False


def test_create_alert_mock(api):
    """Prueba creación de alerta usando mock."""
    logger.info("Probando creación de alerta (mock)...")
    
    try:
        import responses
        
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                f"{api.base_url}/alerts",
                json={
                    "alert": {
                        "id": "test_alert_123",
                        "personName": "Test Person",
                        "videoUrl": "/uploads/videos/test.mp4",
                        "message": "Test alert",
                        "status": "pending"
                    }
                },
                status=201
            )
            
            api.auth._token = "mock_token"
            api.auth._token_expires_at = 9999999999.0
            
            alert = api.create_alert(
                person_name="Test Person",
                video_url="/uploads/videos/test.mp4",
                message="Test alert"
            )
            
            if alert:
                logger.info(f"✓ Alerta creada (mock): {alert.get('id')}")
                return True
            else:
                logger.error("✗ Creación de alerta falló (mock)")
                return False
                
    except ImportError:
        logger.warning("⚠ responses no disponible, saltando test mock")
        return None
    except Exception as e:
        logger.error(f"✗ Error en test mock: {e}", exc_info=True)
        return False


def test_create_alert_real(api):
    """Prueba creación de alerta real."""
    logger.info("Probando creación de alerta real...")
    
    try:
        if not api.auth.is_authenticated():
            logger.warning("⚠ No hay token de autenticación")
            return None
        
        alert = api.create_alert(
            person_name="Test Person",
            video_url="/uploads/videos/test.mp4",
            message="Test alert from test script"
        )
        
        if alert:
            logger.info(f"✓ Alerta creada exitosamente: {alert.get('id')}")
            return True
        else:
            logger.error("✗ Creación de alerta falló")
            return False
            
    except Exception as e:
        logger.error(f"✗ Error creando alerta: {e}", exc_info=True)
        return False


def main():
    parser = argparse.ArgumentParser(description="Prueba cliente API")
    parser.add_argument(
        '--mock',
        action='store_true',
        help='Usar solo tests mock (no requiere backend)'
    )
    parser.add_argument(
        '--real-backend',
        action='store_true',
        help='Probar con backend real'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Test de Cliente API")
    logger.info("=" * 60)
    
    # Test 1: Imports
    if not test_imports():
        sys.exit(1)
    
    # Test 2: Inicialización
    api = test_client_initialization()
    if api is None:
        sys.exit(1)
    
    success = True
    
    # Test 3: Conexión (si no es solo mock)
    if not args.mock:
        if not test_connection(api):
            logger.warning("⚠ Backend no disponible, algunos tests pueden fallar")
    
    # Test 4: Subida de video (mock)
    if args.mock or not args.real_backend:
        result = test_video_upload_mock(api)
        if result is False:
            success = False
    
    # Test 5: Subida de video (real)
    if args.real_backend:
        result = test_video_upload_real(api)
        if result is False:
            success = False
    
    # Test 6: Crear alerta (mock)
    if args.mock or not args.real_backend:
        result = test_create_alert_mock(api)
        if result is False:
            success = False
    
    # Test 7: Crear alerta (real)
    if args.real_backend:
        result = test_create_alert_real(api)
        if result is False:
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
