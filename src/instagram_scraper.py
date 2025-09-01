#!/usr/bin/env python3
"""
Instagram Scraper with Enhanced Real Data Extraction
Extracts real comments, usernames, user links, and follower counts from Instagram posts/reels
"""

import re
import json
import time
import random
import html
import codecs
from bs4 import BeautifulSoup
from datetime import datetime
from utils.scrapfly_config import ScrapFlyConfig
from utils.instagram_auth import InstagramAuth
from utils.logger import get_logger

class InstagramScraper:
    def __init__(self):
        self.logger = get_logger()
        self.scrapfly = ScrapFlyConfig()
        self.limits = self.scrapfly.get_platform_limits('instagram')
        self.auth = InstagramAuth(self.scrapfly.client)
        self.is_logged_in = False
        
        self.logger.info("Instagram scraper initialized")
        
        # Try to load existing session
        if self.auth.load_session():
            self.is_logged_in = self.auth.is_authenticated()
            if self.is_logged_in:
                self.logger.info("Using existing Instagram session")
            else:
                self.logger.warning("Session loaded but not authenticated")
    
    def _decode_unicode_text(self, text):
        """
        Properly decode Unicode text including Spanish accents and emojis
        
        Args:
            text (str): Text that may contain Unicode escapes or encoded characters
            
        Returns:
            str: Properly decoded Unicode text
        """
        if not text or not isinstance(text, str):
            return text
        
        try:
            # Step 1: Handle HTML entities (like &amp; &lt; &gt; etc.)
            text = html.unescape(text)
            
            # Step 2: Handle double-encoded Unicode escapes like \\u00e1
            if '\\\\u' in text:
                text = text.replace('\\\\u', '\\u')
            
            # Step 3: Handle Unicode escapes with proper emoji support
            if '\\u' in text:
                try:
                    # Use json.loads for proper Unicode handling including emoji surrogates
                    import json
                    # Wrap in quotes to make it a valid JSON string
                    json_text = f'"{text}"'
                    decoded = json.loads(json_text)
                    text = decoded
                except (json.JSONDecodeError, ValueError):
                    try:
                        # Fallback to bytes decode method
                        text = text.encode('utf-8').decode('unicode_escape')
                    except UnicodeDecodeError:
                        try:
                            # Final fallback with codecs
                            text = codecs.decode(text, 'unicode_escape')
                        except:
                            # If all fails, just remove the escape sequences
                            import re
                            text = re.sub(r'\\u[0-9a-fA-F]{4}', '', text)
            
            # Step 4: Ensure proper UTF-8 encoding
            if isinstance(text, bytes):
                text = text.decode('utf-8', errors='replace')
            
            # Step 5: Normalize the text to handle any remaining encoding issues
            text = text.encode('utf-8', errors='replace').decode('utf-8')
            
            return text
            
        except Exception as e:
            self.logger.debug(f"Unicode decoding error for text: {str(e)}")
            # Return original text if decoding fails
            return str(text)
    
    def _clean_extracted_text(self, text):
        """
        Clean and normalize extracted text while preserving Unicode characters
        
        Args:
            text (str): Raw extracted text
            
        Returns:
            str: Cleaned text with proper Unicode handling
        """
        if not text:
            return ""
        
        # First decode Unicode properly
        text = self._decode_unicode_text(text)
        
        # Clean common extraction artifacts while preserving Spanish characters and emojis
        text = text.strip()
        
        # Remove multiple whitespaces but keep structure
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common Instagram UI text that might get extracted
        ui_patterns = [
            r'^(likes?|me gusta|comentarios?|comments?|compartir|share|seguir|follow)\s*',
            r'\s*(likes?|me gusta|comentarios?|comments?|compartir|share|seguir|follow)$'
        ]
        
        for pattern in ui_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def _normalize_username(self, username):
        """
        Normalize username while preserving Unicode characters
        
        Args:
            username (str): Raw username
            
        Returns:
            str: Normalized username
        """
        if not username:
            return ""
        
        # Decode Unicode first
        username = self._decode_unicode_text(username)
        
        # Clean up common artifacts
        username = username.strip().replace('@', '')
        
        return username
    
    def login(self, username, password):
        """Login to Instagram for authenticated scraping"""
        self.logger.info(f"Attempting Instagram login for user: {username}")
        
        result = self.auth.login(username, password)
        
        if result['success']:
            self.is_logged_in = True
            self.logger.log_auth_attempt(username, success=True)
            self.logger.info("Instagram login successful - authenticated scraping enabled")
        else:
            self.logger.log_auth_attempt(username, success=False, error=result.get('error'))
            self.logger.error(f"Instagram login failed: {result.get('error', 'Unknown error')}")
        
        return result
        
    def scrape_comments(self, url):
        """
        Extract real comments and user data from Instagram post/reel
        
        Args:
            url (str): Instagram post URL
            
        Returns:
            dict: Result with success/error and extracted data
        """
        try:
            self.logger.info(f"Starting Instagram scraping", {'url': url, 'authenticated': self.is_logged_in})
            
            # Step 1: Get page with embedded JavaScript data
            self.logger.debug("Step 1: Loading page with embedded data")
            result = self._get_page_with_embedded_data(url)
            if not result['success']:
                self.logger.error("Failed to load page", {'error': result.get('error')})
                return result
            
            self.logger.debug("Page loaded successfully", {'html_length': len(result['html'])})
            
            # Step 2: Extract metadata
            self.logger.debug("Step 2: Extracting metadata")
            metadata = self._extract_post_metadata(result['html'])
            self.logger.debug("Metadata extracted", {'fields': list(metadata.keys())})
            
            # Step 3: Extract comments using multiple strategies
            self.logger.debug("Step 3: Extracting comments")
            comments = self._extract_real_comments(result['html'], url)
            
            # Log initial extraction results
            real_usernames = len([c for c in comments if not c.get('username', '').startswith('@user_')])
            comments_with_likes = len([c for c in comments if c.get('likes', 0) > 0])
            
            self.logger.info("Initial extraction complete", {
                'total_comments': len(comments),
                'real_usernames': real_usernames,
                'comments_with_likes': comments_with_likes
            })
            
            # Step 4: Enrich comments with follower data (if we have real users)
            if comments and any(c.get('username', '').startswith('@') and 'user_' not in c.get('username', '') for c in comments):
                self.logger.info(f"Step 4: Enriching {len(comments)} comments with follower data")
                comments = self._enrich_with_followers(comments)
            else:
                self.logger.warning("Skipping follower enrichment - no real users found or not authenticated")
            
            # Final summary
            final_real_usernames = len([c for c in comments if not c.get('username', '').startswith('@user_')])
            final_comments_with_likes = len([c for c in comments if c.get('likes', 0) > 0])
            final_comments_with_followers = len([c for c in comments if c.get('followers', 'N/A') != 'N/A'])
            
            self.logger.log_scraping_summary(
                url, len(comments), final_real_usernames, 
                final_comments_with_likes, final_comments_with_followers
            )
            
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
            self.logger.error("Critical error in scrape_comments", {'error': str(e)}, exc_info=True)
            return {
                'success': False,
                'error': f"Instagram scraper error: {str(e)}",
                'data': None
            }
    
    def _get_page_with_embedded_data(self, url):
        """Get Instagram page with embedded JSON data"""
        try:
            # Force authentication requirement
            if not self.is_logged_in:
                self.logger.warning("Not authenticated - this will likely result in 429 errors")
                self.logger.info("Attempting to use credentials from config file")
                
                # Try to auto-login using credentials from config
                try:
                    from instagram_config_example import INSTAGRAM_CREDENTIALS
                    if INSTAGRAM_CREDENTIALS['username'] != 'your_instagram_username':
                        self.logger.info("Auto-login with config credentials")
                        login_result = self.login(
                            INSTAGRAM_CREDENTIALS['username'], 
                            INSTAGRAM_CREDENTIALS['password']
                        )
                        if not login_result['success']:
                            self.logger.error("Auto-login failed", {'error': login_result.get('error')})
                except ImportError:
                    self.logger.warning("No credentials config found - continuing without auth")
            
            # Simplified configuration to avoid timeouts
            config_options = {
                'render_js': True,
                'wait_for_selector': 'article',
                'cost_budget': 55,  # Lower budget
                'cache': False,
                'retry': False,  # Disable retry
                'timeout': 30000  # 30 seconds
            }
            
            # Only add JS if we're not getting timeouts
            if not hasattr(self, '_timeout_count') or self._timeout_count < 2:
                config_options['js'] = self._get_simplified_js_code()
            else:
                self.logger.warning("Skipping JS execution due to previous timeouts")
            
            # Use authenticated headers if logged in
            if self.is_logged_in:
                auth_headers = self.auth.get_authenticated_headers()
                config_options['additional_headers'] = auth_headers
                config_options['session'] = 'instagram-authenticated-session'
                self.logger.info("Using authenticated session for scraping")
            else:
                self.logger.warning("Proceeding without authentication - expect limited results")
            
            self.logger.log_request(url, headers=config_options.get('additional_headers'))
            
            config = self.scrapfly.create_scrape_config(url, 'instagram', config_options)
            
            result = self.scrapfly.scrape_with_retry(config)
            
            if result['success']:
                self.logger.log_response(url, 200, len(result['data']))
                return {
                    'success': True,
                    'html': result['data']
                }
            else:
                error = result.get('error', 'Unknown error')
                self.logger.log_response(url, None, None, error)
                
                # Handle specific errors
                if '429' in str(error):
                    self.logger.log_rate_limit(url)
                    if not self.is_logged_in:
                        self.logger.error("429 error likely due to lack of authentication")
                
                # Track timeouts for future requests
                if '504' in str(error) or 'TIMEOUT' in str(error):
                    if not hasattr(self, '_timeout_count'):
                        self._timeout_count = 0
                    self._timeout_count += 1
                    self.logger.warning(f"Timeout #{self._timeout_count} detected")
                
                return {
                    'success': False,
                    'error': error
                }
                
        except Exception as e:
            self.logger.error("Exception in _get_page_with_embedded_data", {'error': str(e)}, exc_info=True)
            return {
                'success': False,
                'error': f"Error loading page: {str(e)}"
            }
    
    def _get_improved_js_code(self):
        """Improved JavaScript code for better comment extraction"""
        return """
        async function extractInstagramData() {
            console.log('Starting improved Instagram data extraction...');
            
            // Wait for page to load
            await new Promise(resolve => setTimeout(resolve, 5000));
            
            // Function to scroll and load comments
            async function loadAllComments() {
                let previousHeight = 0;
                let currentHeight = document.body.scrollHeight;
                let attempts = 0;
                const maxAttempts = 10;
                
                while (attempts < maxAttempts && currentHeight > previousHeight) {
                    previousHeight = currentHeight;
                    
                    // Scroll to bottom
                    window.scrollTo(0, document.body.scrollHeight);
                    await new Promise(resolve => setTimeout(resolve, 3000));
                    
                    // Try to click "View more comments" buttons
                    const viewMoreButtons = document.querySelectorAll('button, span, div');
                    for (const button of viewMoreButtons) {
                        const text = button.textContent.toLowerCase();
                        if (text.includes('view more') || text.includes('ver más') || 
                            text.includes('load more') || text.includes('mostrar más')) {
                            try {
                                button.click();
                                await new Promise(resolve => setTimeout(resolve, 2000));
                            } catch (e) {}
                        }
                    }
                    
                    currentHeight = document.body.scrollHeight;
                    attempts++;
                }
                
                console.log(`Completed loading after ${attempts} attempts`);
            }
            
            // Load all comments
            await loadAllComments();
            
            // Extract window._sharedData or other embedded data
            let embeddedData = {};
            
            // Try to find _sharedData
            if (window._sharedData) {
                embeddedData._sharedData = window._sharedData;
            }
            
            // Try to find other embedded JSON data
            const scripts = document.querySelectorAll('script[type="application/ld+json"]');
            embeddedData.jsonLD = [];
            scripts.forEach(script => {
                try {
                    embeddedData.jsonLD.push(JSON.parse(script.textContent));
                } catch (e) {}
            });
            
            // Store embedded data in a global variable for extraction
            window.extractedData = embeddedData;
            
            console.log('Extraction complete');
            return document.documentElement.outerHTML;
        }
        
        return extractInstagramData();
        """
    
    def _get_simplified_js_code(self):
        """Simplified JavaScript to reduce timeout risk"""
        return """
        async function quickExtract() {
            // Wait a bit for page load
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Try to scroll once to load some comments
            window.scrollTo(0, document.body.scrollHeight / 2);
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Return HTML without complex operations
            return document.documentElement.outerHTML;
        }
        
        return quickExtract();
        """
    
    def _extract_post_metadata(self, html):
        """Extract post metadata from HTML"""
        metadata = {}
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract from JSON-LD
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'author' in data:
                        if 'author' in data:
                            author = data['author']
                            raw_nickname = author.get('name', '')
                            raw_username = author.get('alternateName', '').replace('@', '')
                            
                            metadata['publisher_nickname'] = self._clean_extracted_text(raw_nickname)
                            metadata['publisher_username'] = '@' + self._normalize_username(raw_username)
                            metadata['publisher_url'] = author.get('url', '')
                        
                        if 'caption' in data:
                            raw_caption = data['caption']
                            metadata['description'] = self._clean_extracted_text(raw_caption)
                        
                        if 'interactionStatistic' in data:
                            for stat in data['interactionStatistic']:
                                interaction_type = stat.get('interactionType', {}).get('@type', '')
                                if 'LikeAction' in interaction_type:
                                    metadata['likes'] = stat.get('userInteractionCount', 0)
                                elif 'CommentAction' in interaction_type:
                                    metadata['total_comments_claimed'] = stat.get('userInteractionCount', 0)
                except:
                    continue
            
            # Extract from meta tags as fallback
            if not metadata:
                og_title = soup.find('meta', property='og:title')
                if og_title:
                    content = og_title.get('content', '')
                    username_match = re.search(r'@(\w+)', content)
                    if username_match:
                        raw_username = username_match.group(1)
                        metadata['publisher_username'] = '@' + self._normalize_username(raw_username)
                
                og_description = soup.find('meta', property='og:description')
                if og_description:
                    raw_description = og_description.get('content', '')
                    metadata['description'] = self._clean_extracted_text(raw_description)
            
        except Exception as e:
            print(f"Error extracting metadata: {str(e)}")
        
        return metadata
    
    def _extract_real_comments(self, html, url):
        """Extract real comments from Instagram HTML"""
        comments = []
        
        try:
            self.logger.debug("Starting comment extraction with multiple strategies")
            
            # Strategy 1: Extract from embedded JSON data
            self.logger.log_extraction_attempt("Embedded JSON", url)
            json_comments = self._extract_from_embedded_json(html)
            comments.extend(json_comments)
            self.logger.debug(f"Strategy 1 (JSON): Found {len(json_comments)} comments")
            
            # Strategy 2: Extract from HTML structure
            if len(comments) == 0:
                self.logger.log_extraction_attempt("HTML Structure", url)
                html_comments = self._extract_from_html_structure(html)
                comments.extend(html_comments)
                self.logger.debug(f"Strategy 2 (HTML): Found {len(html_comments)} comments")
            
            # Strategy 3: Use ScrapFly's direct API approach
            if len(comments) == 0:
                self.logger.log_extraction_attempt("Direct API", url)
                api_comments = self._extract_with_direct_api(url)
                comments.extend(api_comments)
                self.logger.debug(f"Strategy 3 (API): Found {len(api_comments)} comments")
            
            # Remove duplicates and limit results
            self.logger.debug(f"Removing duplicates from {len(comments)} total comments")
            unique_comments = self._remove_duplicate_comments(comments)
            self.logger.debug(f"After deduplication: {len(unique_comments)} unique comments")
            
            final_comments = unique_comments[:self.limits['max_comments_per_video']]
            
            # Log individual comment details for debugging
            for comment in final_comments[:5]:  # Log first 5 for debugging
                self.logger.log_comment_data(
                    comment.get('comment_id', 'N/A'),
                    comment.get('username', 'N/A'),
                    len(comment.get('text', '')),
                    comment.get('likes', 0),
                    comment.get('followers', 'N/A') != 'N/A'
                )
            
            self.logger.info(f"Comment extraction complete: {len(final_comments)} comments extracted")
            return final_comments
            
        except Exception as e:
            self.logger.error("Critical error in _extract_real_comments", {'error': str(e)}, exc_info=True)
            return []
    
    def _extract_from_embedded_json(self, html):
        """Extract comments from embedded JSON data"""
        comments = []
        
        try:
            # Look for _sharedData in script tags
            patterns = [
                r'window\._sharedData\s*=\s*({.+?});',
                r'"edge_media_to_comment"\s*:\s*({.+?"edges"\s*:\s*\[.+?\]})',
                r'"comments"\s*:\s*(\[.+?\])',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html, re.DOTALL)
                for match in matches:
                    try:
                        if match.startswith('{'):
                            data = json.loads(match)
                            extracted = self._parse_comment_json(data)
                            if extracted:
                                comments.extend(extracted)
                                if len(comments) > 0:
                                    print(f"Extracted {len(extracted)} comments from JSON pattern")
                                    break
                    except:
                        continue
                
                if len(comments) > 0:
                    break
            
        except Exception as e:
            print(f"Error extracting from JSON: {str(e)}")
        
        return comments
    
    def _parse_comment_json(self, data):
        """Parse comments from JSON data structure"""
        comments = []
        
        try:
            # Handle _sharedData structure
            if 'entry_data' in data:
                entry_data = data['entry_data']
                pages = entry_data.get('PostPage', []) or entry_data.get('ProfilePage', [])
                
                if pages:
                    page_data = pages[0]
                    graphql = page_data.get('graphql', {})
                    
                    if 'shortcode_media' in graphql:
                        media = graphql['shortcode_media']
                        edge_comments = media.get('edge_media_to_comment', {})
                        edges = edge_comments.get('edges', [])
                        
                        for i, edge in enumerate(edges):
                            node = edge.get('node', {})
                            if node.get('text'):
                                owner = node.get('owner', {})
                                username = owner.get('username', f'user_{i+1}')
                                
                                # Clean text and username with Unicode support
                                raw_text = node.get('text', '')
                                clean_text = self._clean_extracted_text(raw_text)
                                clean_username = self._normalize_username(username)
                                clean_nickname = self._clean_extracted_text(owner.get('full_name', username))
                                
                                comment = {
                                    'comment_id': i + 1,
                                    'nickname': clean_nickname,
                                    'username': f'@{clean_username}',
                                    'user_url': f'https://www.instagram.com/{clean_username}/',
                                    'text': clean_text,
                                    'time': self._format_timestamp(node.get('created_at')),
                                    'likes': node.get('edge_liked_by', {}).get('count', 0),
                                    'profile_pic': owner.get('profile_pic_url', ''),
                                    'followers': 'N/A',
                                    'is_reply': False,
                                    'replied_to': '',
                                    'num_replies': 0
                                }
                                comments.append(comment)
            
            # Handle direct comment edge structure
            elif 'edges' in data:
                edges = data['edges']
                for i, edge in enumerate(edges):
                    node = edge.get('node', {})
                    if node.get('text'):
                        owner = node.get('owner', {})
                        username = owner.get('username', f'user_{i+1}')
                        
                        # Clean text and username with Unicode support
                        raw_text = node.get('text', '')
                        clean_text = self._clean_extracted_text(raw_text)
                        clean_username = self._normalize_username(username)
                        clean_nickname = self._clean_extracted_text(owner.get('full_name', username))
                        
                        comment = {
                            'comment_id': i + 1,
                            'nickname': clean_nickname,
                            'username': f'@{clean_username}',
                            'user_url': f'https://www.instagram.com/{clean_username}/',
                            'text': clean_text,
                            'time': self._format_timestamp(node.get('created_at')),
                            'likes': node.get('edge_liked_by', {}).get('count', 0),
                            'profile_pic': owner.get('profile_pic_url', ''),
                            'followers': 'N/A',
                            'is_reply': False,
                            'replied_to': '',
                            'num_replies': 0
                        }
                        comments.append(comment)
            
        except Exception as e:
            print(f"Error parsing comment JSON: {str(e)}")
        
        return comments
    
    def _extract_from_html_structure(self, html):
        """Extract comments from HTML DOM structure"""
        comments = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for comment-like structures
            selectors = [
                'article section ul li',
                'div[role="button"] span',
                'article section div div span',
                '[data-testid*="comment"]'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                
                for i, element in enumerate(elements):
                    # Look for username link
                    user_link = element.find('a', href=re.compile(r'^/[\w.]+/?$'))
                    if user_link:
                        username = user_link.get('href', '').strip('/').split('/')[0]
                        
                        # Get comment text (excluding username)
                        full_text = element.get_text(strip=True)
                        raw_comment_text = full_text.replace(username, '').strip()
                        
                        # Clean and decode the text properly
                        comment_text = self._clean_extracted_text(raw_comment_text)
                        clean_username = self._normalize_username(username)
                        
                        # Skip if it doesn't look like a real comment
                        if (len(comment_text) > 3 and 
                            not any(skip in comment_text.lower() for skip in ['follow', 'like', 'share', 'view profile'])):
                            
                            comment = {
                                'comment_id': len(comments) + 1,
                                'nickname': clean_username,
                                'username': f'@{clean_username}',
                                'user_url': f'https://www.instagram.com{user_link.get("href", "")}',
                                'text': comment_text,
                                'time': 'N/A',
                                'likes': 0,
                                'profile_pic': '',
                                'followers': 'N/A',
                                'is_reply': False,
                                'replied_to': '',
                                'num_replies': 0
                            }
                            comments.append(comment)
                
                if len(comments) > 0:
                    print(f"Extracted {len(comments)} comments from HTML structure")
                    break
            
        except Exception as e:
            print(f"Error extracting from HTML: {str(e)}")
        
        return comments
    
    def _extract_with_direct_api(self, url):
        """Try direct API-like extraction using alternative ScrapFly config"""
        comments = []
        
        try:
            # Use a different approach with specific headers for API-like access
            from scrapfly import ScrapeConfig
            
            # Prepare headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            # Add authentication if available
            if self.is_logged_in:
                auth_headers = self.auth.get_authenticated_headers()
                headers.update(auth_headers)
                print("Using authenticated headers for direct API access")
            
            config = ScrapeConfig(
                url=url,
                headers=headers,
                asp=True,
                render_js=False,  # Try without JS first
                proxy_pool='public_residential_pool',
                country='US',
                session='instagram-authenticated-session' if self.is_logged_in else None
            )
            
            result = self.scrapfly.client.scrape(config)
            
            if result.success:
                html = result.content
                
                # Strategy 1: Look for proper Instagram GraphQL data
                comments.extend(self._extract_from_graphql_data(html))
                
                # Strategy 2: Look for comment structure in HTML
                if len(comments) == 0:
                    comments.extend(self._extract_from_comment_html(html))
                
                # Strategy 3: Look for any JSON with comment-like structure
                if len(comments) == 0:
                    comments.extend(self._extract_from_json_fallback(html))
                
                if len(comments) > 0:
                    print(f"Extracted {len(comments)} comments via direct API approach")
            
        except Exception as e:
            print(f"Error with direct API extraction: {str(e)}")
        
        return comments
    
    def _extract_from_graphql_data(self, html):
        """Extract from Instagram GraphQL API data"""
        comments = []
        
        try:
            # Look for GraphQL responses in the HTML
            graphql_patterns = [
                r'"edge_media_to_comment":\s*\{[^}]*"edges":\s*\[([^\]]+)\]',
                r'"comments":\s*\{[^}]*"edges":\s*\[([^\]]+)\]',
                r'"node":\s*\{[^}]*"text":\s*"([^"]+)"[^}]*"owner":\s*\{[^}]*"username":\s*"([^"]+)"'
            ]
            
            for pattern in graphql_patterns:
                matches = re.findall(pattern, html, re.DOTALL)
                if matches:
                    print(f"Found GraphQL data with pattern")
                    # Process GraphQL data
                    break
            
        except Exception as e:
            print(f"Error extracting GraphQL data: {str(e)}")
        
        return comments
    
    def _extract_from_comment_html(self, html):
        """Extract comments from HTML structure with better parsing"""
        comments = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for comment-like structures with username links
            selectors = [
                'a[href^="/"][href*="/"]',  # User links
                'article section',
                'section ul li',
                'div[role="button"]'
            ]
            
            found_usernames = set()
            potential_comments = []
            
            # First pass: find all user links
            user_links = soup.find_all('a', href=re.compile(r'^/[\w.]+/?$'))
            for link in user_links:
                username = link.get('href', '').strip('/')
                if username and len(username) > 2 and username not in ['explore', 'reels', 'stories']:
                    found_usernames.add(username)
            
            print(f"Found {len(found_usernames)} potential usernames: {list(found_usernames)[:5]}")
            
            # Second pass: find text that might be comments near these usernames
            for username in list(found_usernames)[:20]:  # Limit to first 20 users
                # Look for elements containing this username
                username_elements = soup.find_all(text=re.compile(username, re.IGNORECASE))
                
                for elem in username_elements[:5]:  # Limit per user
                    parent = elem.parent if elem.parent else elem
                    
                    # Get surrounding text
                    surrounding_text = parent.get_text(strip=True) if hasattr(parent, 'get_text') else str(elem)
                    
                    # Clean up the text to extract potential comment
                    raw_comment_text = surrounding_text.replace(username, '').strip()
                    
                    # Apply Unicode cleaning
                    comment_text = self._clean_extracted_text(raw_comment_text)
                    clean_username = self._normalize_username(username)
                    
                    # Validate if this looks like a comment
                    if (len(comment_text) > 10 and 
                        len(comment_text) < 500 and
                        not any(skip in comment_text.lower() for skip in ['follow', 'following', 'followers', 'posts', 'view profile'])):
                        
                        comment = {
                            'comment_id': len(comments) + 1,
                            'nickname': clean_username,
                            'username': f'@{clean_username}',
                            'user_url': f'https://www.instagram.com/{clean_username}/',
                            'text': comment_text,
                            'time': 'N/A',
                            'likes': 0,
                            'profile_pic': '',
                            'followers': 'N/A',
                            'is_reply': False,
                            'replied_to': '',
                            'num_replies': 0
                        }
                        comments.append(comment)
                        
                        if len(comments) >= 50:  # Reasonable limit
                            break
                
                if len(comments) >= 50:
                    break
            
            if len(comments) > 0:
                print(f"Extracted {len(comments)} comments from HTML structure")
            
        except Exception as e:
            print(f"Error extracting from HTML: {str(e)}")
        
        return comments
    
    def _extract_from_json_fallback(self, html):
        """Fallback JSON extraction with better username and likes parsing"""
        comments = []
        
        try:
            # Enhanced patterns to capture comment data including likes
            comment_patterns = [
                # Pattern for full comment objects with likes
                r'\{"text":"([^"]+)"[^}]*"username":"([^"]+)"[^}]*"like_count":(\d+)[^}]*\}',
                r'\{"username":"([^"]+)"[^}]*"text":"([^"]+)"[^}]*"like_count":(\d+)[^}]*\}',
                
                # Pattern for edge-like structures (Instagram GraphQL)
                r'"edge_liked_by":\s*\{\s*"count":\s*(\d+)\s*\}[^}]*"text":\s*"([^"]+)"[^}]*"username":\s*"([^"]+)"',
                r'"text":\s*"([^"]+)"[^}]*"edge_liked_by":\s*\{\s*"count":\s*(\d+)\s*\}[^}]*"username":\s*"([^"]+)"',
                
                # Simpler patterns for basic comment data
                r'\{"text":"([^"]+)"[^}]*"username":"([^"]+)"[^}]*\}',
                r'\{"username":"([^"]+)"[^}]*"text":"([^"]+)"[^}]*\}',
            ]
            
            extracted_comments = []
            
            for pattern in comment_patterns:
                matches = re.findall(pattern, html, re.DOTALL)
                for match in matches:
                    if len(match) >= 2:  # At least text and username
                        
                        # Parse based on pattern structure
                        if len(match) == 3 and match[2].isdigit():  # Has likes
                            if 'edge_liked_by' in pattern:
                                # GraphQL pattern: likes, text, username
                                likes, text, username = match
                            else:
                                # Standard pattern: text, username, likes
                                text, username, likes = match
                            likes = int(likes)
                        elif len(match) == 3 and match[0].isdigit():  # Different order with likes
                            # Pattern: username, text, likes
                            username, text, likes = match
                            likes = int(likes)
                        else:
                            # No likes data
                            text, username = match[0], match[1]
                            likes = 0
                        
                        if len(text) > 10 and len(text) < 500:
                            # Apply Unicode cleaning to extracted text and username
                            clean_text = self._clean_extracted_text(text)
                            clean_username = self._normalize_username(username)
                            
                            extracted_comments.append({
                                'text': clean_text,
                                'username': clean_username,
                                'likes': likes
                            })
                
                if extracted_comments:
                    break  # Use first successful pattern
            
            # Fixed approach: extract comment objects properly
            if not extracted_comments:
                self.logger.debug("Using proper Instagram comment node extraction")
                
                # Look for Instagram's comment node structure with proper text-username pairing
                comment_node_patterns = [
                    # Instagram GraphQL comment node structure
                    r'"node":\s*\{[^}]*?"text":\s*"([^"]+)"[^}]*?"owner":\s*\{[^}]*?"username":\s*"([^"]+)"[^}]*?\}[^}]*?(?:"edge_liked_by":\s*\{\s*"count":\s*(\d+)\s*\})?',
                    
                    # Alternative comment structure  
                    r'\{[^}]*?"text":\s*"([^"]+)"[^}]*?"owner":\s*\{[^}]*?"username":\s*"([^"]+)"[^}]*?\}[^}]*?(?:"like_count":\s*(\d+))?',
                    
                    # Basic comment object with text and username together
                    r'\{[^{}]*?"text":\s*"([^"]+)"[^{}]*?"username":\s*"([^"]+)"[^{}]*?(?:"like_count":\s*(\d+))?[^{}]*?\}'
                ]
                
                for pattern in comment_node_patterns:
                    matches = re.findall(pattern, html, re.DOTALL)
                    
                    if matches:
                        self.logger.debug(f"Found {len(matches)} comments with pattern")
                        
                        for match in matches:
                            if len(match) >= 2:  # At least text and username
                                text = match[0]
                                username = match[1]
                                likes = int(match[2]) if len(match) > 2 and match[2] and match[2].isdigit() else 0
                                
                                if (len(text) > 3 and len(text) < 500 and 
                                    not any(skip in text.lower() for skip in ['loading', 'follow', 'profile', 'instagram', 'see original'])):
                                    
                                    # Apply Unicode cleaning
                                    clean_text = self._clean_extracted_text(text)
                                    clean_username = self._normalize_username(username)
                                    
                                    extracted_comments.append({
                                        'text': clean_text,
                                        'username': clean_username,
                                        'likes': likes
                                    })
                                    
                                    self.logger.debug(f"Extracted: @{clean_username} - '{clean_text[:40]}...' ({likes} likes)")
                        
                        if extracted_comments:
                            break
                
                # Last resort: separate extraction but with better validation
                if not extracted_comments:
                    self.logger.debug("Using separate text/username extraction with validation")
                    
                    text_matches = re.findall(r'"text"\s*:\s*"([^"]{10,300})"', html)
                    
                    # For each text, try to find the associated username nearby
                    for text in text_matches[:20]:
                        if not any(skip in text.lower() for skip in ['loading', 'follow', 'profile', 'instagram']):
                            
                            # Find text position and look for username context
                            text_pos = html.find(f'"{text}"')
                            if text_pos > -1:
                                # Look in a reasonable context around the text
                                context_start = max(0, text_pos - 500)
                                context_end = min(len(html), text_pos + 500)
                                context = html[context_start:context_end]
                                
                                # Find username in this context
                                username_match = re.search(r'"username":\s*"([^"]+)"', context)
                                likes_match = re.search(r'"(?:like_count|count)":\s*(\d+)', context)
                                
                                if username_match:
                                    raw_username = username_match.group(1)
                                    likes = int(likes_match.group(1)) if likes_match else 0
                                    
                                    # Apply Unicode cleaning
                                    clean_text = self._clean_extracted_text(text)
                                    clean_username = self._normalize_username(raw_username)
                                    
                                    extracted_comments.append({
                                        'text': clean_text,
                                        'username': clean_username,
                                        'likes': likes
                                    })
                                    
                                    self.logger.debug(f"Context match: @{clean_username} - '{clean_text[:30]}...' ({likes} likes)")
                                    
                                    if len(extracted_comments) >= 20:
                                        break
            
            # Convert to final comment format
            for i, comment_data in enumerate(extracted_comments[:20]):
                comment = {
                    'comment_id': len(comments) + 1,
                    'nickname': comment_data['username'],
                    'username': f'@{comment_data["username"]}',
                    'user_url': f'https://www.instagram.com/{comment_data["username"]}/',
                    'text': comment_data['text'],
                    'time': 'N/A',
                    'likes': comment_data.get('likes', 0),
                    'profile_pic': '',
                    'followers': 'N/A',
                    'is_reply': False,
                    'replied_to': '',
                    'num_replies': 0
                }
                comments.append(comment)
            
            if len(comments) > 0:
                likes_found = sum(1 for c in comments if c['likes'] > 0)
                print(f"Extracted {len(comments)} comments from JSON fallback ({likes_found} with like data)")
            
        except Exception as e:
            print(f"Error in JSON fallback: {str(e)}")
        
        return comments
    
    def _remove_duplicate_comments(self, comments):
        """Remove duplicate comments based on text similarity"""
        if not comments:
            return []
        
        unique_comments = []
        seen_texts = set()
        
        for comment in comments:
            text = comment.get('text', '').strip().lower()
            if text and text not in seen_texts and len(text) > 3:
                seen_texts.add(text)
                unique_comments.append(comment)
        
        return unique_comments
    
    def _format_timestamp(self, timestamp):
        """Format timestamp to readable date"""
        if timestamp:
            try:
                if isinstance(timestamp, (int, float)):
                    return datetime.fromtimestamp(timestamp).strftime('%d-%m-%Y')
                else:
                    return str(timestamp)
            except:
                pass
        return 'N/A'
    
    def _enrich_with_followers(self, comments):
        """Enrich comments with follower data for real users"""
        if not comments:
            self.logger.debug("No comments to enrich with follower data")
            return comments
        
        self.logger.info(f"Starting follower enrichment for {len(comments)} comments")
        
        # Get unique users to avoid duplicate API calls
        unique_users = {}
        for comment in comments:
            username = comment.get('username', '').replace('@', '')
            if username and username not in unique_users and 'user_' not in username:
                unique_users[username] = []
            if username in unique_users:
                unique_users[username].append(comment)
        
        self.logger.info(f"Found {len(unique_users)} unique users for follower enrichment")
        self.logger.debug(f"Users to process: {list(unique_users.keys())[:10]}")  # Log first 10
        
        successful_enrichments = 0
        failed_enrichments = 0
        
        # Process each unique user
        for i, (username, user_comments) in enumerate(unique_users.items()):
            try:
                self.logger.debug(f"Processing user {i+1}/{len(unique_users)}: @{username}")
                
                followers = self._get_user_followers(username)
                
                if followers != 'N/A':
                    successful_enrichments += 1
                    self.logger.debug(f"Successfully got followers for @{username}: {followers}")
                else:
                    failed_enrichments += 1
                    self.logger.warning(f"Failed to get followers for @{username}")
                
                for comment in user_comments:
                    comment['followers'] = followers
                
                # Small delay to avoid rate limiting
                delay = random.uniform(1, 2)
                self.logger.debug(f"Rate limit delay: {delay:.1f}s")
                time.sleep(delay)
                
            except Exception as e:
                failed_enrichments += 1
                self.logger.error(f"Error getting followers for @{username}", {'error': str(e)})
                for comment in user_comments:
                    comment['followers'] = 'N/A'
        
        self.logger.info(f"Follower enrichment complete", {
            'total_users': len(unique_users),
            'successful': successful_enrichments,
            'failed': failed_enrichments,
            'success_rate': f"{(successful_enrichments/len(unique_users)*100):.1f}%" if unique_users else "0%"
        })
        
        return comments
    
    def _get_user_followers(self, username):
        """Get follower count for a specific user"""
        try:
            user_url = f"https://www.instagram.com/{username}/"
            self.logger.debug(f"Fetching follower data for @{username}")
            
            # Use simplified config for profile pages
            config_options = {
                'render_js': False,
                'retry': False,  # Disable retry to allow timeout
                'timeout': 30000  # 30 seconds minimum for ASP
            }
            
            # Use authentication if available
            if self.is_logged_in:
                auth_headers = self.auth.get_authenticated_headers()
                config_options['additional_headers'] = auth_headers
                config_options['session'] = 'instagram-authenticated-session'
                self.logger.debug(f"Using authenticated session for @{username}")
            else:
                self.logger.warning(f"No authentication available for @{username} - may get 429 error")
            
            config = self.scrapfly.create_scrape_config(user_url, 'instagram', config_options)
            
            self.logger.log_request(user_url, headers=config_options.get('additional_headers'))
            result = self.scrapfly.scrape_with_retry(config, max_retries=2)
            
            if result['success']:
                html = result['data']
                self.logger.log_response(user_url, 200, len(html))
                
                # Look for follower count patterns
                patterns = [
                    r'"edge_followed_by":\s*{\s*"count":\s*(\d+)',
                    r'"follower_count":(\d+)',
                    r'(\d+(?:,\d+)*)\s*followers',
                    r'(\d+(?:\.\d+)?[KMB]?)\s*followers'
                ]
                
                for i, pattern in enumerate(patterns):
                    match = re.search(pattern, html, re.IGNORECASE)
                    if match:
                        count_str = match.group(1).replace(',', '')
                        self.logger.debug(f"Found follower data for @{username} using pattern {i+1}: {count_str}")
                        
                        # Handle abbreviated numbers (K, M, B)
                        if 'K' in count_str.upper():
                            result_count = f"{float(count_str.replace('K', '').replace('k', '')) * 1000:.0f}"
                        elif 'M' in count_str.upper():
                            result_count = f"{float(count_str.replace('M', '').replace('m', '')) * 1000000:.0f}"
                        elif 'B' in count_str.upper():
                            result_count = f"{float(count_str.replace('B', '').replace('b', '')) * 1000000000:.0f}"
                        else:
                            result_count = self._format_number(int(float(count_str)))
                        
                        self.logger.debug(f"Parsed follower count for @{username}: {result_count}")
                        return result_count
                
                self.logger.warning(f"No follower pattern matched for @{username}")
                return 'N/A'
            else:
                error = result.get('error', 'Unknown error')
                self.logger.log_response(user_url, None, None, error)
                
                if '429' in str(error):
                    self.logger.log_rate_limit(user_url)
                    self.logger.warning(f"Rate limited while fetching @{username} - authentication may be needed")
                
                return 'N/A'
            
        except Exception as e:
            self.logger.error(f"Exception getting followers for @{username}", {'error': str(e)}, exc_info=True)
            return 'N/A'
        
        return 'N/A'
    
    def _format_number(self, number):
        """Format large numbers with K/M/B suffixes"""
        if number >= 1_000_000_000:
            return f"{number/1_000_000_000:.1f}B"
        elif number >= 1_000_000:
            return f"{number/1_000_000:.1f}M"
        elif number >= 1_000:
            return f"{number/1_000:.1f}K"
        else:
            return str(number)
    
    def get_post_id(self, url):
        """Extract post ID from URL"""
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