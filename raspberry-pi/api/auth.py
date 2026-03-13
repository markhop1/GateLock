"""
Autenticación JWT con el backend.

Maneja el login y el almacenamiento de tokens en caché local.
"""
import json
import time
import logging
from pathlib import Path
from typing import Optional
import requests

from config import API_BASE_URL, API_TIMEOUT_SECONDS, TOKEN_CACHE_FILE, TOKEN_CACHE_DIR

logger = logging.getLogger(__name__)


class APIAuth:
    """
    Maneja la autenticación JWT con el backend.
    
    Guarda tokens en caché local para evitar logins repetidos.
    """
    
    def __init__(self, base_url: str = API_BASE_URL, token_cache_file: Path = TOKEN_CACHE_FILE):
        """
        Inicializa el cliente de autenticación.
        
        Args:
            base_url: URL base de la API
            token_cache_file: Archivo donde guardar el token en caché
        """
        self.base_url = base_url.rstrip('/')
        self.token_cache_file = Path(token_cache_file)
        self.token_cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        self._token: Optional[str] = None
        self._token_expires_at: Optional[float] = None
    
    def login(self, email: str, password: str) -> bool:
        """
        Inicia sesión y obtiene un token JWT.
        
        Args:
            email: Email del usuario (el backend usa email, no username)
            password: Contraseña
            
        Returns:
            True si el login fue exitoso, False en caso contrario
        """
        try:
            url = f"{self.base_url}/auth/login"
            response = requests.post(
                url,
                json={"email": email, "password": password},
                timeout=API_TIMEOUT_SECONDS
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("token")
                
                if token:
                    self._token = token
                    # Intentar obtener expiración del token (si está en la respuesta)
                    expires_in = data.get("expiresIn", 7 * 24 * 60 * 60)  # Default 7 días
                    self._token_expires_at = time.time() + expires_in
                    
                    # Guardar en caché
                    self._save_token_cache()
                    logger.info("Login exitoso")
                    return True
                else:
                    logger.error("Token no recibido en la respuesta")
                    return False
            else:
                logger.error(f"Error en login: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión durante login: {e}")
            return False
    
    def get_token(self) -> Optional[str]:
        """
        Obtiene un token válido.
        
        Si el token está expirado o no existe, retorna None.
        El usuario debe llamar a login() primero.
        
        Returns:
            Token JWT o None si no hay token válido
        """
        # Cargar desde caché si no está en memoria
        if self._token is None:
            self._load_token_cache()
        
        # Verificar expiración
        if self._token and self._token_expires_at:
            if time.time() >= self._token_expires_at:
                logger.warning("Token expirado")
                self._token = None
                self._token_expires_at = None
                return None
        
        return self._token
    
    def is_authenticated(self) -> bool:
        """Verifica si hay un token válido."""
        token = self.get_token()
        return token is not None
    
    def logout(self):
        """Cierra sesión y limpia el token."""
        self._token = None
        self._token_expires_at = None
        
        # Eliminar caché
        if self.token_cache_file.exists():
            self.token_cache_file.unlink()
            logger.info("Token eliminado de caché")
    
    def _save_token_cache(self):
        """Guarda el token en caché local."""
        try:
            cache_data = {
                "token": self._token,
                "expires_at": self._token_expires_at
            }
            
            with open(self.token_cache_file, 'w') as f:
                json.dump(cache_data, f)
            
            logger.debug(f"Token guardado en caché: {self.token_cache_file}")
            
        except Exception as e:
            logger.warning(f"Error al guardar token en caché: {e}")
    
    def _load_token_cache(self):
        """Carga el token desde caché local."""
        if not self.token_cache_file.exists():
            return
        
        try:
            with open(self.token_cache_file, 'r') as f:
                cache_data = json.load(f)
            
            self._token = cache_data.get("token")
            self._token_expires_at = cache_data.get("expires_at")
            
            # Verificar si está expirado
            if self._token_expires_at and time.time() >= self._token_expires_at:
                logger.info("Token en caché está expirado. Eliminando caché.")
                self._token = None
                self._token_expires_at = None
                self.token_cache_file.unlink(missing_ok=True)
                return
            
            logger.debug("Token cargado desde caché")
            
        except Exception as e:
            logger.warning(f"Error al cargar token desde caché: {e}")
            self._token = None
            self._token_expires_at = None
