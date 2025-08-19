#!/usr/bin/env python3
"""
Improved Instagram Scraper that extracts real comments, usernames, and user data
Focuses on actual data extraction rather than placeholders
"""

import re
import json
import time
import random
from bs4 import BeautifulSoup
from datetime import datetime
from utils.scrapfly_config import ScrapFlyConfig

class ImprovedInstagramScraper:
    def __init__(self):
        self.scrapfly = ScrapFlyConfig()
        self.limits = self.scrapfly.get_platform_limits('instagram')
        
    def scrape_comments(self, url):
        """
        Extract real comments and user data from Instagram post/reel
        
        Args:
            url (str): Instagram post URL
            
        Returns:
            dict: Result with success/error and extracted data
        """
        try:
            print(f"Starting Instagram scraping: {url[:50]}...")
            
            # Step 1: Get page with embedded JavaScript data
            result = self._get_page_with_embedded_data(url)
            if not result['success']:
                return result
            
            # Step 2: Extract metadata
            metadata = self._extract_post_metadata(result['html'])
            
            # Step 3: Extract comments using multiple strategies
            comments = self._extract_real_comments(result['html'], url)
            
            print(f"Successfully extracted {len(comments)} real comments")
            
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
                'error': f"Instagram scraper error: {str(e)}",
                'data': None
            }
    
    def _get_page_with_embedded_data(self, url):
        """Get Instagram page with embedded JSON data"""
        try:
            # Enhanced configuration for better data extraction
            config = self.scrapfly.create_scrape_config(url, 'instagram', {
                'render_js': True,
                'wait_for_selector': 'article',
                'timeout': 30000,
                'js': self._get_improved_js_code()
            })
            
            result = self.scrapfly.scrape_with_retry(config)
            
            if result['success']:
                return {
                    'success': True,
                    'html': result['data']
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error')
                }
                
        except Exception as e:
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
                except:
                    continue
            
            # Extract from meta tags as fallback
            if not metadata:
                og_title = soup.find('meta', property='og:title')
                if og_title:
                    content = og_title.get('content', '')
                    username_match = re.search(r'@(\w+)', content)
                    if username_match:
                        metadata['publisher_username'] = '@' + username_match.group(1)
                
                og_description = soup.find('meta', property='og:description')
                if og_description:
                    metadata['description'] = og_description.get('content', '')
            
        except Exception as e:
            print(f"Error extracting metadata: {str(e)}")
        
        return metadata
    
    def _extract_real_comments(self, html, url):
        """Extract real comments from Instagram HTML"""
        comments = []
        
        try:
            # Strategy 1: Extract from embedded JSON data
            comments.extend(self._extract_from_embedded_json(html))
            
            # Strategy 2: Extract from HTML structure
            if len(comments) == 0:
                comments.extend(self._extract_from_html_structure(html))
            
            # Strategy 3: Use ScrapFly's direct API approach
            if len(comments) == 0:
                comments.extend(self._extract_with_direct_api(url))
            
            # Remove duplicates and limit results
            unique_comments = self._remove_duplicate_comments(comments)
            
            return unique_comments[:self.limits['max_comments_per_video']]
            
        except Exception as e:
            print(f"Error extracting comments: {str(e)}")
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
                                
                                comment = {
                                    'comment_id': i + 1,
                                    'nickname': owner.get('full_name', username),
                                    'username': f'@{username}',
                                    'user_url': f'https://www.instagram.com/{username}/',
                                    'text': node.get('text', ''),
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
                        
                        comment = {
                            'comment_id': i + 1,
                            'nickname': owner.get('full_name', username),
                            'username': f'@{username}',
                            'user_url': f'https://www.instagram.com/{username}/',
                            'text': node.get('text', ''),
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
                        comment_text = full_text.replace(username, '').strip()
                        
                        # Skip if it doesn't look like a real comment
                        if (len(comment_text) > 3 and 
                            not any(skip in comment_text.lower() for skip in ['follow', 'like', 'share', 'view profile'])):
                            
                            comment = {
                                'comment_id': len(comments) + 1,
                                'nickname': username,
                                'username': f'@{username}',
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
            
            config = ScrapeConfig(
                url=url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                asp=True,
                render_js=False,  # Try without JS first
                proxy_pool='public_residential_pool',
                country='US'
            )
            
            result = self.scrapfly.client.scrape(config)
            
            if result.success:
                html = result.content
                # Try to extract any embedded data
                json_matches = re.findall(r'({[^{}]*"text"[^{}]*})', html)
                
                for i, match in enumerate(json_matches[:20]):  # Limit to 20 matches
                    try:
                        data = json.loads(match)
                        if 'text' in data and len(data['text']) > 3:
                            comment = {
                                'comment_id': i + 1,
                                'nickname': data.get('owner', {}).get('username', f'user_{i+1}'),
                                'username': f'@{data.get("owner", {}).get("username", f"user_{i+1}")}',
                                'user_url': f'https://www.instagram.com/{data.get("owner", {}).get("username", f"user_{i+1}")|}/',
                                'text': data['text'],
                                'time': 'N/A',
                                'likes': data.get('edge_liked_by', {}).get('count', 0),
                                'profile_pic': '',
                                'followers': 'N/A',
                                'is_reply': False,
                                'replied_to': '',
                                'num_replies': 0
                            }
                            comments.append(comment)
                    except:
                        continue
                
                if len(comments) > 0:
                    print(f"Extracted {len(comments)} comments via direct API approach")
            
        except Exception as e:
            print(f"Error with direct API extraction: {str(e)}")
        
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