import requests
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
from typing import Dict, List, Optional, Any, Tuple
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import logging

logger = logging.getLogger(__name__)


class ShopifyScraper:
    """Main scraper class for Shopify websites"""
    
    def __init__(self, timeout: int = 10):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.timeout = timeout
    
    def get_page_content(self, url: str) -> Tuple[Optional[str], Optional[BeautifulSoup]]:
        """Fetch page content and return both raw HTML and BeautifulSoup object"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return response.text, soup
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None, None
    
    def get_products_json(self, base_url: str) -> Optional[Dict[str, Any]]:
        """Fetch products from the /products.json endpoint"""
        try:
            products_url = urljoin(base_url, '/products.json')
            response = self.session.get(products_url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, json.JSONDecodeError) as e:
            logger.error(f"Error fetching products.json from {base_url}: {e}")
            return None
    
    def get_collections_json(self, base_url: str) -> Optional[Dict[str, Any]]:
        """Fetch collections from the /collections.json endpoint"""
        try:
            collections_url = urljoin(base_url, '/collections.json')
            response = self.session.get(collections_url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, json.JSONDecodeError) as e:
            logger.error(f"Error fetching collections.json from {base_url}: {e}")
            return None
    
    def is_shopify_store(self, url: str) -> bool:
        """Check if a given URL is a Shopify store"""
        try:
            # Try to access the /products.json endpoint
            products_data = self.get_products_json(url)
            if products_data and 'products' in products_data:
                return True
            
            # Check for Shopify-specific meta tags or scripts
            _, soup = self.get_page_content(url)
            if soup:
                # Look for Shopify-specific indicators
                shopify_indicators = [
                    soup.find('meta', {'name': 'generator', 'content': re.compile(r'Shopify', re.I)}),
                    soup.find('script', src=re.compile(r'shopify', re.I)),
                    soup.find(text=re.compile(r'shopify', re.I)),
                    soup.find('link', href=re.compile(r'shopify', re.I))
                ]
                
                return any(indicator for indicator in shopify_indicators)
            
            return False
        except Exception as e:
            logger.error(f"Error checking if {url} is Shopify store: {e}")
            return False
    
    def extract_social_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract social media links from the page"""
        social_links = []
        social_patterns = {
            'instagram': r'instagram\.com/([^/\s?]+)',
            'facebook': r'facebook\.com/([^/\s?]+)',
            'twitter': r'twitter\.com/([^/\s?]+)',
            'tiktok': r'tiktok\.com/@?([^/\s?]+)',
            'youtube': r'youtube\.com/(?:c/|channel/|user/)?([^/\s?]+)',
            'linkedin': r'linkedin\.com/(?:company/|in/)?([^/\s?]+)',
            'pinterest': r'pinterest\.com/([^/\s?]+)'
        }
        
        # Find all links
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '').lower()
            if not href:
                continue
            
            # Make relative URLs absolute
            if href.startswith('/'):
                href = urljoin(base_url, href)
            
            for platform, pattern in social_patterns.items():
                match = re.search(pattern, href)
                if match:
                    social_links.append({
                        'platform': platform,
                        'url': href,
                        'handle': match.group(1)
                    })
        
        return social_links
    
    def extract_contact_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract contact information from the page"""
        contact_info = {
            'emails': [],
            'phone_numbers': [],
            'address': None
        }
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        text = soup.get_text()
        emails = re.findall(email_pattern, text)
        contact_info['emails'] = list(set(emails))
        
        # Extract phone numbers (basic patterns)
        phone_patterns = [
            r'\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
            r'\+?([0-9]{1,3})[-.\s]?([0-9]{3,4})[-.\s]?([0-9]{3,4})[-.\s]?([0-9]{3,4})',
        ]
        
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            for phone in phones:
                phone_str = ''.join(phone)
                if len(phone_str) >= 7:  # Minimum phone number length
                    contact_info['phone_numbers'].append(''.join(phone))
        
        contact_info['phone_numbers'] = list(set(contact_info['phone_numbers']))
        
        return contact_info
    
    def extract_faqs(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract FAQ items from the page"""
        faqs = []
        
        # Common FAQ patterns
        faq_selectors = [
            'div[class*="faq"]',
            'section[class*="faq"]',
            'div[class*="question"]',
            'details',
            'div[class*="accordion"]'
        ]
        
        for selector in faq_selectors:
            elements = soup.select(selector)
            for element in elements:
                # Look for question-answer pairs
                question_elem = element.find(['h3', 'h4', 'h5', 'summary', 'dt', '[class*="question"]'])
                answer_elem = element.find(['p', 'div', 'dd', '[class*="answer"]'])
                
                if question_elem and answer_elem:
                    question = question_elem.get_text(strip=True)
                    answer = answer_elem.get_text(strip=True)
                    
                    if question and answer and len(question) > 5 and len(answer) > 10:
                        faqs.append({
                            'question': question,
                            'answer': answer
                        })
        
        return faqs
    
    def extract_policies(self, base_url: str) -> Dict[str, Optional[Dict[str, str]]]:
        """Extract various policies from the website"""
        policies = {
            'privacy_policy': None,
            'return_policy': None,
            'refund_policy': None,
            'terms_of_service': None,
            'shipping_policy': None
        }
        
        policy_urls = {
            'privacy_policy': ['/pages/privacy-policy', '/privacy-policy', '/pages/privacy'],
            'return_policy': ['/pages/returns', '/pages/return-policy', '/returns'],
            'refund_policy': ['/pages/refunds', '/pages/refund-policy', '/refunds'],
            'terms_of_service': ['/pages/terms-of-service', '/terms', '/pages/terms'],
            'shipping_policy': ['/pages/shipping-policy', '/pages/shipping', '/shipping']
        }
        
        for policy_name, possible_urls in policy_urls.items():
            for url_path in possible_urls:
                try:
                    full_url = urljoin(base_url, url_path)
                    _, soup = self.get_page_content(full_url)
                    
                    if soup:
                        # Extract policy content
                        content_elem = soup.find(['main', 'article', 'div[class*="content"]', 'div[class*="policy"]'])
                        if content_elem:
                            content = content_elem.get_text(strip=True)
                            if len(content) > 100:  # Ensure it's substantial content
                                policies[policy_name] = {
                                    'title': policy_name.replace('_', ' ').title(),
                                    'content': content[:2000],  # Truncate for storage
                                    'url': full_url
                                }
                                break
                except Exception as e:
                    logger.debug(f"Could not fetch {policy_name} from {url_path}: {e}")
                    continue
        
        return policies
    
    def extract_important_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract important navigation links"""
        important_links = []
        important_keywords = [
            'contact', 'about', 'track', 'tracking', 'support', 'help',
            'blog', 'news', 'size guide', 'shipping', 'returns'
        ]
        
        # Look for navigation links
        nav_areas = soup.find_all(['nav', 'footer', 'header', 'div[class*="menu"]'])
        
        for nav in nav_areas:
            links = nav.find_all('a', href=True)
            for link in links:
                text = link.get_text(strip=True).lower()
                href = link.get('href')
                
                if any(keyword in text for keyword in important_keywords):
                    # Make relative URLs absolute
                    if href.startswith('/'):
                        href = urljoin(base_url, href)
                    
                    important_links.append({
                        'title': link.get_text(strip=True),
                        'url': href,
                        'description': text
                    })
        
        return important_links
    
    def get_hero_products(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract hero products from the homepage"""
        hero_product_handles = []
        
        # Look for product links on the main page
        product_links = soup.find_all('a', href=re.compile(r'/products/'))
        
        for link in product_links:
            href = link.get('href')
            if href:
                # Extract product handle from URL
                match = re.search(r'/products/([^/?]+)', href)
                if match:
                    hero_product_handles.append(match.group(1))
        
        # Remove duplicates and limit to first 10
        return list(set(hero_product_handles))[:10]
    
    def extract_brand_info(self, soup: BeautifulSoup) -> Dict[str, Optional[str]]:
        """Extract brand information from the page"""
        brand_info = {
            'name': None,
            'description': None
        }
        
        # Try to get brand name from title, h1, or meta tags
        title_tag = soup.find('title')
        if title_tag:
            brand_info['name'] = title_tag.get_text(strip=True).split('|')[0].strip()
        
        # Look for about sections
        about_selectors = [
            'div[class*="about"]',
            'section[class*="about"]',
            'div[class*="story"]',
            'section[class*="story"]'
        ]
        
        for selector in about_selectors:
            about_elem = soup.select_one(selector)
            if about_elem:
                text = about_elem.get_text(strip=True)
                if len(text) > 50:
                    brand_info['description'] = text[:500]  # Limit length
                    break
        
        return brand_info
