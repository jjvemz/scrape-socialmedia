#!/usr/bin/env python3
"""
Instagram Authentication Module for ScrapFly
Handles login and session management for Instagram scraping
"""

import os
import json
import time
import random
from scrapfly import ScrapeConfig

class InstagramAuth:
    def __init__(self, scrapfly_client):
        self.client = scrapfly_client
        self.session_id = None
        self.cookies = {}
        self.csrf_token = None
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        self.session_file = 'instagram_session.json'
        
    def load_session(self):
        """Load existing Instagram session if available"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    session_data = json.load(f)
                    self.cookies = session_data.get('cookies', {})
                    self.csrf_token = session_data.get('csrf_token')
                    self.session_id = session_data.get('session_id')
                    print("Loaded existing Instagram session")
                    return True
        except Exception as e:
            print(f"Error loading session: {str(e)}")
        return False
    
    def save_session(self):
        """Save Instagram session for reuse"""
        try:
            session_data = {
                'cookies': self.cookies,
                'csrf_token': self.csrf_token,
                'session_id': self.session_id,
                'timestamp': time.time()
            }
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f)
            print("Instagram session saved")
        except Exception as e:
            print(f"Error saving session: {str(e)}")
    
    def login(self, username, password):
        """
        Login to Instagram using ScrapFly
        
        Args:
            username (str): Instagram username
            password (str): Instagram password
            
        Returns:
            dict: Login result with success status
        """
        try:
            print(f"Attempting Instagram login for user: {username}")
            
            # Step 1: Get Instagram login page to obtain CSRF token
            login_result = self._get_login_page()
            if not login_result['success']:
                return login_result
            
            # Step 2: Extract CSRF token and cookies
            csrf_result = self._extract_csrf_token(login_result['html'])
            if not csrf_result['success']:
                return csrf_result
            
            # Step 3: Perform login
            auth_result = self._perform_login(username, password)
            if not auth_result['success']:
                return auth_result
            
            # Step 4: Verify login success
            verify_result = self._verify_login()
            if verify_result['success']:
                self.save_session()
                return {
                    'success': True,
                    'message': 'Instagram login successful'
                }
            else:
                return verify_result
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Login error: {str(e)}"
            }
    
    def _get_login_page(self):
        """Get Instagram login page"""
        try:
            config = ScrapeConfig(
                url='https://www.instagram.com/accounts/login/',
                headers={
                    'User-Agent': self.user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                },
                asp=True,
                render_js=True,
                wait_for_selector='input[name="username"]',
                proxy_pool='public_residential_pool',
                country='US',
                session='instagram-login-session'
            )
            
            result = self.client.scrape(config)
            
            if result.success:
                return {
                    'success': True,
                    'html': result.content,
                    'response': result
                }
            else:
                return {
                    'success': False,
                    'error': f"Failed to load login page: {result.error if hasattr(result, 'error') else 'Unknown error'}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Error getting login page: {str(e)}"
            }
    
    def _extract_csrf_token(self, html):
        """Extract CSRF token from login page"""
        try:
            import re
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Method 1: Look for CSRF token in meta tag
            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
            if csrf_meta:
                self.csrf_token = csrf_meta.get('content')
                print(f"Found CSRF token via meta tag")
                return {'success': True}
            
            # Method 2: Look for CSRF token in script tags
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    csrf_match = re.search(r'"csrf_token":\s*"([^"]+)"', script.string)
                    if csrf_match:
                        self.csrf_token = csrf_match.group(1)
                        print(f"Found CSRF token via script")
                        return {'success': True}
            
            # Method 3: Look for rollout_hash as alternative
            for script in scripts:
                if script.string:
                    rollout_match = re.search(r'"rollout_hash":\s*"([^"]+)"', script.string)
                    if rollout_match:
                        self.csrf_token = rollout_match.group(1)
                        print(f"Found rollout hash as CSRF alternative")
                        return {'success': True}
            
            return {
                'success': False,
                'error': 'Could not extract CSRF token from login page'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error extracting CSRF token: {str(e)}"
            }
    
    def _perform_login(self, username, password):
        """Perform actual login request"""
        try:
            # Updated login data format for 2025
            login_data = {
                'username': username,
                'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{password}',
                'queryParams': '{}',
                'optIntoOneTap': 'false',
                'trustedDeviceRecords': '{}',
                'stopDeletionNonce': '',
                'queryParams': '{}'
            }
            
            # Add CSRF token if available
            if self.csrf_token:
                login_data['csrf_token'] = self.csrf_token
            
            # Prepare headers
            headers = {
                'User-Agent': self.user_agent,
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest',
                'X-IG-App-ID': '936619743392459',
                'X-Instagram-AJAX': '1',
                'X-ASBD-ID': '129477',
                'X-Web-Device-Id': f'web-{random.randint(10000000, 99999999)}',
                'Origin': 'https://www.instagram.com',
                'Referer': 'https://www.instagram.com/accounts/login/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"'
            }
            
            if self.csrf_token:
                headers['X-CSRFToken'] = self.csrf_token
            
            # Create login request config with better settings
            config = ScrapeConfig(
                url='https://www.instagram.com/accounts/login/ajax/',
                method='POST',
                headers=headers,
                body=login_data,
                asp=True,
                proxy_pool='public_residential_pool',
                country='US',
                session='instagram-login-session',
                timeout=30000,  # 30 second timeout (minimum for ASP)
                retry=False  # No retry for login
            )
            
            result = self.client.scrape(config)
            
            if result.success:
                try:
                    response_data = json.loads(result.content)
                    print(f"Login response: {response_data}")
                    
                    if response_data.get('authenticated'):
                        print("Login successful!")
                        
                        # Extract session cookies
                        if hasattr(result, 'response') and hasattr(result.response, 'cookies'):
                            for cookie in result.response.cookies:
                                self.cookies[cookie.name] = cookie.value
                                if cookie.name == 'sessionid':
                                    self.session_id = cookie.value
                        
                        return {'success': True}
                    elif response_data.get('status') == 'ok':
                        # Alternative success check
                        print("Login appears successful (status: ok)")
                        return {'success': True}
                    else:
                        error_msg = response_data.get('message', 'Authentication failed')
                        return {
                            'success': False,
                            'error': f"Login failed: {error_msg}"
                        }
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'error': 'Invalid response format from Instagram'
                    }
            else:
                return {
                    'success': False,
                    'error': f"Login request failed: {result.error if hasattr(result, 'error') else 'Unknown error'}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Error performing login: {str(e)}"
            }
    
    def _verify_login(self):
        """Verify that login was successful"""
        try:
            # Try to access a page that requires authentication
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            
            # Add session cookies
            cookie_header = '; '.join([f'{name}={value}' for name, value in self.cookies.items()])
            if cookie_header:
                headers['Cookie'] = cookie_header
            
            config = ScrapeConfig(
                url='https://www.instagram.com/',
                headers=headers,
                asp=True,
                proxy_pool='public_residential_pool',
                country='US',
                session='instagram-login-session'
            )
            
            result = self.client.scrape(config)
            
            if result.success:
                # Check if we're logged in (not redirected to login)
                if 'accounts/login' not in result.content and 'logged_in' in result.content.lower():
                    return {'success': True}
                else:
                    return {
                        'success': False,
                        'error': 'Login verification failed - still being redirected to login page'
                    }
            else:
                return {
                    'success': False,
                    'error': 'Could not verify login status'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Error verifying login: {str(e)}"
            }
    
    def get_authenticated_headers(self):
        """Get headers for authenticated requests"""
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Cache-Control': 'max-age=0',
        }
        
        # Add authentication cookies
        if self.cookies:
            cookie_header = '; '.join([f'{name}={value}' for name, value in self.cookies.items()])
            headers['Cookie'] = cookie_header
        
        if self.csrf_token:
            headers['X-CSRFToken'] = self.csrf_token
        
        return headers
    
    def is_authenticated(self):
        """Check if we have a valid session"""
        return bool(self.session_id or self.cookies.get('sessionid'))
    
    def logout(self):
        """Clear session data"""
        self.cookies = {}
        self.csrf_token = None
        self.session_id = None
        
        # Remove session file
        try:
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
        except:
            pass
        
        print("Instagram session cleared")