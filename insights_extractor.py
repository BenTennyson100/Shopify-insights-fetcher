from typing import Dict, List, Optional, Any
from models import BrandContext, Product, FAQ, SocialHandle, ContactInfo, Policy, ImportantLink
from scraper import ShopifyScraper
import logging
from urllib.parse import urljoin
import json

logger = logging.getLogger(__name__)


class InsightsExtractor:
    """Main class for extracting insights from Shopify stores"""
    
    def __init__(self):
        self.scraper = ShopifyScraper()
    
    def extract_all_insights(self, website_url: str) -> BrandContext:
        """Extract all insights from a Shopify store"""
        # Ensure URL has protocol
        if not website_url.startswith(('http://', 'https://')):
            website_url = 'https://' + website_url
        
        # Verify it's a Shopify store
        if not self.scraper.is_shopify_store(website_url):
            raise ValueError("The provided URL does not appear to be a Shopify store")
        
        # Initialize the brand context
        brand_context = BrandContext(website_url=website_url)
        
        # Get main page content
        html_content, soup = self.scraper.get_page_content(website_url)
        if not soup:
            raise Exception("Could not fetch website content")
        
        try:
            # Extract brand information
            brand_info = self.scraper.extract_brand_info(soup)
            brand_context.brand_name = brand_info.get('name')
            brand_context.about_brand = brand_info.get('description')
            
            # Extract product catalog
            products_data = self._extract_products(website_url)
            brand_context.product_catalog = products_data['products']
            brand_context.total_products = len(products_data['products'])
            
            # Extract hero products
            hero_product_handles = self.scraper.get_hero_products(soup, website_url)
            brand_context.hero_products = self._get_products_by_handles(
                products_data['products'], hero_product_handles
            )
            
            # Extract social handles
            social_links = self.scraper.extract_social_links(soup, website_url)
            brand_context.social_handles = [
                SocialHandle(**social) for social in social_links
            ]
            
            # Extract contact information
            contact_data = self.scraper.extract_contact_info(soup)
            brand_context.contact_info = ContactInfo(**contact_data)
            
            # Extract FAQs
            faqs_data = self.scraper.extract_faqs(soup)
            brand_context.faqs = [FAQ(**faq) for faq in faqs_data]
            
            # Extract policies
            policies_data = self.scraper.extract_policies(website_url)
            if policies_data.get('privacy_policy'):
                brand_context.privacy_policy = Policy(**policies_data['privacy_policy'])
            if policies_data.get('return_policy'):
                brand_context.return_policy = Policy(**policies_data['return_policy'])
            if policies_data.get('refund_policy'):
                brand_context.refund_policy = Policy(**policies_data['refund_policy'])
            if policies_data.get('terms_of_service'):
                brand_context.terms_of_service = Policy(**policies_data['terms_of_service'])
            if policies_data.get('shipping_policy'):
                brand_context.shipping_policy = Policy(**policies_data['shipping_policy'])
            
            # Extract important links
            links_data = self.scraper.extract_important_links(soup, website_url)
            brand_context.important_links = [
                ImportantLink(**link) for link in links_data
            ]
            
            # Extract additional metadata
            brand_context.currency = self._extract_currency(soup)
            brand_context.country = self._extract_country(soup)
            
            # Add extraction notes
            brand_context.extraction_notes.append(f"Successfully extracted data from {website_url}")
            brand_context.extraction_success = True
            
        except Exception as e:
            logger.error(f"Error extracting insights: {e}")
            brand_context.extraction_success = False
            brand_context.extraction_notes.append(f"Partial extraction due to error: {str(e)}")
        
        return brand_context
    
    def _extract_products(self, website_url: str) -> Dict[str, List[Product]]:
        """Extract product catalog from Shopify store"""
        products_data = {'products': []}
        
        # Get products from JSON endpoint
        json_products = self.scraper.get_products_json(website_url)
        
        if json_products and 'products' in json_products:
            for product_data in json_products['products']:
                try:
                    # Extract product images
                    images = []
                    if 'images' in product_data:
                        images = [img.get('src', '') for img in product_data['images']]
                    
                    # Extract product price (get first variant price)
                    price = None
                    compare_at_price = None
                    available = False
                    
                    if product_data.get('variants'):
                        first_variant = product_data['variants'][0]
                        price = first_variant.get('price', '')
                        compare_at_price = first_variant.get('compare_at_price', '')
                        available = first_variant.get('available', False)
                    
                    # Create product URL
                    product_url = urljoin(website_url, f"/products/{product_data.get('handle', '')}")
                    
                    product = Product(
                        id=str(product_data.get('id', '')),
                        title=product_data.get('title', ''),
                        description=self._clean_html(product_data.get('body_html', '')),
                        price=price,
                        compare_at_price=compare_at_price,
                        vendor=product_data.get('vendor', ''),
                        product_type=product_data.get('product_type', ''),
                        handle=product_data.get('handle', ''),
                        url=product_url,
                        images=images,
                        variants=product_data.get('variants', []),
                        tags=product_data.get('tags', []),
                        available=available
                    )
                    
                    products_data['products'].append(product)
                    
                except Exception as e:
                    logger.warning(f"Error processing product {product_data.get('id')}: {e}")
                    continue
        
        return products_data
    
    def _get_products_by_handles(self, products: List[Product], handles: List[str]) -> List[Product]:
        """Get products that match the given handles"""
        hero_products = []
        handles_set = set(handles)
        
        for product in products:
            if product.handle in handles_set:
                hero_products.append(product)
        
        return hero_products
    
    def _extract_currency(self, soup) -> Optional[str]:
        """Extract currency information from the page"""
        try:
            # Look for currency in various places
            currency_selectors = [
                'span[class*="currency"]',
                'span[class*="money"]',
                '[data-currency]'
            ]
            
            for selector in currency_selectors:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    # Common currency symbols
                    if '$' in text:
                        return 'USD'
                    elif '€' in text:
                        return 'EUR'
                    elif '£' in text:
                        return 'GBP'
                    elif '₹' in text:
                        return 'INR'
            
            # Look for data attributes
            currency_elem = soup.find(attrs={'data-currency': True})
            if currency_elem:
                return currency_elem.get('data-currency')
                
        except Exception as e:
            logger.debug(f"Could not extract currency: {e}")
        
        return None
    
    def _extract_country(self, soup) -> Optional[str]:
        """Extract country information from the page"""
        try:
            # Look for country selectors or shipping info
            country_indicators = soup.find_all(text=lambda text: text and any(
                country in text.lower() for country in ['shipping to', 'deliver to', 'country']
            ))
            
            if country_indicators:
                # This is a simplified approach - in reality, you might want more sophisticated parsing
                text = country_indicators[0].strip()
                # Common countries mentioned in shipping
                countries = ['united states', 'canada', 'united kingdom', 'australia', 'india']
                for country in countries:
                    if country in text.lower():
                        return country.title()
                        
        except Exception as e:
            logger.debug(f"Could not extract country: {e}")
        
        return None
    
    def _clean_html(self, html_content: str) -> str:
        """Clean HTML content and return plain text"""
        if not html_content:
            return ""
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and clean it up
            text = soup.get_text()
            # Break into lines and remove leading and trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text[:500]  # Limit length
        except Exception as e:
            logger.warning(f"Error cleaning HTML: {e}")
            return html_content[:500]
    
    def extract_additional_faqs(self, website_url: str) -> List[FAQ]:
        """Extract FAQs from dedicated FAQ pages"""
        additional_faqs = []
        
        # Common FAQ page URLs
        faq_urls = [
            '/pages/faq',
            '/pages/faqs',
            '/pages/frequently-asked-questions',
            '/faq',
            '/faqs',
            '/help'
        ]
        
        for faq_path in faq_urls:
            try:
                faq_url = urljoin(website_url, faq_path)
                _, soup = self.scraper.get_page_content(faq_url)
                
                if soup:
                    faqs = self.scraper.extract_faqs(soup)
                    for faq_data in faqs:
                        additional_faqs.append(FAQ(**faq_data))
                    
                    if faqs:  # If we found FAQs, no need to check other URLs
                        break
                        
            except Exception as e:
                logger.debug(f"Could not fetch FAQs from {faq_path}: {e}")
                continue
        
        return additional_faqs
