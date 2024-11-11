"""
Test Checker Module
-----------------
Pruebas unitarias para el módulo core.checker
"""

import pytest
import urllib.error
from unittest.mock import Mock, patch
from datetime import datetime
from src.core.checker import WebsiteChecker, CheckResult

@pytest.fixture
def checker():
    """Fixture que proporciona una instancia de WebsiteChecker."""
    return WebsiteChecker(timeout=5)

@pytest.fixture
def mock_response():
    """Fixture que simula una respuesta HTTP."""
    mock = Mock()
    mock.getcode.return_value = 200
    mock.info.return_value = {
        'Content-Type': 'text/html',
        'Server': 'nginx/1.19.0',
    }
    mock.read.return_value = b"<html><body>Test</body></html>"
    return mock

class TestWebsiteChecker:
    """Pruebas para la clase WebsiteChecker."""
    
    def test_initialization(self, checker):
        """Prueba la inicialización correcta del checker."""
        assert checker.timeout == 5
        assert checker.verify_ssl == True
        assert isinstance(checker._history, dict)
        assert isinstance(checker.metrics, dict)
    
    @patch('urllib.request.urlopen')
    def test_check_website_success(self, mock_urlopen, checker, mock_response):
        """Prueba una verificación exitosa de sitio web."""
        mock_urlopen.return_value = mock_response
        url = "https://example.com"
        
        result = checker.check_website(url)
        
        assert isinstance(result, CheckResult)
        assert result.status_code == 200
        assert result.response_time > 0
        assert result.error is None
    
    @patch('urllib.request.urlopen')
    def test_check_website_http_error(self, mock_urlopen, checker):
        """Prueba el manejo de errores HTTP."""
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://example.com",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None
        )
        
        result = checker.check_website("https://example.com")
        
        assert result.status_code == 404
        assert result.error is not None
    
    @patch('urllib.request.urlopen')
    def test_check_website_timeout(self, mock_urlopen, checker):
        """Prueba el manejo de timeout."""
        mock_urlopen.side_effect = urllib.error.URLError("timeout")
        
        result = checker.check_website("https://example.com")
        
        assert result.status_code == -1
        assert "timeout" in str(result.error).lower()
    
    def test_get_statistics_empty(self, checker):
        """Prueba obtener estadísticas cuando no hay datos."""
        stats = checker.get_statistics("https://example.com")
        
        assert stats['total_checks'] == 0
        assert stats['success_rate'] == 0
        assert stats['avg_response_time'] == 0
    
    @patch('urllib.request.urlopen')
    def test_get_statistics_with_data(self, mock_urlopen, checker, mock_response):
        """Prueba obtener estadísticas después de algunas verificaciones."""
        mock_urlopen.return_value = mock_response
        url = "https://example.com"
        
        # Realizar algunas verificaciones
        for _ in range(3):
            checker.check_website(url)
        
        stats = checker.get_statistics(url)
        
        assert stats['total_checks'] == 3
        assert stats['success_rate'] == 100.0
        assert stats['avg_response_time'] > 0
    
    def test_clear_history(self, checker):
        """Prueba la limpieza del historial."""
        url = "https://example.com"
        checker.metrics[url] = {'checks': 1}
        checker._history[url] = [{'timestamp': datetime.now()}]
        
        checker.clear_history()
        
        assert len(checker._history) == 0
        assert len(checker.metrics) == 0
    
    @pytest.mark.asyncio
    async def test_bulk_check(self, checker):
        """Prueba la verificación en masa de URLs."""
        urls = [
            "https://example1.com",
            "https://example2.com",
            "https://example3.com"
        ]
        
        results = await checker.bulk_check(urls)
        
        assert len(results) == 3
        assert all(isinstance(result, CheckResult) for result in results.values())
    
    def test_calculate_health_score(self, checker):
        """Prueba el cálculo del score de salud."""
        url = "https://example.com"
        
        # Simular algunas métricas
        checker.metrics[url] = {
            'checks': 10,
            'successful': 9,
            'failed': 1,
            'total_response_time': 5000,
            'uptime_percentage': 90.0
        }
        
        score = checker.calculate_health_score(url)
        
        assert 0 <= score <= 100
        assert score > 80  # Debería ser alto dado que la mayoría de las métricas son buenas

    def test_get_history_with_days(self, checker):
        """Prueba obtener historial filtrado por días."""
        url = "https://example.com"
        
        # Agregar algunos registros al historial
        checker._history[url] = [
            {'timestamp': datetime.now(), 'status_code': 200},
            {'timestamp': datetime.now(), 'status_code': 200},
        ]
        
        history = checker.get_history(url, days=1)
        
        assert len(history) == 2
        assert all('timestamp' in check for check in history)
    
    @patch('urllib.request.urlopen')
    def test_ssl_verification(self, mock_urlopen, checker, mock_response):
        """Prueba la verificación SSL."""
        mock_urlopen.return_value = mock_response
        url = "https://example.com"
        
        result = checker.check_website(url)
        
        assert result.status_code == 200
        # El SSL info podría ser None en pruebas, pero no debería causar errores
        assert not hasattr(result, 'error') or result.error is None
    
    def test_export_import_data(self, checker, tmp_path):
        """Prueba la exportación e importación de datos."""
        url = "https://example.com"
        checker._history[url] = [
            {'timestamp': datetime.now(), 'status_code': 200}
        ]
        
        # Exportar datos
        export_file = tmp_path / "export.json"
        checker.export_data(str(export_file))
        
        # Limpiar datos
        checker.clear_history()
        assert len(checker._history) == 0
        
        # Importar datos
        checker.import_data(str(export_file))
        assert len(checker._history) == 1
        assert url in checker._history