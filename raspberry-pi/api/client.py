"""
Cliente API para comunicación con el backend.

Maneja la subida de videos y la creación de alertas.
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import requests

from config import API_BASE_URL, API_TIMEOUT_SECONDS
from api.auth import APIAuth

logger = logging.getLogger(__name__)


class GateLockAPI:
    """
    Cliente para interactuar con la API del backend.
    
    Maneja autenticación automática y operaciones de API.
    """
    
    def __init__(self, base_url: str = API_BASE_URL, auth: Optional[APIAuth] = None):
        """
        Inicializa el cliente API.
        
        Args:
            base_url: URL base de la API
            auth: Instancia de APIAuth. Si es None, crea una nueva
        """
        self.base_url = base_url.rstrip('/')
        self.auth = auth or APIAuth(base_url=base_url)
    
    def _get_headers(self) -> Dict[str, str]:
        """Obtiene headers con autenticación."""
        token = self.auth.get_token()
        if not token:
            raise ValueError("No hay token de autenticación. Llama a login() primero.")
        
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def upload_video(self, video_path: Path) -> Optional[str]:
        """
        Sube un archivo de video al backend.
        
        Args:
            video_path: Ruta al archivo de video
            
        Returns:
            URL del video subido o None si falló
        """
        if not Path(video_path).exists():
            logger.error(f"Archivo de video no encontrado: {video_path}")
            return None
        
        try:
            url = f"{self.base_url}/videos/upload"
            
            # Preparar archivo para subida
            with open(video_path, 'rb') as video_file:
                files = {'video': (video_path.name, video_file, 'video/mp4')}
                
                # Headers sin Content-Type (requests lo maneja automáticamente para multipart)
                headers = {"Authorization": f"Bearer {self.auth.get_token()}"}
                
                upload_timeout = max(60, API_TIMEOUT_SECONDS * 2)  # Subida de video requiere más tiempo
                response = requests.post(
                    url,
                    files=files,
                    headers=headers,
                    timeout=upload_timeout
                )
            
            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                video_url = data.get("videoUrl")
                logger.info(f"Video subido exitosamente: {video_url}")
                return video_url
            elif response.status_code == 401:
                logger.warning("Token inválido o expirado (401). Se requiere nuevo login.")
                self.auth.logout()
                logger.error(f"Error al subir video: {response.status_code} - {response.text}")
                return None
            else:
                logger.error(f"Error al subir video: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión al subir video: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al subir video: {e}")
            return None
    
    def create_alert(
        self,
        person_name: str,
        video_url: str,
        message: str,
        person_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Crea una alerta en el backend.
        
        Args:
            person_name: Nombre de la persona detectada
            video_url: URL del video asociado
            message: Mensaje de la alerta
            person_id: ID de la persona (opcional)
            
        Returns:
            Datos de la alerta creada o None si falló
        """
        try:
            url = f"{self.base_url}/alerts"
            
            payload = {
                "personName": person_name,
                "videoUrl": video_url,
                "message": message
            }
            
            if person_id:
                payload["personId"] = person_id
            
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=API_TIMEOUT_SECONDS
            )
            
            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                alert = data.get("alert")
                logger.info(f"Alerta creada exitosamente: {alert.get('id')}")
                return alert
            elif response.status_code == 401:
                logger.warning("Token inválido o expirado (401). Se requiere nuevo login.")
                self.auth.logout()
                logger.error(f"Error al crear alerta: {response.status_code} - {response.text}")
                return None
            else:
                logger.error(f"Error al crear alerta: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión al crear alerta: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al crear alerta: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Prueba la conexión con el backend.
        
        Returns:
            True si la conexión es exitosa, False en caso contrario
        """
        try:
            url = f"{self.base_url}/health"
            response = requests.get(url, timeout=API_TIMEOUT_SECONDS)
            return response.status_code == 200
        except Exception:
            return False
