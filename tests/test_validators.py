"""
Test Validators Module
-------------------
Pruebas unitarias para el módulo utils.validators
"""

import pytest
from src.utils.validators import URLValidator

@pytest.fixture
def validator():
    """Fixture que proporciona una instancia de URLValidator."""
    return URLValidator()

class TestURLValidator:
    """Pruebas para la clase URLValidator."""
    
    def test_initialization(self, validator):
        """Prueba la inicialización correcta del validador."""
        assert hasattr(validator, 'url_pattern')
        assert validator.url_pattern is not None
    
    def test_valid_urls(self, validator):
        """Prueba URLs válidas."""
        valid_urls = [
            "https://www.example.com",
            "http://example.com",
            "https://sub.domain.example.com",
            "http://example.com:8080",
            "https://example.com/path",
            "http://example.com/path?param=value",
            "https://example.com#section"
        ]
        
        for url in valid_urls:
            assert validator.is_valid_url(url), f"URL debería ser válida: {url}"
    
    def test_invalid_urls(self, validator):
        """Prueba URLs inválidas."""
        invalid_urls = [
            "",
            "not_a_url",
            "ftp://example.com",
            "//example.com",
            "https://",
            "https://.com",
            "https://example.",
            "http:/example.com"
        ]
        
        for url in invalid_urls:
            assert not validator.is_valid_url(url), f"URL debería ser inválida: {url}"
    
    def test_normalize_url(self, validator):
        """Prueba la normalización de URLs."""
        test_cases = [
            ("example.com", "https://example.com"),
            ("http://example.com", "http://example.com"),
            ("https://example.com", "https://example.com"),
        ]
        
        for input_url, expected in test_cases:
            assert validator.normalize_url(input_url) == expected
    
    def test_get_url_info(self, validator):
        """Prueba la obtención de información de URL."""
        url = "https://user:pass@example.com:8080/path?query=value#fragment"
        info = validator.get_url_info(url)
        
        assert info is not None
        assert info['scheme'] == 'https'
        assert info['domain'] == 'user:pass@example.com:8080'
        assert info['path'] == '/path'
        assert info['query'] == 'query=value'
        assert info['fragment'] == 'fragment'
    
    def test_get_domain_info(self, validator):
        """Prueba la obtención de información de dominio."""
        url = "https://sub.example.com"
        info = validator.get_domain_info(url)
        
        assert info is not None
        assert info['domain'] == 'sub.example.com'
        assert info['subdomain'] == 'sub'
        assert info['domain_name'] == 'example'
        assert info['tld'] == 'com'
    
    def test_is_secure_url(self, validator):
        """Prueba la verificación de URLs seguras."""
        test_cases = [
            ("https://example.com", True),
            ("http://example.com", False),
            ("invalid_url", False)
        ]
        
        for url, expected_secure in test_cases:
            is_secure, reason = validator.is_secure_url(url)
            assert is_secure == expected_secure
    
    def test_get_url_parts(self, validator):
        """Prueba la descomposición de URLs."""
        url = "https://user:pass@example.com:8080/path?key=value#section"
        parts = validator.get_url_parts(url)
        
        assert parts is not None
        assert parts['scheme'] == 'https'
        assert parts['username'] == 'user'
        assert parts['password'] == 'pass'
        assert parts['hostname'] == 'example.com'
        assert parts['port'] == 8080
        assert parts['path'] == '/path'
        assert parts['query'] == {'key': 'value'}
        assert parts['fragment'] == 'section'
    
    def test_invalid_url_info(self, validator):
        """Prueba el manejo de URLs inválidas en métodos de información."""
        invalid_url = "not_a_url"
        
        assert validator.get_url_info(invalid_url) is None
        assert validator.get_domain_info(invalid_url) is None
        assert validator.get_url_parts(invalid_url) is None
    
    def test_edge_cases(self, validator):
        """Prueba casos límite."""
        edge_cases = [
            None,
            "",
            " ",
            "https://" + "a" * 256 + ".com",  # URL muy larga
            "https://localhost",
            "https://127.0.0.1",
            "https://[::1]",
        ]
        
        for url in edge_cases:
            # No debería lanzar excepciones
            validator.is_valid_url(url)
            validator.get_url_info(url)
            validator.get_domain_info(url)
    
    def test_url_validation_with_special_characters(self, validator):
        """Prueba URLs con caracteres especiales."""
        special_urls = [
            "https://example.com/path with spaces",
            "https://example.com/path%20with%20encoding",
            "https://example.com/path?q=special&k=value+with+plus",
            "https://example.com/path?q=español",
        ]
        
        for url in special_urls:
            assert validator.is_valid_url(url), f"URL con caracteres especiales debería ser válida: {url}"