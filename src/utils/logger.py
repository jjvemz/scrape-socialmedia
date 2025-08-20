#!/usr/bin/env python3
"""
Comprehensive logging system for Instagram scraper debugging
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

class ScraperLogger:
    def __init__(self, name="instagram_scraper", log_level=logging.DEBUG):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        
        # Clear existing handlers to avoid duplicates
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Create logs directory
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup file and console handlers
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Setup file and console logging handlers"""
        
        # File handler for detailed logs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"scraper_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler for important messages
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Detailed formatter for file
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Simple formatter for console
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"Logging initialized - Log file: {log_file}")
    
    def debug(self, message, extra_data=None):
        """Log debug message with optional extra data"""
        if extra_data:
            message = f"{message} | Data: {extra_data}"
        self.logger.debug(message)
    
    def info(self, message, extra_data=None):
        """Log info message with optional extra data"""
        if extra_data:
            message = f"{message} | Data: {extra_data}"
        self.logger.info(message)
    
    def warning(self, message, extra_data=None):
        """Log warning message with optional extra data"""
        if extra_data:
            message = f"{message} | Data: {extra_data}"
        self.logger.warning(message)
    
    def error(self, message, extra_data=None, exc_info=False):
        """Log error message with optional extra data and exception info"""
        if extra_data:
            message = f"{message} | Data: {extra_data}"
        self.logger.error(message, exc_info=exc_info)
    
    def critical(self, message, extra_data=None, exc_info=False):
        """Log critical message with optional extra data and exception info"""
        if extra_data:
            message = f"{message} | Data: {extra_data}"
        self.logger.critical(message, exc_info=exc_info)
    
    def log_request(self, url, method="GET", headers=None, status_code=None):
        """Log HTTP request details"""
        self.debug(f"HTTP {method} Request", {
            'url': url,
            'headers_count': len(headers) if headers else 0,
            'status_code': status_code
        })
    
    def log_response(self, url, status_code, content_length=None, error=None):
        """Log HTTP response details"""
        response_data = {
            'url': url,
            'status_code': status_code,
            'content_length': content_length
        }
        
        if error:
            response_data['error'] = str(error)
            self.error(f"HTTP Response Error", response_data)
        else:
            self.debug(f"HTTP Response Success", response_data)
    
    def log_extraction_attempt(self, strategy, url, found_count=0):
        """Log extraction strategy attempt"""
        self.info(f"Extraction Strategy: {strategy}", {
            'url': url[:50] + '...' if len(url) > 50 else url,
            'found_count': found_count
        })
    
    def log_auth_attempt(self, username, success=False, error=None):
        """Log authentication attempt"""
        auth_data = {
            'username': username,
            'success': success
        }
        
        if error:
            auth_data['error'] = str(error)
            self.error("Authentication Failed", auth_data)
        else:
            if success:
                self.info("Authentication Successful", auth_data)
            else:
                self.warning("Authentication Failed", auth_data)
    
    def log_comment_data(self, comment_id, username, text_length, likes, has_followers):
        """Log individual comment data for debugging"""
        self.debug(f"Comment Extracted", {
            'comment_id': comment_id,
            'username': username,
            'text_length': text_length,
            'likes': likes,
            'has_followers': has_followers
        })
    
    def log_scraping_summary(self, url, total_comments, real_usernames, comments_with_likes, comments_with_followers):
        """Log overall scraping summary"""
        summary_data = {
            'url': url[:50] + '...' if len(url) > 50 else url,
            'total_comments': total_comments,
            'real_usernames': real_usernames,
            'comments_with_likes': comments_with_likes,
            'comments_with_followers': comments_with_followers
        }
        
        self.info("Scraping Summary", summary_data)
    
    def log_rate_limit(self, url, retry_after=None):
        """Log rate limiting encounters"""
        rate_limit_data = {
            'url': url,
            'retry_after': retry_after,
            'timestamp': datetime.now().isoformat()
        }
        
        self.warning("Rate Limit Encountered (429)", rate_limit_data)
    
    def log_config_issue(self, issue_type, details):
        """Log configuration issues"""
        self.error(f"Configuration Issue: {issue_type}", details)

# Global logger instance
scraper_logger = ScraperLogger()

def get_logger():
    """Get the global scraper logger instance"""
    return scraper_logger