#!/usr/bin/env python3
"""
Scraper específico para Instagram usando ScrapFly
"""

import re
import json
import time
import random
from bs4 import BeautifulSoup
from datetime import datetime
from utils.scrapfly_config import ScrapFlyConfig

class InstagramScraper:
    def __init__(self):
        self.scrapfly = ScrapFlyConfig()
        self.limits = self.scrapfly.get_platform_limits('instagram')
        
    def scrape_comments(self, url):
        """
        Extrae comentarios y metadatos de un post/reel de Instagram
        
        Args:
            url (str): URL del post de Instagram
            
        Returns:
            dict: Resultado con éxito/error y datos extraídos
        """
        try:
            print(f"📸 Iniciando scraping de Instagram: {url[:50]}...")
            
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
                'error': f"Error en Instagram scraper: {str(e)}",
                'data': None
            }
    
    def _get_initial_page(self, url):
        """Obtiene la página inicial del post"""
        try:
            config = self.scrapfly.create_scrape_config(url, 'instagram')
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
        """Extrae metadatos del post desde el HTML"""
        metadata = {}
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Buscar datos JSON en scripts
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'author' in data:
                        metadata.update(self._parse_instagram_json(data))
                except:
                    pass
            
            # Buscar en window._sharedData
            if not metadata:
                script_tags = soup.find_all('script')
                for script in script_tags:
                    if script.string and 'window._sharedData' in script.string:
                        json_match = re.search(r'window\._sharedData\s*=\s*({.+?});', script.string)
                        if json_match:
                            try:
                                data = json.loads(json_match.group(1))
                                metadata.update(self._parse_shared_data(data))
                            except:
                                pass
            
            # Fallback: extraer desde meta tags
            if not metadata:
                metadata = self._extract_metadata_fallback(soup)
                
        except Exception as e:
            print(f"⚠️ Error extrayendo metadatos: {str(e)}")
        
        return metadata
    
    def _parse_instagram_json(self, data):
        """Parsea los datos JSON de Instagram"""
        metadata = {}
        
        try:
            # Estructura LD+JSON
            if 'author' in data:
                author = data['author']
                metadata['publisher_nickname'] = author.get('name', '')
                metadata['publisher_username'] = '@' + author.get('alternateName', '').replace('@', '')
                metadata['publisher_url'] = author.get('url', '')
            
            if 'caption' in data:
                metadata['description'] = data['caption']
            
            if 'interactionStatistic' in data:
                for stat in data['interactionStatistic']:
                    interaction_type = stat.get('interactionType', {}).get('@type', '')
                    if 'LikeAction' in interaction_type:
                        metadata['likes'] = stat.get('userInteractionCount', 0)
                    elif 'CommentAction' in interaction_type:
                        metadata['total_comments_claimed'] = stat.get('userInteractionCount', 0)
            
            if 'datePublished' in data:
                metadata['publish_time'] = datetime.fromisoformat(data['datePublished'].replace('Z', '+00:00')).strftime('%d-%m-%Y')
                
        except Exception as e:
            print(f"⚠️ Error parseando JSON Instagram: {str(e)}")
        
        return metadata
    
    def _parse_shared_data(self, data):
        """Parsea window._sharedData de Instagram"""
        metadata = {}
        
        try:
            # Navegar por la estructura _sharedData
            entry_data = data.get('entry_data', {})
            
            # Buscar en PostPage o ProfilePage
            pages = entry_data.get('PostPage', []) or entry_data.get('ProfilePage', [])
            
            if pages:
                page_data = pages[0]
                graphql = page_data.get('graphql', {})
                
                if 'shortcode_media' in graphql:
                    media = graphql['shortcode_media']
                    
                    # Información del post
                    metadata['likes'] = media.get('edge_media_preview_like', {}).get('count', 0)
                    metadata['total_comments_claimed'] = media.get('edge_media_to_comment', {}).get('count', 0)
                    
                    # Información del autor
                    owner = media.get('owner', {})
                    metadata['publisher_nickname'] = owner.get('full_name', '')
                    metadata['publisher_username'] = '@' + owner.get('username', '')
                    metadata['publisher_url'] = f"https://www.instagram.com/{owner.get('username', '')}/"
                    
                    # Descripción
                    edges = media.get('edge_media_to_caption', {}).get('edges', [])
                    if edges:
                        metadata['description'] = edges[0].get('node', {}).get('text', '')
                    
                    # Fecha
                    timestamp = media.get('taken_at_timestamp')
                    if timestamp:
                        metadata['publish_time'] = datetime.fromtimestamp(timestamp).strftime('%d-%m-%Y')
                        
        except Exception as e:
            print(f"⚠️ Error parseando _sharedData: {str(e)}")
        
        return metadata
    
    def _extract_metadata_fallback(self, soup):
        """Método fallback para extraer metadatos"""
        metadata = {}
        
        try:
            # Meta tags de Open Graph
            og_title = soup.find('meta', property='og:title')
            if og_title:
                content = og_title.get('content', '')
                # Extraer username del título
                username_match = re.search(r'@(\w+)', content)
                if username_match:
                    metadata['publisher_username'] = '@' + username_match.group(1)
            
            og_description = soup.find('meta', property='og:description')
            if og_description:
                metadata['description'] = og_description.get('content', '')
            
            # Buscar en el HTML visible
            # Instagram a menudo tiene datos en atributos data-*
            article_element = soup.find('article')
            if article_element:
                # Buscar likes y comentarios
                like_button = soup.find('button', {'aria-label': re.compile(r'like', re.I)})
                if like_button and like_button.get_text():
                    likes_match = re.search(r'(\d+)', like_button.get_text())
                    if likes_match:
                        metadata['likes'] = int(likes_match.group(1))
                        
        except Exception as e:
            print(f"⚠️ Error en metadata fallback: {str(e)}")
        
        return metadata
    
    def _load_comments_with_js(self, url):
        """Carga comentarios usando JavaScript"""
        javascript_code = """
        async function loadInstagramComments() {
            let previousCount = 0;
            let stableCount = 0;
            const maxStable = 5;
            
            // Buscar y hacer clic en "Ver más comentarios" si existe
            while (stableCount < maxStable) {
                // Buscar botones de "Ver más comentarios"
                const loadMoreButtons = document.querySelectorAll(
                    'button[type="button"]:not([disabled])'
                ).filter(btn => 
                    btn.textContent.includes('View') || 
                    btn.textContent.includes('more') ||
                    btn.textContent.includes('Ver') ||
                    btn.textContent.includes('Load')
                );
                
                // Hacer clic en botones encontrados
                let clicked = false;
                loadMoreButtons.forEach(btn => {
                    if (btn.offsetParent !== null) { // Visible
                        btn.click();
                        clicked = true;
                    }
                });
                
                if (clicked) {
                    await new Promise(resolve => setTimeout(resolve, 3000));
                }
                
                // Scroll para cargar más contenido
                window.scrollTo(0, document.body.scrollHeight);
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // Contar comentarios
                const comments = document.querySelectorAll(
                    '[role="article"] ul li, ' +
                    '.comment, ' +
                    '[data-testid*="comment"], ' +
                    'article section > div > div > div'
                );
                
                const currentCount = comments.length;
                console.log(`Comentarios encontrados: ${currentCount}`);
                
                if (currentCount === previousCount) {
                    stableCount++;
                } else {
                    stableCount = 0;
                    previousCount = currentCount;
                }
            }
            
            return document.documentElement.outerHTML;
        }
        
        return loadInstagramComments();
        """
        
        try:
            result = self.scrapfly.execute_javascript(url, javascript_code, 'instagram')
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
            
            # Selectores para comentarios de Instagram
            comment_selectors = [
                'article section ul li',
                '[data-testid*="comment"]',
                '.comment',
                'article section > div > div > div'
            ]
            
            comment_elements = []
            for selector in comment_selectors:
                elements = soup.select(selector)
                if elements:
                    comment_elements = elements
                    break
            
            # Filtrar elementos que realmente son comentarios
            filtered_comments = []
            for element in comment_elements:
                # Verificar que tenga texto y un enlace de usuario
                user_link = element.find('a', href=re.compile(r'^/[\w.]+/$'))
                comment_text = element.find(text=True, recursive=True)
                
                if user_link and comment_text and len(comment_text.strip()) > 0:
                    filtered_comments.append(element)
            
            # Procesar comentarios
            for i, element in enumerate(filtered_comments[:self.limits['max_comments_per_video']]):
                comment = self._extract_comment_data(element, i + 1)
                if comment:
                    comments.append(comment)
                    
        except Exception as e:
            print(f"⚠️ Error procesando comentarios: {str(e)}")
        
        return comments
    
    def _extract_comment_data(self, element, comment_id):
        """Extrae datos de un comentario individual"""
        try:
            # Extraer username desde el enlace
            user_link = element.find('a', href=re.compile(r'^/[\w.]+/$'))
            if not user_link:
                return None
                
            username = user_link.get('href', '').strip('/').replace('/', '')
            if not username:
                return None
            
            # Extraer texto del comentario
            # El texto suele estar después del enlace del usuario
            comment_text = ''
            text_elements = user_link.find_next_siblings(text=True)
            if text_elements:
                comment_text = ' '.join([t.strip() for t in text_elements if t.strip()])
            
            if not comment_text:
                # Buscar en spans o divs siguientes
                next_element = user_link.parent.find_next()
                if next_element:
                    comment_text = next_element.get_text(strip=True)
            
            # Extraer tiempo (Instagram usa "time" elements)
            time_element = element.find('time')
            time_posted = time_element.get('datetime', '') if time_element else 'N/A'
            if time_posted and time_posted != 'N/A':
                try:
                    time_posted = datetime.fromisoformat(time_posted.replace('Z', '+00:00')).strftime('%d-%m-%Y')
                except:
                    time_posted = time_element.get_text(strip=True)
            
            # Extraer likes (Instagram no siempre muestra likes de comentarios)
            likes = 0
            like_elements = element.find_all(text=re.compile(r'\d+\s*(like|me gusta)', re.I))
            if like_elements:
                like_match = re.search(r'(\d+)', like_elements[0])
                if like_match:
                    likes = int(like_match.group(1))
            
            # Buscar imagen de perfil
            profile_img = element.find('img')
            profile_pic = profile_img.get('src', '') if profile_img else ''
            
            # Determinar si es respuesta (Instagram anida las respuestas)
            is_reply = bool(element.find_parent('li')) and bool(element.find_parent('ul').find_parent('li'))
            
            if username and comment_text:
                return {
                    'comment_id': comment_id,
                    'nickname': username,  # Instagram username es también el display name
                    'username': f'@{username}',
                    'user_url': f'https://www.instagram.com/{username}/',
                    'text': comment_text.strip(),
                    'time': time_posted,
                    'likes': likes,
                    'profile_pic': profile_pic,
                    'followers': 'N/A',  # Se completará después
                    'is_reply': is_reply,
                    'replied_to': '',
                    'num_replies': 0
                }
                
        except Exception as e:
            print(f"⚠️ Error extrayendo comentario: {str(e)}")
        
        return None
    
    def _enrich_with_followers(self, comments):
        """Enriquece los comentarios con datos de seguidores"""
        unique_users = {}
        
        # Agrupar comentarios por usuario
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
                
                # Delay más largo para Instagram (más estricto)
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"  ⚠️ Error obteniendo seguidores para @{username}: {str(e)}")
                for comment in user_comments:
                    comment['followers'] = 'N/A'
        
        return comments
    
    def _get_user_followers(self, username):
        """Obtiene el número de seguidores de un usuario"""
        try:
            user_url = f"https://www.instagram.com/{username}/"
            
            config = self.scrapfly.create_scrape_config(user_url, 'instagram', {
                'render_js': False,  # Intentar sin JS primero
                'timeout': 15000
            })
            
            result = self.scrapfly.scrape_with_retry(config, max_retries=2)
            
            if result['success']:
                html = result['data']
                
                # Buscar en JSON estructurado
                follower_patterns = [
                    r'"edge_followed_by":\s*{\s*"count":\s*(\d+)',
                    r'"follower_count":(\d+)',
                    r'"followers":(\d+)',
                    r'(\d+)\s*followers'
                ]
                
                for pattern in follower_patterns:
                    match = re.search(pattern, html, re.IGNORECASE)
                    if match:
                        return self._format_number(int(match.group(1)))
                
                # Buscar en meta tags
                soup = BeautifulSoup(html, 'html.parser')
                meta_description = soup.find('meta', {'name': 'description'})
                if meta_description:
                    content = meta_description.get('content', '')
                    follower_match = re.search(r'(\d+(?:,\d+)*)\s*followers', content, re.IGNORECASE)
                    if follower_match:
                        number_str = follower_match.group(1).replace(',', '')
                        return self._format_number(int(number_str))
                
            return 'N/A'
            
        except Exception as e:
            print(f"    ⚠️ Error: {str(e)}")
            return 'N/A'
    
    def _format_number(self, number):
        """Formatea números grandes"""
        if number >= 1_000_000_000:
            return f"{number/1_000_000_000:.1f}B"
        elif number >= 1_000_000:
            return f"{number/1_000_000:.1f}M"
        elif number >= 1_000:
            return f"{number/1_000:.1f}K"
        else:
            return str(number)
    
    def get_post_id(self, url):
        """Extrae el ID del post de la URL"""
        patterns = [
            r'/p/([A-Za-z0-9_-]+)',
            r'/reel/([A-Za-z0-9_-]+)',
            r'/tv/([A-Za-z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None