import openai
import json
from typing import Dict, List, Optional, Any
from models import FAQ, SocialHandle, ContactInfo
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class LLMService:
    """Service for using LLM to structure unorganized data"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if self.api_key:
            openai.api_key = self.api_key
        self.enabled = bool(self.api_key)
        
        if not self.enabled:
            logger.warning("OpenAI API key not found. LLM features will be disabled.")
    
    def structure_faqs(self, raw_text: str) -> List[FAQ]:
        """Use LLM to extract and structure FAQ data from raw text"""
        if not self.enabled:
            return []
        
        try:
            prompt = f"""
            Extract FAQ (Frequently Asked Questions) data from the following text. 
            Return ONLY a valid JSON array of objects with 'question' and 'answer' fields.
            Each question should be a clear, standalone question, and each answer should be complete.
            Filter out incomplete or unclear Q&A pairs.
            
            Text: {raw_text[:3000]}
            
            Format:
            [
                {{
                    "question": "Do you offer international shipping?",
                    "answer": "Yes, we ship worldwide with standard delivery times of 7-14 business days."
                }}
            ]
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured FAQ data from text. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                faq_data = json.loads(content)
                if isinstance(faq_data, list):
                    return [FAQ(**faq) for faq in faq_data if 'question' in faq and 'answer' in faq]
            except json.JSONDecodeError:
                logger.warning("Could not parse LLM response as JSON")
                
        except Exception as e:
            logger.error(f"Error using LLM for FAQ extraction: {e}")
        
        return []
    
    def extract_contact_info(self, raw_text: str) -> Optional[ContactInfo]:
        """Use LLM to extract contact information from raw text"""
        if not self.enabled:
            return None
        
        try:
            prompt = f"""
            Extract contact information from the following text.
            Return ONLY a valid JSON object with 'emails', 'phone_numbers', and 'address' fields.
            
            Text: {raw_text[:2000]}
            
            Format:
            {{
                "emails": ["contact@example.com", "support@example.com"],
                "phone_numbers": ["+1-555-0123", "1-800-555-0456"],
                "address": "123 Main St, New York, NY 10001"
            }}
            
            If no information is found for a field, use an empty array or null.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts contact information from text. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            
            try:
                contact_data = json.loads(content)
                return ContactInfo(**contact_data)
            except json.JSONDecodeError:
                logger.warning("Could not parse LLM contact info response as JSON")
                
        except Exception as e:
            logger.error(f"Error using LLM for contact info extraction: {e}")
        
        return None
    
    def enhance_brand_description(self, raw_about_text: str, brand_name: str = None) -> Optional[str]:
        """Use LLM to create a clean, structured brand description"""
        if not self.enabled or not raw_about_text:
            return raw_about_text
        
        try:
            brand_context = f" for {brand_name}" if brand_name else ""
            
            prompt = f"""
            Clean and summarize the following brand description{brand_context}.
            Make it concise, professional, and informative. Remove any HTML tags, excessive formatting, or redundant information.
            Keep it under 200 words and focus on what makes the brand unique.
            
            Raw text: {raw_about_text[:1000]}
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates clean, professional brand descriptions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error enhancing brand description: {e}")
        
        return raw_about_text
    
    def extract_social_handles(self, raw_text: str) -> List[SocialHandle]:
        """Use LLM to extract social media handles from raw text"""
        if not self.enabled:
            return []
        
        try:
            prompt = f"""
            Extract social media handles and URLs from the following text.
            Return ONLY a valid JSON array of objects with 'platform', 'url', and 'handle' fields.
            Common platforms: instagram, facebook, twitter, tiktok, youtube, linkedin, pinterest
            
            Text: {raw_text[:2000]}
            
            Format:
            [
                {{
                    "platform": "instagram",
                    "url": "https://instagram.com/brandname",
                    "handle": "brandname"
                }}
            ]
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts social media information from text. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            
            try:
                social_data = json.loads(content)
                if isinstance(social_data, list):
                    return [SocialHandle(**social) for social in social_data if 'platform' in social and 'url' in social]
            except json.JSONDecodeError:
                logger.warning("Could not parse LLM social handles response as JSON")
                
        except Exception as e:
            logger.error(f"Error using LLM for social handles extraction: {e}")
        
        return []
    
    def analyze_competitor_similarity(self, brand1_data: Dict[str, Any], brand2_data: Dict[str, Any]) -> float:
        """Use LLM to analyze similarity between two brands"""
        if not self.enabled:
            return 0.0
        
        try:
            # Simplified similarity analysis based on product types and descriptions
            brand1_summary = {
                'name': brand1_data.get('brand_name', ''),
                'products': [p.get('product_type', '') for p in brand1_data.get('product_catalog', [])[:10]],
                'description': brand1_data.get('about_brand', '')[:200]
            }
            
            brand2_summary = {
                'name': brand2_data.get('brand_name', ''),
                'products': [p.get('product_type', '') for p in brand2_data.get('product_catalog', [])[:10]],
                'description': brand2_data.get('about_brand', '')[:200]
            }
            
            prompt = f"""
            Analyze the similarity between these two brands on a scale of 0.0 to 1.0.
            Consider product types, brand descriptions, and target markets.
            Return ONLY a single decimal number between 0.0 and 1.0.
            
            Brand 1: {json.dumps(brand1_summary)}
            Brand 2: {json.dumps(brand2_summary)}
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes brand similarity. Return only a decimal number."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            return float(content)
            
        except Exception as e:
            logger.error(f"Error analyzing competitor similarity: {e}")
        
        return 0.0
    
    def generate_competitor_search_terms(self, brand_data: Dict[str, Any]) -> List[str]:
        """Generate search terms to find competitor brands"""
        if not self.enabled:
            return []
        
        try:
            brand_summary = {
                'name': brand_data.get('brand_name', ''),
                'products': [p.get('product_type', '') for p in brand_data.get('product_catalog', [])[:5]],
                'description': brand_data.get('about_brand', '')[:200]
            }
            
            prompt = f"""
            Based on this brand data, generate 5-8 search terms to find similar competitor brands.
            Focus on product categories, style, and target market.
            Return ONLY a JSON array of search terms.
            
            Brand: {json.dumps(brand_summary)}
            
            Format: ["women's fashion", "sustainable clothing", "affordable jewelry"]
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates search terms. Return only valid JSON array."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            
            try:
                search_terms = json.loads(content)
                if isinstance(search_terms, list):
                    return search_terms
            except json.JSONDecodeError:
                logger.warning("Could not parse LLM search terms response as JSON")
                
        except Exception as e:
            logger.error(f"Error generating competitor search terms: {e}")
        
        return []
