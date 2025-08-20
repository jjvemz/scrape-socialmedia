#!/usr/bin/env python3
"""
Configuración y cliente para ScrapFly
"""

import os
import time
import random
from scrapfly import ScrapflyClient, ScrapeConfig
from fake_useragent import UserAgent

class ScrapFlyConfig:
    def __init__(self):
        # Buscar API key en variables de entorno o archivo .env
        self.api_key = self._get_api_key()
        
        if self.api_key:
            self.client = ScrapflyClient(key=self.api_key)
        else:
            self.client = None
            
        self.ua = UserAgent()
        
        # Configuración de headers por defecto
        self.default_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        }
        
        # Configuración específica por plataforma
        self.platform_configs = {
            'tiktok': {
                'render_js': True,
                'wait_for_selector': 'div[data-e2e="comment-list"]',
                'auto_scroll': True,
                'scroll_pause_time': 2,
                'additional_headers': {
                    'Referer': 'https://www.tiktok.com/',
                    'Origin': 'https://www.tiktok.com'
                }
            },
            'instagram': {
                # ✅ Configuración optimizada según investigación ScrapFly 2025
                'asp': True,                              # CRÍTICO: Anti-Scraping Protection
                'cost_budget': 55,                        # Presupuesto adecuado para ASP
                'proxy_pool': 'public_residential_pool',  # Proxies residenciales obligatorios
                'country': 'US',                          # País recomendado
                'timeout': 45000,                         # 45 segundos timeout
                'retry': False,                           # Disable retry to allow timeout
                'render_js': True,
                'wait_for_selector': 'article, main, [role="main"]',
                'auto_scroll': True,
                'scroll_pause_time': 2,
                'additional_headers': {
                    # ✅ Headers críticos para Instagram API
                    'x-ig-app-id': '936619743392459',     # OBLIGATORIO para Instagram
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Referer': 'https://www.instagram.com/',
                    'Origin': 'https://www.instagram.com',
                    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    'Sec-Ch-Ua-Mobile': '?0',
                    'Sec-Ch-Ua-Platform': '"Windows"',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin'
                }
            },
            'facebook': {
                'asp': True,                              # Enable Anti-Scraping Protection for Facebook
                'cost_budget': 120,                       # Higher budget for Facebook's anti-bot measures
                'proxy_pool': 'public_residential_pool',  # Use residential proxies
                'country': 'US',                          # US-based proxies
                'render_js': True,
                'wait_for_selector': 'body',              # More basic selector
                'auto_scroll': True,
                'scroll_pause_time': 2,
                'additional_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Referer': 'https://www.facebook.com/',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'same-origin',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    'Sec-Ch-Ua-Mobile': '?0',
                    'Sec-Ch-Ua-Platform': '"Windows"'
                }
            }
        }
    
    def _get_api_key(self):
        """Obtiene la API key de ScrapFly"""
        # Intentar obtener de variables de entorno
        api_key = os.getenv('SCRAPFLY_API_KEY')
        
        if not api_key:
            # Intentar leer de archivo .env
            env_file = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith('SCRAPFLY_API_KEY='):
                            api_key = line.split('=', 1)[1].strip().strip('"\'')
                            break
        
        if not api_key:
            # Solicitar al usuario que ingrese la API key
            print("\n🔑 No se encontró la API key de ScrapFly.")
            print("Puedes obtener una gratis en: https://scrapfly.io/")
            api_key = input("Ingresa tu API key de ScrapFly: ").strip()
            
            # Guardar en archivo .env para futuras ejecuciones
            if api_key:
                env_file = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
                with open(env_file, 'a') as f:
                    f.write(f"\nSCRAPFLY_API_KEY={api_key}\n")
        
        return api_key
    
    def verify_connection(self):
        """Verifica que la conexión con ScrapFly funcione"""
        if not self.client:
            print("ERROR: Cliente ScrapFly no inicializado. Verifica tu API key.")
            return False
            
        try:
            # Test simple con configuración básica
            result = self.client.scrape(ScrapeConfig(
                url="https://httpbin.org/user-agent"
                # Removido timeout para evitar conflicto con retry
            ))
            return result.success
        except Exception as e:
            print(f"ERROR: Error al verificar conexión ScrapFly: {str(e)}")
            return False
    
    def create_scrape_config(self, url, platform='general', custom_options=None):
        """
        Crea la configuración de scraping para una plataforma específica
        
        Args:
            url (str): URL a scrapear
            platform (str): Plataforma ('tiktok', 'instagram', 'facebook', 'general')
            custom_options (dict): Opciones personalizadas adicionales
            
        Returns:
            ScrapeConfig: Configuración lista para usar
        """
        
        if not self.client:
            raise Exception("Cliente ScrapFly no disponible")
            
        # Obtener configuración de plataforma
        platform_config = self.platform_configs.get(platform, {})
        
        # Headers combinados
        headers = self.default_headers.copy()
        headers['User-Agent'] = self.ua.random
        
        if 'additional_headers' in platform_config:
            headers.update(platform_config['additional_headers'])
        
        # Configuración base (sin timeout para evitar conflictos)
        config_params = {
            'url': url,
            'headers': headers,
            'country': 'US',  # Usar proxies de US
            'render_js': platform_config.get('render_js', False),
            'cache': False,  # No usar caché para datos frescos
            'debug': False
        }
        
        if platform == 'instagram':
            # Generar session ID único para coherencia de navegación
            session_id = f"instagram-session-{int(time.time())}-{random.randint(1000, 9999)}"
            
            # Configuración optimizada para Instagram comments
            config_params.update({
                'asp': True,                                    # CRÍTICO para Instagram
                'cost_budget': platform_config.get('cost_budget', 80),  # Presupuesto suficiente para ASP
                'proxy_pool': 'public_residential_pool',        # Proxies residenciales
                'session': session_id,                          # Manejo de sesión
                'cache': False                                  # No usar caché para datos frescos
            })
        elif platform == 'facebook':
            # Generar session ID único para Facebook
            session_id = f"facebook-session-{int(time.time())}-{random.randint(1000, 9999)}"
            
            # Configuración optimizada para Facebook con ASP
            config_params.update({
                'asp': True,                                    # CRÍTICO para Facebook login bypass
                'cost_budget': platform_config.get('cost_budget', 120),  # Higher budget for Facebook
                'proxy_pool': 'public_residential_pool',        # Proxies residenciales
                'session': session_id,                          # Manejo de sesión
                'cache': False                                  # No usar caché para datos frescos
            })
        
        # Aplicar opciones personalizadas ANTES de manejar timeout/retry conflicts
        if custom_options:
            config_params.update(custom_options)
        
        # Fix timeout/retry conflicts - ScrapFly doesn't allow custom timeout when retry is enabled
        has_retry = config_params.get('retry', False) or (custom_options and custom_options.get('retry', False))
        has_timeout = 'timeout' in config_params or (custom_options and 'timeout' in custom_options)
        
        # Only remove timeout if retry is explicitly enabled
        if has_retry and has_timeout:
            config_params.pop('timeout', None)
            if custom_options and 'timeout' in custom_options:
                custom_options.pop('timeout', None)
            print("INFO: Removed timeout setting due to retry being enabled")
        elif not has_retry and not has_timeout:
            # Add a reasonable default timeout when no retry and no timeout specified
            config_params['timeout'] = platform_config.get('timeout', 30000)
        
        # Add wait selector only if render_js is enabled
        if config_params.get('render_js', False) and 'wait_for_selector' in platform_config:
            config_params['wait_for_selector'] = platform_config['wait_for_selector']
        elif 'wait_for_selector' in config_params and not config_params.get('render_js', False):
            # Remove wait_for_selector if render_js is disabled
            config_params.pop('wait_for_selector', None)
            print("WARNING: Removed wait_for_selector - only works with render_js enabled")
            
        return ScrapeConfig(**config_params)
    
    def scrape_with_retry(self, scrape_config, max_retries=3, base_delay=2):
        """
        Ejecuta scraping con reintentos automáticos
        
        Args:
            scrape_config (ScrapeConfig): Configuración de scraping
            max_retries (int): Número máximo de reintentos
            base_delay (int): Delay base entre reintentos (segundos)
            
        Returns:
            dict: Resultado del scraping con información de éxito/error
        """
        if not self.client:
            return {'success': False, 'error': 'Cliente ScrapFly no disponible', 'data': None}
        
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    # Delay exponencial con jitter
                    delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
                    print(f"RETRY: Reintento {attempt}/{max_retries} en {delay:.1f}s...")
                    time.sleep(delay)
                
                result = self.client.scrape(scrape_config)
                
                if result.success:
                    return {
                        'success': True,
                        'data': result.content,
                        'status_code': getattr(result, 'status_code', 200),
                        'url': getattr(result, 'url', scrape_config.url),
                        'attempt': attempt + 1
                    }
                else:
                    last_error = f"Status code: {getattr(result, 'status_code', 'Unknown')}"
                    
            except Exception as e:
                last_error = str(e)
                print(f"ERROR: Error en intento {attempt + 1}: {last_error}")
                
                # Si es un error de configuración, no reintentar
                if "timeout" in last_error.lower() and "retry" in last_error.lower():
                    print("WARNING: Error de configuración detectado, ajustando...")
                    # Crear nueva configuración sin conflictos
                    try:
                        simple_config = ScrapeConfig(
                            url=scrape_config.url,
                            headers=scrape_config.headers,
                            country='US',
                            cache=False
                        )
                        result = self.client.scrape(simple_config)
                        if result.success:
                            return {
                                'success': True,
                                'data': result.content,
                                'status_code': getattr(result, 'status_code', 200),
                                'url': getattr(result, 'url', scrape_config.url),
                                'attempt': attempt + 1
                            }
                    except Exception as e2:
                        last_error = f"Error con configuración simple: {str(e2)}"
                        break
        
        return {
            'success': False,
            'error': f"Falló después de {max_retries + 1} intentos. Último error: {last_error}",
            'data': None
        }
    
    def execute_javascript(self, url, javascript_code, platform='general'):
        """
        Ejecuta JavaScript personalizado en una página
        
        Args:
            url (str): URL donde ejecutar el JavaScript
            javascript_code (str): Código JavaScript a ejecutar
            platform (str): Plataforma objetivo
            
        Returns:
            dict: Resultado de la ejecución
        """
        config = self.create_scrape_config(url, platform, {
            'render_js': True,
            'js': javascript_code,  # Correct parameter name for ScrapFly
            'wait_for_selector': 'article, main'
            # No incluir timeout cuando retry está habilitado
        })
        
        # Use direct execution for JavaScript to avoid retry conflicts
        try:
            result = self.client.scrape(config)
            if result.success:
                return {
                    'success': True,
                    'data': result.content
                }
            else:
                return {
                    'success': False,
                    'error': f"ScrapFly error: {result.error}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"Execution error: {str(e)}"
            }
    
    def get_platform_limits(self, platform):
        """
        Retorna los límites recomendados para cada plataforma
        
        Args:
            platform (str): Nombre de la plataforma
            
        Returns:
            dict: Límites y configuraciones recomendadas
        """
        limits = {
            'tiktok': {
                'requests_per_minute': 20,
                'delay_between_requests': 3,
                'max_comments_per_video': 1000,
                'timeout': 30
            },
            'instagram': {
                'requests_per_minute': 15,
                'delay_between_requests': 4,
                'max_comments_per_video': 500,
                'timeout': 25
            },
            'facebook': {
                'requests_per_minute': 10,
                'delay_between_requests': 6,
                'max_comments_per_video': 800,
                'timeout': 35
            }
        }
        
        return limits.get(platform, {
            'requests_per_minute': 10,
            'delay_between_requests': 6,
            'max_comments_per_video': 500,
            'timeout': 30
        })
    
    def rotate_headers(self):
        """Rota los headers para evitar detección"""
        self.default_headers['User-Agent'] = self.ua.random
        
        # Rotar algunos valores adicionales
        accept_languages = [
            'en-US,en;q=0.9',
            'en-US,en;q=0.8',
            'en-GB,en;q=0.9',
            'en-US,en;q=0.5,es;q=0.3'
        ]
        
        self.default_headers['Accept-Language'] = random.choice(accept_languages)
        
        return self.default_headers