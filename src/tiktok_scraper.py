#!/usr/bin/env python3
"""
Scraper específico para TikTok usando ScrapFly
"""

import re
import json
import time
import random
from bs4 import BeautifulSoup
from datetime import datetime
from utils.scrapfly_config import ScrapFlyConfig

class TikTokScraper:
    def __init__(self):
        self.scrapfly = ScrapFlyConfig()
        self.limits = self.scrapfly.get_platform_limits('tiktok')
        
    def scrape_comments(self, url):
        """
        Extrae comentarios y metadatos de un video de TikTok
        
        Args:
            url (str): URL del video de TikTok
            
        Returns:
            dict: Resultado con éxito/error y datos extraídos
        """
        try:
            print(f"🎵 Iniciando scraping de TikTok: {url[:50]}...")
            
            # Paso 1: Obtener página inicial
            initial_result = self._get_initial_page(url)
            if not initial_result['success']:
                return initial_result
            
            # Paso 2: Extraer metadatos básicos
            metadata = self._extract_metadata(initial_result['html'])
            
            # Paso 3: Cargar comentarios con JavaScript
            comments_result = self._load_comments_with_js(url)
            if not comments_result['success']:
                return comments_result
            
            # Paso 4: Procesar comentarios
            comments = self._process_comments(comments_result['html'], metadata.get('publisher_username', ''))
            
            # Paso 5: Obtener seguidores para cada usuario único
            comments = self._enrich_with_followers(comments)
            
            return {
                'success': True,
                'data': {
                    'metadata': metadata,
                    'comments': comments,
                    'total_comments': len(comments),
                    'extraction_time': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error en TikTok scraper: {str(e)}",
                'data': None
            }
    
    def _get_initial_page(self, url):
        """Obtiene la página inicial del video"""
        try:
            config = self.scrapfly.create_scrape_config(url, 'tiktok')
            result = self.scrapfly.scrape_with_retry(config)
            
            if result['success']:
                return {
                    'success': True,
                    'html': result['data'],
                    'url': result.get('url', url)
                }
            else:
                return {
                    'success': False,
                    'error': f"Error cargando página: {result.get('error', 'Unknown')}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Error en solicitud inicial: {str(e)}"
            }
    
    def _extract_metadata(self, html):
        """Extrae metadatos del video desde el HTML"""
        metadata = {}
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Buscar datos JSON en scripts
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and '__UNIVERSAL_DATA_FOR_REHYDRATION__' in script.string:
                    # Extraer JSON data
                    json_match = re.search(r'__UNIVERSAL_DATA_FOR_REHYDRATION__\s*=\s*({.+?})\s*;', script.string)
                    if json_match:
                        try:
                            data = json.loads(json_match.group(1))
                            metadata.update(self._parse_tiktok_json(data))
                        except:
                            pass
            
            # Fallback: extraer desde meta tags y elementos visibles
            if not metadata:
                metadata = self._extract_metadata_fallback(soup)
            
        except Exception as e:
            print(f"⚠️ Error extrayendo metadatos: {str(e)}")
        
        return metadata
    
    def _parse_tiktok_json(self, data):
        """Parsea los datos JSON de TikTok"""
        metadata = {}
        
        try:
            # Navegar por la estructura JSON de TikTok
            default_scope = data.get('__DEFAULT_SCOPE__', {})
            webapp_data = default_scope.get('webapp.video-detail', {})
            item_info = webapp_data.get('itemInfo', {}).get('itemStruct', {})
            
            if item_info:
                # Información del video
                metadata['video_id'] = item_info.get('id', '')
                metadata['description'] = item_info.get('desc', '')
                metadata['likes'] = item_info.get('stats', {}).get('diggCount', 0)
                metadata['shares'] = item_info.get('stats', {}).get('shareCount', 0)
                metadata['total_comments_claimed'] = item_info.get('stats', {}).get('commentCount', 0)
                
                # Información del autor
                author_info = item_info.get('author', {})
                metadata['publisher_nickname'] = author_info.get('nickname', '')
                metadata['publisher_username'] = '@' + author_info.get('uniqueId', '')
                metadata['publisher_url'] = f"https://www.tiktok.com/@{author_info.get('uniqueId', '')}"
                
                # Tiempo de publicación
                create_time = item_info.get('createTime')
                if create_time:
                    metadata['publish_time'] = datetime.fromtimestamp(int(create_time)).strftime('%d-%m-%Y')
            
        except Exception as e:
            print(f"⚠️ Error parseando JSON TikTok: {str(e)}")
        
        return metadata
    
    def _extract_metadata_fallback(self, soup):
        """Método fallback para extraer metadatos"""
        metadata = {}
        
        try:
            # Intentar extraer desde meta tags
            og_title = soup.find('meta', property='og:title')
            if og_title:
                content = og_title.get('content', '')
                # El título suele contener el username
                username_match = re.search(r'@(\w+)', content)
                if username_match:
                    metadata['publisher_username'] = '@' + username_match.group(1)
            
            og_description = soup.find('meta', property='og:description')
            if og_description:
                metadata['description'] = og_description.get('content', '')
            
            # Buscar estadísticas en el HTML
            stats_pattern = r'"diggCount":(\d+)|"shareCount":(\d+)|"commentCount":(\d+)'
            stats_matches = re.findall(stats_pattern, str(soup))
            
            for match in stats_matches:
                if match[0]:  # likes
                    metadata['likes'] = int(match[0])
                elif match[1]:  # shares
                    metadata['shares'] = int(match[1])
                elif match[2]:  # comments
                    metadata['total_comments_claimed'] = int(match[2])
                    
        except Exception as e:
            print(f"⚠️ Error en metadata fallback: {str(e)}")
        
        return metadata
    
    def _load_comments_with_js(self, url):
        """Carga comentarios usando JavaScript para scroll infinito"""
        javascript_code = """
        // Función para scroll y cargar comentarios
        async function loadAllComments() {
            let previousCount = 0;
            let stableCount = 0;
            const maxStable = 5;
            
            while (stableCount < maxStable) {
                // Scroll hacia abajo
                window.scrollTo(0, document.body.scrollHeight);
                
                // Esperar a que carguen nuevos comentarios
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // Contar comentarios actuales
                const comments = document.querySelectorAll('[data-e2e="comment-item"], .comment-item, [class*="comment"]');
                const currentCount = comments.length;
                
                if (currentCount === previousCount) {
                    stableCount++;
                } else {
                    stableCount = 0;
                    previousCount = currentCount;
                }
                
                console.log(`Comentarios encontrados: ${currentCount}`);
            }
            
            return document.documentElement.outerHTML;
        }
        
        return loadAllComments();
        """
        
        try:
            result = self.scrapfly.execute_javascript(url, javascript_code, 'tiktok')
            return result
        except Exception as e:
            return {
                'success': False,
                'error': f"Error ejecutando JavaScript: {str(e)}"
            }
    
    def _process_comments(self, html, publisher_username=''):
        """Procesa y extrae comentarios del HTML"""
        comments = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Selectores para comentarios de TikTok
            comment_selectors = [
                '[data-e2e="comment-item"]',
                '.comment-item',
                '[class*="comment-container"]',
                '[class*="CommentContainer"]'
            ]
            
            comment_elements = []
            for selector in comment_selectors:
                elements = soup.select(selector)
                if elements:
                    comment_elements = elements
                    break
            
            if not comment_elements:
                # Búsqueda más genérica
                comment_elements = soup.find_all('div', class_=re.compile(r'comment', re.I))
            
            for i, element in enumerate(comment_elements[:self.limits['max_comments_per_video']]):
                comment = self._extract_comment_data(element, i + 1)
                if comment:
                    comments.append(comment)
                    
        except Exception as e:
            print(f"⚠️ Error procesando comentarios: {str(e)}")
        
        return comments
    
    def _extract_comment_data(self, element, comment_id):
        """Extrae datos de un comentario individual"""
        try:
            # Extraer username
            username_selectors = ['[data-e2e="comment-username"]', '.username', '[class*="username"]']
            username = self._find_text_by_selectors(element, username_selectors)
            
            # Extraer texto del comentario
            text_selectors = ['[data-e2e="comment-text"]', '.comment-text', '[class*="comment-text"]']
            text = self._find_text_by_selectors(element, text_selectors)
            
            # Extraer likes
            likes_selectors = ['[data-e2e="comment-like-count"]', '.like-count', '[class*="like"]']
            likes = self._find_text_by_selectors(element, likes_selectors) or "0"
            
            # Extraer tiempo
            time_selectors = ['[data-e2e="comment-time"]', '.time', '[class*="time"]']
            time_posted = self._find_text_by_selectors(element, time_selectors)
            
            # Extraer imagen de perfil
            img_element = element.find('img')
            profile_pic = img_element.get('src', '') if img_element else ''
            
            # Determinar si es respuesta
            is_reply = 'reply' in str(element).lower() or 'indent' in str(element).lower()
            
            if username and text:
                return {
                    'comment_id': comment_id,
                    'nickname': username.replace('@', ''),
                    'username': username if username.startswith('@') else f'@{username}',
                    'user_url': f"https://www.tiktok.com/{username.replace('@', '@')}",
                    'text': text.strip(),
                    'time': time_posted or 'N/A',
                    'likes': self._parse_number(likes),
                    'profile_pic': profile_pic,
                    'followers': 'N/A',  # Se completará después
                    'is_reply': is_reply,
                    'replied_to': '',
                    'num_replies': 0
                }
                
        except Exception as e:
            print(f"⚠️ Error extrayendo comentario: {str(e)}")
        
        return None
    
    def _find_text_by_selectors(self, element, selectors):
        """Busca texto usando múltiples selectores CSS"""
        for selector in selectors:
            found = element.select_one(selector)
            if found and found.get_text(strip=True):
                return found.get_text(strip=True)
        return None
    
    def _parse_number(self, text):
        """Convierte texto de números (ej: "1.2K" -> 1200)"""
        if not text:
            return 0
            
        text = str(text).strip().upper()
        
        # Remover caracteres no numéricos excepto K, M, B
        cleaned = re.sub(r'[^\d.KMB]', '', text)
        
        if 'K' in cleaned:
            return int(float(cleaned.replace('K', '')) * 1000)
        elif 'M' in cleaned:
            return int(float(cleaned.replace('M', '')) * 1000000)
        elif 'B' in cleaned:
            return int(float(cleaned.replace('B', '')) * 1000000000)
        else:
            try:
                return int(float(cleaned)) if cleaned else 0
            except:
                return 0
    
    def _enrich_with_followers(self, comments):
        """Enriquece los comentarios con datos de seguidores"""
        unique_users = {}
        
        # Agrupar comentarios por usuario para evitar requests duplicados
        for comment in comments:
            username = comment['username'].replace('@', '')
            if username not in unique_users:
                unique_users[username] = []
            unique_users[username].append(comment)
        
        # Obtener seguidores para cada usuario único
        for username, user_comments in unique_users.items():
            try:
                print(f"  📊 Obteniendo seguidores para @{username}...")
                followers = self._get_user_followers(username)
                
                # Actualizar todos los comentarios de este usuario
                for comment in user_comments:
                    comment['followers'] = followers
                
                # Delay para evitar rate limiting
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                print(f"  ⚠️ Error obteniendo seguidores para @{username}: {str(e)}")
                for comment in user_comments:
                    comment['followers'] = 'N/A'
        
        return comments
    
    def _get_user_followers(self, username):
        """Obtiene el número de seguidores de un usuario"""
        try:
            user_url = f"https://www.tiktok.com/@{username}"
            
            config = self.scrapfly.create_scrape_config(user_url, 'tiktok', {
                'render_js': True,
                'wait_for_selector': 'main',
                'timeout': 15000
            })
            
            result = self.scrapfly.scrape_with_retry(config, max_retries=2)
            
            if result['success']:
                html = result['data']
                
                # Buscar followerCount en JSON
                follower_patterns = [
                    r'"followerCount":(\d+)',
                    r'"followersCount":(\d+)', 
                    r'follower[^"]*":(\d+)',
                    r'Followers[^"]*":(\d+)'
                ]
                
                for pattern in follower_patterns:
                    match = re.search(pattern, html, re.IGNORECASE)
                    if match:
                        return self._format_number(int(match.group(1)))
                
                # Buscar en elementos HTML
                soup = BeautifulSoup(html, 'html.parser')
                follower_selectors = [
                    '[data-e2e="followers-count"]',
                    '[class*="follower"]',
                    '[class*="Follower"]'
                ]
                
                for selector in follower_selectors:
                    element = soup.select_one(selector)
                    if element:
                        text = element.get_text(strip=True)
                        if any(keyword in text.lower() for keyword in ['follower', 'seguidor']):
                            number = re.search(r'[\d.]+[KMB]?', text)
                            if number:
                                return self._parse_number(number.group())
                
            return 'N/A'
            
        except Exception as e:
            print(f"    ⚠️ Error: {str(e)}")
            return 'N/A'
    
    def _format_number(self, number):
        """Formatea números grandes (ej: 1500000 -> 1.5M)"""
        if number >= 1_000_000_000:
            return f"{number/1_000_000_000:.1f}B"
        elif number >= 1_000_000:
            return f"{number/1_000_000:.1f}M"
        elif number >= 1_000:
            return f"{number/1_000:.1f}K"
        else:
            return str(number)
    
    def get_video_id(self, url):
        """Extrae el ID del video de la URL"""
        patterns = [
            r'/video/(\d+)',
            r'v=(\d+)',
            r'/(\d+)(?:\?|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None