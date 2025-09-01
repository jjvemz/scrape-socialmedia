#!/usr/bin/env python3
"""
Validador de URLs para diferentes plataformas de redes sociales
"""

import re
import requests
from urllib.parse import urlparse

class URLValidator:
    def __init__(self):
        self.platform_patterns = {
            'instagram': [
                r'https?://(?:www\.)?instagram\.com/[\w.-]+/p/[\w-]+/?.*',
                r'https?://(?:www\.)?instagram\.com/[\w.-]+/reel/[\w-]+/?.*',
                r'https?://(?:www\.)?instagram\.com/[\w.-]+/tv/[\w-]+/?.*',
                r'https?://(?:www\.)?instagram\.com/p/[\w-]+/?.*',
                r'https?://(?:www\.)?instagram\.com/reel/[\w-]+/?.*',
                r'https?://(?:www\.)?instagram\.com/tv/[\w-]+/?.*'
            ]
        }
        
    def is_valid_url(self, url, platform=None):
        """
        Valida si una URL pertenece a la plataforma especificada
        
        Args:
            url (str): URL a validar
            platform (str): Plataforma esperada ('instagram')
            
        Returns:
            bool: True si la URL es válida para la plataforma
        """
        if not url or not isinstance(url, str):
            return False
            
        url = url.strip()
        
        # Verificar formato básico de URL
        if not self._is_valid_url_format(url):
            return False
            
        if platform:
            return self._matches_platform(url, platform)
        else:
            # Si no se especifica plataforma, verificar si coincide con alguna
            for platform_name in self.platform_patterns:
                if self._matches_platform(url, platform_name):
                    return True
            return False
    
    def _is_valid_url_format(self, url):
        """Verifica el formato básico de la URL"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _matches_platform(self, url, platform):
        """Verifica si la URL coincide con los patrones de la plataforma"""
        if platform not in self.platform_patterns:
            return False
            
        patterns = self.platform_patterns[platform]
        
        for pattern in patterns:
            try:
                if re.match(pattern, url, re.IGNORECASE):
                    return True
            except re.error:
                continue
                
        return False
    
    def detect_platform(self, url):
        """
        Detecta automáticamente la plataforma de una URL
        
        Args:
            url (str): URL a analizar
            
        Returns:
            str or None: Nombre de la plataforma o None si no se detecta
        """
        for platform, patterns in self.platform_patterns.items():
            for pattern in patterns:
                if re.match(pattern, url, re.IGNORECASE):
                    return platform
        return None
    
    def validate_url_accessibility(self, url, timeout=10):
        """
        Verifica si la URL es accesible (opcional, para validación adicional)
        
        Args:
            url (str): URL a verificar
            timeout (int): Timeout en segundos
            
        Returns:
            bool: True si la URL es accesible
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
            return response.status_code < 400
            
        except:
            return False
    
    def normalize_url(self, url, platform):
        """
        Normaliza la URL eliminando parámetros innecesarios
        
        Args:
            url (str): URL original
            platform (str): Plataforma de la URL
            
        Returns:
            str: URL normalizada
        """
        if platform == 'instagram':
            # Limpiar parámetros de Instagram
            if '?' in url:
                base_url = url.split('?')[0]
                return base_url.rstrip('/')
        
        return url
    
    def get_platform_info(self, platform):
        """
        Obtiene información sobre los patrones soportados para una plataforma
        
        Args:
            platform (str): Nombre de la plataforma
            
        Returns:
            dict: Información de la plataforma
        """
        if platform not in self.platform_patterns:
            return None
            
        return {
            'platform': platform,
            'patterns': self.platform_patterns[platform],
            'examples': self._get_example_urls(platform)
        }
    
    def _get_example_urls(self, platform):
        """Devuelve URLs de ejemplo para cada plataforma"""
        examples = {
            'instagram': [
                'https://www.instagram.com/p/ABC123DEF456/',
                'https://www.instagram.com/reel/XYZ789ABC123/'
            ]
        }
        
        return examples.get(platform, [])