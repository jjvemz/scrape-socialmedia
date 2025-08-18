#!/usr/bin/env python3
"""
Scraper específico para Facebook usando ScrapFly
"""

import re
import json
import time
import random
from bs4 import BeautifulSoup
from datetime import datetime
from utils.scrapfly_config import ScrapFlyConfig

class FacebookScraper:
    def __init__(self):
        self.scrapfly = ScrapFlyConfig()
        self.limits = self.scrapfly.get_platform_limits('facebook')
        
    def scrape_comments(self, url):
        """
        Extrae comentarios y metadatos de un video de Facebook
        
        Args:
            url (str): URL del video de Facebook
            
        Returns:
            dict: Resultado con éxito/error y datos extraídos
        """
        try:
            print(f"📘 Iniciando scraping de Facebook: {url[:50]}...")
            
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
                'error': f"Error en Facebook scraper: {str(e)}",
                'data': None
            }
    
    def _get_initial_page(self, url):
        """Obtiene la página inicial del video"""
        try:
            config = self.scrapfly.create_scrape_config(url, 'facebook')
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
                if script.string and ('attachments' in script.string or 'videoData' in script.string):
                    # Buscar JSON embebido
                    json_matches = re.finditer(r'\{[^{}]*"attachments"[^{}]*\}', script.string)
                    for match in json_matches:
                        try:
                            data = json.loads(match.group())
                            metadata.update(self._parse_facebook_json(data))
                        except:
                            continue
            
            # Fallback: extraer desde meta tags y elementos visibles
            if not metadata:
                metadata = self._extract_metadata_fallback(soup)
                
        except Exception as e:
            print(f"⚠️ Error extrayendo metadatos: {str(e)}")
        
        return metadata
    
    def _parse_facebook_json(self, data):
        """Parsea los datos JSON de Facebook"""
        metadata = {}
        
        try:
            # Facebook tiene estructuras JSON complejas
            if 'attachments' in data:
                attachments = data['attachments']
                if isinstance(attachments, list) and attachments:
                    attachment = attachments[0]
                    
                    # Información del video
                    if 'media' in attachment:
                        media = attachment['media']
                        metadata['video_id'] = media.get('id', '')
                        
                        # Estadísticas
                        if 'feedback' in media:
                            feedback = media['feedback']
                            metadata['likes'] = feedback.get('reaction_count', {}).get('count', 0)
                            metadata['total_comments_claimed'] = feedback.get('comment_count', {}).get('total_count', 0)
                            metadata['shares'] = feedback.get('share_count', {}).get('count', 0)
            
            # Información del autor
            if 'owner' in data:
                owner = data['owner']
                metadata['publisher_nickname'] = owner.get('name', '')
                metadata['publisher_username'] = owner.get('username', '') or owner.get('id', '')
                metadata['publisher_url'] = f"https://www.facebook.com/{owner.get('username', owner.get('id', ''))}"
            
            # Fecha de publicación
            if 'created_time' in data:
                try:
                    created_time = datetime.fromisoformat(data['created_time'].replace('Z', '+00:00'))
                    metadata['publish_time'] = created_time.strftime('%d-%m-%Y')
                except:
                    pass
            
            # Descripción/texto
            if 'message' in data:
                metadata['description'] = data['message']
                
        except Exception as e:
            print(f"⚠️ Error parseando JSON Facebook: {str(e)}")
        
        return metadata
    
    def _extract_metadata_fallback(self, soup):
        """Método fallback para extraer metadatos"""
        metadata = {}
        
        try:
            # Meta tags de Open Graph
            og_title = soup.find('meta', property='og:title')
            if og_title:
                content = og_title.get('content', '')
                # Facebook titles suelen tener el nombre del autor
                metadata['publisher_nickname'] = content.split(' - ')[0] if ' - ' in content else content
            
            og_description = soup.find('meta', property='og:description')
            if og_description:
                metadata['description'] = og_description.get('content', '')
            
            og_url = soup.find('meta', property='og:url')
            if og_url:
                url = og_url.get('content', '')
                # Extraer username/page de la URL
                url_match = re.search(r'facebook\.com/([^/]+)', url)
                if url_match:
                    page_name = url_match.group(1)
                    if page_name not in ['watch', 'video.php', 'photo.php']:
                        metadata['publisher_username'] = page_name
                        metadata['publisher_url'] = f"https://www.facebook.com/{page_name}"
            
            # Buscar estadísticas en el HTML
            # Facebook cambia frecuentemente sus selectores, usar patrones flexibles
            stats_text = str(soup)
            
            # Buscar likes
            like_patterns = [
                r'(\d+(?:,\d+)*)\s*(?:like|me gusta)',
                r'"reaction_count"[^}]*"count":(\d+)',
                r'"like_count":(\d+)'
            ]
            
            for pattern in like_patterns:
                match = re.search(pattern, stats_text, re.IGNORECASE)
                if match:
                    likes_str = match.group(1).replace(',', '')
                    metadata['likes'] = int(likes_str)
                    break
            
            # Buscar comentarios
            comment_patterns = [
                r'(\d+(?:,\d+)*)\s*(?:comment|comentario)',
                r'"comment_count"[^}]*"total_count":(\d+)',
                r'"comments_count":(\d+)'
            ]
            
            for pattern in comment_patterns:
                match = re.search(pattern, stats_text, re.IGNORECASE)
                if match:
                    comments_str = match.group(1).replace(',', '')
                    metadata['total_comments_claimed'] = int(comments_str)
                    break
            
            # Buscar shares
            share_patterns = [
                r'(\d+(?:,\d+)*)\s*(?:share|compartir)',
                r'"share_count"[^}]*"count":(\d+)',
                r'"shares_count":(\d+)'
            ]
            
            for pattern in share_patterns:
                match = re.search(pattern, stats_text, re.IGNORECASE)
                if match:
                    shares_str = match.group(1).replace(',', '')
                    metadata['shares'] = int(shares_str)
                    break
                    
        except Exception as e:
            print(f"⚠️ Error en metadata fallback: {str(e)}")
        
        return metadata
    
    def _load_comments_with_js(self, url):
        """Carga comentarios usando JavaScript"""
        javascript_code = """
        async function loadFacebookComments() {
            let previousCount = 0;
            let stableCount = 0;
            const maxStable = 5;
            
            while (stableCount < maxStable) {
                // Buscar botones de "Ver más comentarios" o "Load more comments"
                const loadMoreButtons = document.querySelectorAll(
                    'div[role="button"], span[role="button"], a[role="button"]'
                ).filter(btn => {
                    const text = btn.textContent.toLowerCase();
                    return text.includes('view') && (text.includes('more') || text.includes('comment')) ||
                           text.includes('ver') && (text.includes('más') || text.includes('comentario')) ||
                           text.includes('load') && text.includes('more') ||
                           text.includes('show') && text.includes('more');
                });
                
                // Hacer clic en los botones encontrados
                let clicked = false;
                loadMoreButtons.forEach(btn => {
                    if (btn.offsetParent !== null && !btn.disabled) {
                        btn.click();
                        clicked = true;
                    }
                });
                
                if (clicked) {
                    await new Promise(resolve => setTimeout(resolve, 3000));
                }
                
                // Scroll para activar lazy loading
                window.scrollTo(0, document.body.scrollHeight);
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // Contar comentarios actuales
                const comments = document.querySelectorAll(
                    '[data-testid*="comment"], ' +
                    '[role="article"] [role="article"], ' +
                    'div[data-sigil="comment"], ' +
                    '.UFIComment, ' +
                    '[data-ft*="comment"]'
                );
                
                const currentCount = comments.length;
                console.log(`Comentarios encontrados: ${currentCount}`);
                
                if (currentCount === previousCount) {
                    stableCount++;
                } else {
                    stableCount = 0;
                    previousCount = currentCount;
                }
                
                // Buscar y expandir respuestas a comentarios
                const replyButtons = document.querySelectorAll(
                    'div[role="button"], span[role="button"]'
                ).filter(btn => {
                    const text = btn.textContent.toLowerCase();
                    return (text.includes('repl') && text.includes('view')) ||
                           (text.includes('respuesta') && text.includes('ver')) ||
                           text.includes('show replies');
                });
                
                replyButtons.forEach(btn => {
                    if (btn.offsetParent !== null) {
                        btn.click();
                    }
                });
                
                if (replyButtons.length > 0) {
                    await new Promise(resolve => setTimeout(resolve, 2000));
                }
            }
            
            return document.documentElement.outerHTML;
        }
        
        return loadFacebookComments();
        """
        
        try:
            result = self.scrapfly.execute_javascript(url, javascript_code, 'facebook')
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
            
            # Selectores para comentarios de Facebook
            comment_selectors = [
                '[data-testid*="comment"]',
                '[role="article"] [role="article"]',
                'div[data-sigil="comment"]',
                '.UFIComment',
                '[data-ft*="comment"]'
            ]
            
            comment_elements = []
            for selector in comment_selectors:
                elements = soup.select(selector)
                if elements:
                    comment_elements = elements
                    print(f"  📝 Encontrados {len(elements)} comentarios con selector: {selector}")
                    break
            
            # Si no encontramos con selectores específicos, buscar patrones más generales
            if not comment_elements:
                # Buscar divs que contengan enlaces de perfil y texto
                potential_comments = soup.find_all('div', recursive=True)
                for div in potential_comments:
                    # Verificar si contiene un enlace de perfil y texto
                    profile_link = div.find('a', href=re.compile(r'/[^/]+\?'))
                    has_text = div.get_text(strip=True)
                    
                    if profile_link and has_text and len(has_text) > 10:
                        # Evitar duplicados
                        if div not in comment_elements:
                            comment_elements.append(div)
                
                print(f"  📝 Encontrados {len(comment_elements)} comentarios con búsqueda general")
            
            # Procesar comentarios
            processed_count = 0
            for i, element in enumerate(comment_elements[:self.limits['max_comments_per_video']]):
                comment = self._extract_comment_data(element, i + 1)
                if comment:
                    comments.append(comment)
                    processed_count += 1
            
            print(f"  ✅ Procesados {processed_count} comentarios válidos")
                    
        except Exception as e:
            print(f"⚠️ Error procesando comentarios: {str(e)}")
        
        return comments
    
    def _extract_comment_data(self, element, comment_id):
        """Extrae datos de un comentario individual"""
        try:
            # Extraer enlace del usuario
            user_links = element.find_all('a', href=re.compile(r'facebook\.com'))
            user_link = None
            
            for link in user_links:
                href = link.get('href', '')
                # Buscar enlaces que parezcan perfiles (no pages, groups, etc.)
                if re.match(r'https?://[^/]*facebook\.com/[^/]+\??', href):
                    if not any(exclude in href for exclude in ['/pages/', '/groups/', '/events/']):
                        user_link = link
                        break
            
            if not user_link:
                return None
            
            # Extraer username y nickname
            username = ''
            nickname = user_link.get_text(strip=True)
            
            href = user_link.get('href', '')
            # Extraer username de la URL
            username_match = re.search(r'facebook\.com/([^/?]+)', href)
            if username_match:
                username = username_match.group(1)
            
            if not username or not nickname:
                return None
            
            # Extraer texto del comentario
            # El comentario suele estar en el mismo contenedor que el enlace del usuario
            comment_text = ''
            
            # Buscar texto después del enlace del usuario
            parent = user_link.parent
            while parent and not comment_text:
                # Buscar spans o divs con texto
                text_elements = parent.find_all(['span', 'div'], recursive=False)
                for text_elem in text_elements:
                    text = text_elem.get_text(strip=True)
                    if text and text != nickname and len(text) > 3:
                        comment_text = text
                        break
                
                if not comment_text:
                    # Buscar hermanos del enlace
                    for sibling in user_link.next_siblings:
                        if hasattr(sibling, 'get_text'):
                            text = sibling.get_text(strip=True)
                            if text and len(text) > 3:
                                comment_text = text
                                break
                
                parent = parent.parent
            
            if not comment_text:
                return None
            
            # Extraer tiempo
            time_posted = 'N/A'
            time_elements = element.find_all(['time', 'abbr', 'span'])
            for time_elem in time_elements:
                # Buscar elementos que contengan tiempo
                time_text = time_elem.get_text(strip=True)
                if any(keyword in time_text.lower() for keyword in ['ago', 'min', 'hour', 'day', 'week', 'month', 'year', 'hace', 'hora', 'día']):
                    time_posted = time_text
                    break
                
                # Buscar datetime attribute
                datetime_attr = time_elem.get('datetime') or time_elem.get('data-utime')
                if datetime_attr:
                    try:
                        if datetime_attr.isdigit():
                            time_posted = datetime.fromtimestamp(int(datetime_attr)).strftime('%d-%m-%Y')
                        else:
                            time_posted = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00')).strftime('%d-%m-%Y')
                        break
                    except:
                        pass
            
            # Extraer likes (Facebook raramente muestra likes de comentarios públicamente)
            likes = 0
            like_elements = element.find_all(text=re.compile(r'\d+.*like', re.I))
            if like_elements:
                like_match = re.search(r'(\d+)', like_elements[0])
                if like_match:
                    likes = int(like_match.group(1))
            
            # Buscar imagen de perfil
            profile_pic = ''
            img_elements = element.find_all('img')
            for img in img_elements:
                src = img.get('src', '')
                if 'profile' in src.lower() or 'avatar' in src.lower():
                    profile_pic = src
                    break
            
            # Determinar si es respuesta
            is_reply = bool(element.find_parent(['ul', 'ol'])) or 'reply' in str(element.get('class', [])).lower()
            
            return {
                'comment_id': comment_id,
                'nickname': nickname,
                'username': username,
                'user_url': f'https://www.facebook.com/{username}',
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
            username = comment['username']
            if username not in unique_users:
                unique_users[username] = []
            unique_users[username].append(comment)
        
        # Facebook es más restrictivo, obtener seguidores solo para algunos usuarios
        processed_users = 0
        max_users_to_process = min(len(unique_users), 20)  # Límite para Facebook
        
        for username, user_comments in list(unique_users.items())[:max_users_to_process]:
            try:
                print(f"  📊 Obteniendo seguidores para {username}...")
                followers = self._get_user_followers(username)
                
                # Actualizar todos los comentarios de este usuario
                for comment in user_comments:
                    comment['followers'] = followers
                
                processed_users += 1
                
                # Delay más largo para Facebook
                time.sleep(random.uniform(3, 6))
                
            except Exception as e:
                print(f"  ⚠️ Error obteniendo seguidores para {username}: {str(e)}")
                for comment in user_comments:
                    comment['followers'] = 'N/A'
        
        # Para usuarios no procesados, marcar como N/A
        remaining_users = list(unique_users.keys())[max_users_to_process:]
        for username in remaining_users:
            for comment in unique_users[username]:
                comment['followers'] = 'N/A'
        
        if remaining_users:
            print(f"  ⏭️ Omitidos {len(remaining_users)} usuarios para evitar rate limiting")
        
        return comments
    
    def _get_user_followers(self, username):
        """Obtiene el número de seguidores de un usuario (limitado en Facebook)"""
        try:
            # Facebook no expone fácilmente los seguidores de perfiles personales
            # Solo funciona bien para páginas públicas
            user_url = f"https://www.facebook.com/{username}"
            
            config = self.scrapfly.create_scrape_config(user_url, 'facebook', {
                'render_js': False,
                'timeout': 15000
            })
            
            result = self.scrapfly.scrape_with_retry(config, max_retries=1)
            
            if result['success']:
                html = result['data']
                
                # Buscar indicadores de páginas (que sí muestran seguidores)
                follower_patterns = [
                    r'(\d+(?:,\d+)*)\s*(?:follower|seguidor)',
                    r'(\d+(?:\.\d+)?[KMB]?)\s*(?:follower|seguidor)',
                    r'"follower_count":(\d+)',
                    r'"subscribers_count":(\d+)'
                ]
                
                for pattern in follower_patterns:
                    match = re.search(pattern, html, re.IGNORECASE)
                    if match:
                        number_str = match.group(1).replace(',', '')
                        if number_str.isdigit():
                            return self._format_number(int(number_str))
                        else:
                            # Manejar K, M, B
                            return self._parse_abbreviated_number(number_str)
                
                # Buscar en meta tags
                soup = BeautifulSoup(html, 'html.parser')
                meta_description = soup.find('meta', {'name': 'description'})
                if meta_description:
                    content = meta_description.get('content', '')
                    if 'page' in content.lower():  # Es una página
                        follower_match = re.search(r'(\d+(?:,\d+)*)\s*people follow', content, re.IGNORECASE)
                        if follower_match:
                            number_str = follower_match.group(1).replace(',', '')
                            return self._format_number(int(number_str))
                
            return 'Private'  # Perfil privado o personal
            
        except Exception as e:
            print(f"    ⚠️ Error: {str(e)}")
            return 'N/A'
    
    def _parse_abbreviated_number(self, text):
        """Parsea números abreviados (1.2K, 5M, etc.)"""
        text = text.upper().strip()
        
        if 'K' in text:
            number = float(text.replace('K', ''))
            return self._format_number(int(number * 1000))
        elif 'M' in text:
            number = float(text.replace('M', ''))
            return self._format_number(int(number * 1000000))
        elif 'B' in text:
            number = float(text.replace('B', ''))
            return self._format_number(int(number * 1000000000))
        else:
            try:
                return self._format_number(int(float(text)))
            except:
                return text
    
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
    
    def get_video_id(self, url):
        """Extrae el ID del video de la URL"""
        patterns = [
            r'v=(\d+)',
            r'/videos/(\d+)',
            r'watch\?v=(\d+)',
            r'fb\.watch/([a-zA-Z0-9]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None