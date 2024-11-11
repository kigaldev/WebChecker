"""
Validators
---------
Proporciona funciones de validación para URLs y otras utilidades.
"""

import re
from typing import Optional, Tuple
from urllib.parse import urlparse
import socket
import logging

class URLValidator:
    """Clase para validar URLs y proporcionar información sobre ellas."""
    
    def __init__(self):
        """Inicializa el validador con expresiones regulares y configuración."""
        # Expresión regular para validar URLs
        self.url_pattern = re.compile(
            r'^(?:http|ftp)s?://'  # http:// o https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # dominio
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # puerto opcional
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        self.logger = logging.getLogger(__name__)
    
    def is_valid_url(self, url: str) -> bool:
        """
        Verifica si una URL es válida.
        
        Args:
            url (str): URL a validar

        Returns:
            bool: True si la URL es válida, False en caso contrario
        """
        try:
            if not url:
                return False
                
            # Agregar protocolo si no está presente
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Validar formato con regex
            if not self.url_pattern.match(url):
                return False
            
            # Validar parsing de la URL
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error validando URL {url}: {str(e)}")
            return False
    
    def get_url_info(self, url: str) -> Optional[dict]:
        """
        Obtiene información detallada sobre una URL.
        
        Args:
            url (str): URL a analizar

        Returns:
            Optional[dict]: Diccionario con información de la URL o None si es inválida
        """
        try:
            if not self.is_valid_url(url):
                return None
                
            parsed = urlparse(url)
            
            return {
                'scheme': parsed.scheme,
                'domain': parsed.netloc,
                'path': parsed.path,
                'query': parsed.query,
                'fragment': parsed.fragment,
                'port': parsed.port or (443 if parsed.scheme == 'https' else 80)
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo información de URL {url}: {str(e)}")
            return None
    
    def normalize_url(self, url: str) -> str:
        """
        Normaliza una URL agregando el protocolo si es necesario.
        
        Args:
            url (str): URL a normalizar

        Returns:
            str: URL normalizada
        """
        if not url.startswith(('http://', 'https://')):
            return 'https://' + url
        return url
    
    def get_domain_info(self, url: str) -> Optional[dict]:
        """
        Obtiene información sobre el dominio de una URL.
        
        Args:
            url (str): URL para extraer información del dominio

        Returns:
            Optional[dict]: Diccionario con información del dominio o None si es inválida
        """
        try:
            if not self.is_valid_url(url):
                return None
                
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # Obtener IP del dominio
            try:
                ip = socket.gethostbyname(domain)
            except socket.gaierror:
                ip = None
            
            # Dividir el dominio en sus partes
            parts = domain.split('.')
            
            return {
                'domain': domain,
                'ip': ip,
                'tld': parts[-1] if len(parts) > 1 else None,
                'subdomain': '.'.join(parts[:-2]) if len(parts) > 2 else None,
                'domain_name': parts[-2] if len(parts) > 1 else parts[0]
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo información del dominio {url}: {str(e)}")
            return None
    
    def is_secure_url(self, url: str) -> Tuple[bool, str]:
        """
        Verifica si una URL utiliza HTTPS.
        
        Args:
            url (str): URL a verificar

        Returns:
            Tuple[bool, str]: (es_segura, razón)
        """
        try:
            if not self.is_valid_url(url):
                return False, "URL inválida"
                
            parsed = urlparse(url)
            
            if parsed.scheme == 'https':
                return True, "La URL utiliza HTTPS"
            elif parsed.scheme == 'http':
                return False, "La URL utiliza HTTP inseguro"
            else:
                return False, f"Esquema desconocido: {parsed.scheme}"
                
        except Exception as e:
            self.logger.error(f"Error verificando seguridad de URL {url}: {str(e)}")
            return False, f"Error al verificar la URL: {str(e)}"
    
    def get_url_parts(self, url: str) -> Optional[dict]:
        """
        Descompone una URL en sus partes constituyentes.
        
        Args:
            url (str): URL a descomponer

        Returns:
            Optional[dict]: Diccionario con las partes de la URL o None si es inválida
        """
        try:
            if not self.is_valid_url(url):
                return None
                
            parsed = urlparse(url)
            query_params = {}
            
            # Parsear parámetros de query si existen
            if parsed.query:
                query_params = dict(param.split('=') for param in parsed.query.split('&'))
            
            return {
                'scheme': parsed.scheme,
                'username': parsed.username,
                'password': parsed.password,
                'hostname': parsed.hostname,
                'port': parsed.port,
                'path': parsed.path,
                'query': query_params,
                'fragment': parsed.fragment
            }
            
        except Exception as e:
            self.logger.error(f"Error descomponiendo URL {url}: {str(e)}")
            return None