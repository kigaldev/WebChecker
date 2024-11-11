"""
Website Checker Core
------------------
Implementa la lógica principal para verificar el estado y rendimiento de sitios web.
"""

import urllib.request
import urllib.error
import ssl
import socket
import logging
import json
import asyncio
import aiohttp
from typing import Optional, Tuple, Dict, List
from datetime import datetime, timedelta
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from email.utils import formatdate
import hashlib

@dataclass
class CheckResult:
    """Clase para almacenar el resultado de una verificación."""
    status_code: int
    response_time: float
    content_type: Optional[str] = None
    server: Optional[str] = None
    content_length: Optional[int] = None
    ssl_info: Optional[Dict] = None
    headers: Optional[Dict] = None
    encoding: Optional[str] = None
    redirect_url: Optional[str] = None
    timestamp: datetime = datetime.now()
    error: Optional[str] = None

class WebsiteChecker:
    """Clase principal para verificar el estado y rendimiento de sitios web."""
    
    def __init__(self, 
                 timeout: int = 10,
                 max_redirects: int = 5,
                 verify_ssl: bool = True,
                 cache_duration: int = 300):
        """
        Inicializa el checker con configuraciones personalizables.
        
        Args:
            timeout (int): Tiempo máximo de espera para la respuesta en segundos
            max_redirects (int): Número máximo de redirecciones permitidas
            verify_ssl (bool): Verificar certificados SSL
            cache_duration (int): Duración del caché en segundos
        """
        self.timeout = timeout
        self.max_redirects = max_redirects
        self.verify_ssl = verify_ssl
        self.cache_duration = cache_duration
        
        self._setup_logging()
        self._init_storage()
        
        # Configuración de headers
        self.headers = {
            'User-Agent': 'WebsiteChecker/2.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Date': formatdate(timeval=None, localtime=False, usegmt=True)
        }
        
        # Configurar el contexto SSL
        self.ssl_context = self._setup_ssl_context()
        
        # Caché para resultados
        self._cache: Dict[str, Tuple[CheckResult, datetime]] = {}
        
        # Métricas y estadísticas
        self.metrics: Dict[str, dict] = {}
        
        # Pool de hilos para operaciones paralelas
        self.thread_pool = ThreadPoolExecutor(max_workers=10)
    
    def _setup_logging(self):
        """Configura el sistema de logging."""
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _init_storage(self):
        """Inicializa el almacenamiento de históricos."""
        self._history: Dict[str, List[dict]] = {}
        self._metrics: Dict[str, dict] = {}
    
    def _setup_ssl_context(self) -> ssl.SSLContext:
        """Configura el contexto SSL con opciones de seguridad."""
        context = ssl.create_default_context()
        if not self.verify_ssl:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        return context
    
    def _get_cached_result(self, url: str) -> Optional[CheckResult]:
        """Obtiene el resultado cacheado si está disponible y válido."""
        if url in self._cache:
            result, timestamp = self._cache[url]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_duration):
                return result
            else:
                del self._cache[url]
        return None
    
    def _cache_result(self, url: str, result: CheckResult):
        """Almacena el resultado en caché."""
        self._cache[url] = (result, datetime.now())
    
    async def check_website_async(self, url: str) -> CheckResult:
        """
        Verifica el estado de un sitio web de forma asíncrona.
        
        Args:
            url (str): URL del sitio web a verificar

        Returns:
            CheckResult: Objeto con los resultados de la verificación
        """
        try:
            # Verificar caché
            cached_result = self._get_cached_result(url)
            if cached_result:
                return cached_result
            
            start_time = datetime.now()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout,
                    max_redirects=self.max_redirects,
                    ssl=self.ssl_context if self.verify_ssl else False
                ) as response:
                    end_time = datetime.now()
                    
                    result = CheckResult(
                        status_code=response.status,
                        response_time=(end_time - start_time).total_seconds() * 1000,
                        content_type=response.headers.get('Content-Type'),
                        server=response.headers.get('Server'),
                        content_length=int(response.headers.get('Content-Length', 0)),
                        headers=dict(response.headers),
                        encoding=response.get_encoding(),
                        redirect_url=str(response.url) if str(response.url) != url else None,
                    )
                    
                    # Verificar SSL si es HTTPS
                    if url.startswith('https'):
                        result.ssl_info = await self._get_ssl_info_async(url)
                    
                    self._cache_result(url, result)
                    self._update_metrics(url, result)
                    self._record_check(url, result)
                    
                    return result
                    
        except Exception as e:
            self.logger.error(f"Error checking {url}: {str(e)}")
            return CheckResult(
                status_code=-1,
                response_time=-1,
                error=str(e)
            )
    
    def check_website(self, url: str) -> CheckResult:
        """
        Versión síncrona de check_website_async.
        
        Args:
            url (str): URL del sitio web a verificar

        Returns:
            CheckResult: Objeto con los resultados de la verificación
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.check_website_async(url))
        finally:
            loop.close()
    
    async def _get_ssl_info_async(self, url: str) -> Dict:
        """Obtiene información del certificado SSL de forma asíncrona."""
        try:
            host = urlparse(url).netloc
            context = ssl.create_default_context()
            
            reader, writer = await asyncio.open_connection(
                host, 443,
                ssl=context,
                server_hostname=host
            )
            
            cert = writer.get_extra_info('peercert')
            writer.close()
            await writer.wait_closed()
            
            if cert:
                return {
                    'issuer': dict(x[0] for x in cert['issuer']),
                    'subject': dict(x[0] for x in cert['subject']),
                    'version': cert['version'],
                    'expires': cert['notAfter'],
                    'serial_number': cert['serialNumber']
                }
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting SSL info for {url}: {str(e)}")
            return None
    
    def _update_metrics(self, url: str, result: CheckResult):
        """Actualiza las métricas para una URL específica."""
        if url not in self.metrics:
            self.metrics[url] = {
                'checks': 0,
                'successful': 0,
                'failed': 0,
                'total_response_time': 0,
                'min_response_time': float('inf'),
                'max_response_time': 0,
                'last_check': None,
                'uptime_percentage': 100.0
            }
        
        metrics = self.metrics[url]
        metrics['checks'] += 1
        metrics['last_check'] = datetime.now()
        
        if result.status_code == 200:
            metrics['successful'] += 1
        else:
            metrics['failed'] += 1
        
        if result.response_time > 0:
            metrics['total_response_time'] += result.response_time
            metrics['min_response_time'] = min(metrics['min_response_time'], result.response_time)
            metrics['max_response_time'] = max(metrics['max_response_time'], result.response_time)
        
        metrics['uptime_percentage'] = (metrics['successful'] / metrics['checks']) * 100
    
    def _record_check(self, url: str, result: CheckResult):
        """Registra una verificación en el historial."""
        if url not in self._history:
            self._history[url] = []
        
        self._history[url].append({
            'timestamp': datetime.now(),
            'status_code': result.status_code,
            'response_time': result.response_time,
            'error': result.error
        })
        
        # Mantener solo los últimos 1000 registros por URL
        if len(self._history[url]) > 1000:
            self._history[url] = self._history[url][-1000:]
    
    def get_statistics(self, url: str) -> Dict:
        """
        Obtiene estadísticas detalladas para una URL.
        
        Args:
            url (str): URL del sitio web

        Returns:
            Dict: Estadísticas detalladas
        """
        if url not in self.metrics:
            return {
                'total_checks': 0,
                'success_rate': 0,
                'avg_response_time': 0,
                'min_response_time': 0,
                'max_response_time': 0,
                'uptime_percentage': 0,
                'last_check': None
            }
        
        metrics = self.metrics[url]
        return {
            'total_checks': metrics['checks'],
            'success_rate': (metrics['successful'] / metrics['checks']) * 100,
            'avg_response_time': metrics['total_response_time'] / metrics['checks'],
            'min_response_time': metrics['min_response_time'],
            'max_response_time': metrics['max_response_time'],
            'uptime_percentage': metrics['uptime_percentage'],
            'last_check': metrics['last_check']
        }
    
    def get_history(self, url: str, days: Optional[int] = None) -> List[dict]:
        """
        Obtiene el historial de verificaciones para una URL.
        
        Args:
            url (str): URL del sitio web
            days (Optional[int]): Número de días a considerar

        Returns:
            List[dict]: Lista de verificaciones previas
        """
        if url not in self._history:
            return []
        
        history = self._history[url]
        
        if days is not None:
            cutoff = datetime.now() - timedelta(days=days)
            history = [
                check for check in history
                if check['timestamp'] >= cutoff
            ]
        
        return history
    
    def export_data(self, filename: str):
        """
        Exporta todos los datos a un archivo JSON.
        
        Args:
            filename (str): Nombre del archivo de salida
        """
        data = {
            'history': self._history,
            'metrics': self.metrics,
            'export_date': datetime.now().isoformat()
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, default=str, indent=2)
        except Exception as e:
            self.logger.error(f"Error exporting data: {str(e)}")
            raise
    
    def import_data(self, filename: str):
        """
        Importa datos desde un archivo JSON.
        
        Args:
            filename (str): Nombre del archivo a importar
        """
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                
            self._history = data['history']
            self.metrics = data['metrics']
            
            # Convertir strings de fecha a objetos datetime
            for url in self._history:
                for check in self._history[url]:
                    check['timestamp'] = datetime.fromisoformat(check['timestamp'])
            
            for url in self.metrics:
                if self.metrics[url]['last_check']:
                    self.metrics[url]['last_check'] = datetime.fromisoformat(
                        self.metrics[url]['last_check']
                    )
                    
        except Exception as e:
            self.logger.error(f"Error importing data: {str(e)}")
            raise
    
    def clear_history(self):
        """Limpia todo el historial y métricas."""
        self._history.clear()
        self.metrics.clear()
        self._cache.clear()
        self.logger.info("History and metrics cleared")

    async def bulk_check(self, urls: List[str]) -> Dict[str, CheckResult]:
        """
        Verifica múltiples URLs de forma asíncrona.
        
        Args:
            urls (List[str]): Lista de URLs a verificar

        Returns:
            Dict[str, CheckResult]: Resultados por URL
        """
        tasks = [self.check_website_async(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return dict(zip(urls, results))

    def calculate_health_score(self, url: str) -> float:
        """
        Calcula un score de salud para el sitio web (0-100).
        
        Args:
            url (str): URL del sitio web

        Returns:
            float: Score de salud
        """
        if url not in self.metrics:
            return 0.0
        
        metrics = self.metrics[url]
        
        # Factores y sus pesos
        uptime_weight = 0.4
        response_time_weight = 0.3
        success_rate_weight = 0.3
        
        # Calcular score de uptime (40%)
        uptime_score = metrics['uptime_percentage']
        
        # Calcular score de tiempo de respuesta (30%)
        avg_response_time = metrics['total_response_time'] / metrics['checks']
        response_time_score = max(0, 100 - (avg_response_time / 1000) * 100)
        
        # Calcular score de tasa de éxito (30%)
        success_rate = (metrics['successful'] / metrics['checks']) * 100