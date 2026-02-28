#!/usr/bin/env python3
"""
Script de prueba para autenticación API.

Prueba login, guardado/carga de tokens y manejo de errores.
"""
import argparse
import sys
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_imports():
    """Verifica que se pueden importar las dependencias."""
    try:
        from api.auth import APIAuth
        logger.info("✓ Imports exitosos")
        return True
    except ImportError as e:
        logger.error(f"✗ Error de import: {e}")
        return False


def test_auth_initialization():
    """Prueba inicialización del cliente de autenticación."""
    try:
        from api.auth import APIAuth
        
        logger.info("Inicializando APIAuth...")
        auth = APIAuth()
        
        logger.info("✓ APIAuth inicializado")
        logger.info(f"  Base URL: {auth.base_url}")
        logger.info(f"  Token cache: {auth.token_cache_file}")
        
        return auth
    except Exception as e:
        logger.error(f"✗ Error inicializando APIAuth: {e}", exc_info=True)
        return None


def test_token_cache(auth):
    """Prueba guardado y carga de tokens en caché."""
    logger.info("Probando caché de tokens...")
    
    try:
        # Limpiar caché existente
        if auth.token_cache_file.exists():
            auth.token_cache_file.unlink()
        
        # Simular token
        auth._token = "test_token_12345"
        auth._token_expires_at = 9999999999.0  # Muy lejano en el futuro
        
        # Guardar en caché
        auth._save_token_cache()
        logger.info("✓ Token guardado en caché")
        
        # Limpiar de memoria
        auth._token = None
        auth._token_expires_at = None
        
        # Cargar desde caché
        auth._load_token_cache()
        
        if auth._token == "test_token_12345":
            logger.info("✓ Token cargado desde caché correctamente")
        else:
            logger.error(f"✗ Token incorrecto: {auth._token}")
            return False
        
        # Limpiar
        auth.logout()
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error probando caché: {e}", exc_info=True)
        return False


def test_login_real(auth):
    """Prueba login real con el backend."""
    logger.info("Probando login real...")
    
    try:
        from config import API_USERNAME, API_PASSWORD
        
        if not API_USERNAME or not API_PASSWORD:
            logger.warning("⚠ Credenciales no configuradas (API_USERNAME, API_PASSWORD)")
            logger.info("  Saltando test de login real")
            return None
        
        logger.info(f"Intentando login con email: {API_USERNAME}")
        
        if auth.login(API_USERNAME, API_PASSWORD):
            logger.info("✓ Login exitoso")
            
            token = auth.get_token()
            if token:
                logger.info(f"✓ Token obtenido: {token[:20]}...")
                return True
            else:
                logger.error("✗ No se pudo obtener el token después del login")
                return False
        else:
            logger.error("✗ Login falló")
            logger.error("  Verifica que el backend esté corriendo y las credenciales sean correctas")
            return False
            
    except Exception as e:
        logger.error(f"✗ Error en login: {e}", exc_info=True)
        return False


def test_token_validation(auth):
    """Prueba validación de tokens."""
    logger.info("Probando validación de tokens...")
    
    try:
        # Token válido
        auth._token = "valid_token"
        auth._token_expires_at = 9999999999.0
        
        if auth.is_authenticated():
            logger.info("✓ Token válido detectado correctamente")
        else:
            logger.error("✗ Token válido no detectado")
            return False
        
        # Token expirado
        import time
        auth._token_expires_at = time.time() - 100  # Expirado hace 100 segundos
        
        if not auth.is_authenticated():
            logger.info("✓ Token expirado detectado correctamente")
        else:
            logger.error("✗ Token expirado no detectado")
            return False
        
        # Sin token
        auth._token = None
        auth._token_expires_at = None
        
        if not auth.is_authenticated():
            logger.info("✓ Ausencia de token detectada correctamente")
        else:
            logger.error("✗ Ausencia de token no detectada")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error validando tokens: {e}", exc_info=True)
        return False


def main():
    parser = argparse.ArgumentParser(description="Prueba autenticación API")
    parser.add_argument(
        '--skip-login',
        action='store_true',
        help='Saltar test de login real'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Test de Autenticación API")
    logger.info("=" * 60)
    
    # Test 1: Imports
    if not test_imports():
        sys.exit(1)
    
    # Test 2: Inicialización
    auth = test_auth_initialization()
    if auth is None:
        sys.exit(1)
    
    success = True
    
    # Test 3: Caché de tokens
    if not test_token_cache(auth):
        success = False
    
    # Test 4: Validación de tokens
    if not test_token_validation(auth):
        success = False
    
    # Test 5: Login real (opcional)
    if not args.skip_login:
        login_result = test_login_real(auth)
        if login_result is False:
            success = False
    else:
        logger.info("Saltando test de login real (--skip-login)")
    
    logger.info("=" * 60)
    if success:
        logger.info("✓ Todos los tests pasaron")
        sys.exit(0)
    else:
        logger.error("✗ Algunos tests fallaron")
        sys.exit(1)


if __name__ == "__main__":
    main()
