import requests
from typing import List, Dict, Optional, Any
from models import BrandContext, CompetitorAnalysis
from llm_service import LLMService
from insights_extractor import InsightsExtractor
import logging
import re
from urllib.parse import quote_plus
import asyncio
import time

logger = logging.getLogger(__name__)


class CompetitorAnalysisService:
    """Service for finding and analyzing competitor brands"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.insights_extractor = InsightsExtractor()
    
    def find_competitor_urls(self, search_terms: List[str], max_results: int = 5) -> List[str]:
        """
        Find potential competitor URLs using search terms.
        This is a simplified implementation - in production, you'd use proper search APIs.
        """
        competitor_urls = []
        
        # Common Shopify stores for different categories (pre-curated list)
        shopify_stores_by_category = {
            'beauty': [
                'https://colourpop.com',
                'https://jeffreestarcosmetics.com',
                'https://fentybeauty.com',
                'https://glossier.com'
            ],
            'fashion': [
                'https://fashionnova.com',
                'https://gymshark.com',
                'https://cupshe.com',
                'https://shein.com'
            ],
            'cosmetics': [
                'https://colourpop.com',
                'https://jeffreestarcosmetics.com',
                'https://rarebeauty.com'
            ],
            'clothing': [
                'https://fashionnova.com',
                'https://memy.co.in',
                'https://gymshark.com'
            ],
            'accessories': [
                'https://pandora.net',
                'https://danielwellington.com'
            ]
        }
        
        # Match search terms to categories and get potential competitors
        for term in search_terms:
            term_lower = term.lower()
            for category, urls in shopify_stores_by_category.items():
                if any(keyword in term_lower for keyword in [category, 'women', 'men', 'apparel', 'makeup']):
                    competitor_urls.extend(urls[:2])  # Add max 2 from each category
        
        # Remove duplicates and limit results
        unique_urls = list(set(competitor_urls))[:max_results]
        
        logger.info(f"Found {len(unique_urls)} potential competitor URLs")
        return unique_urls
    
    def analyze_competitors(self, primary_brand: BrandContext, max_competitors: int = 3) -> CompetitorAnalysis:
        """Analyze competitors for a given brand"""
        try:
            # Generate search terms using LLM
            search_terms = []
            if self.llm_service.enabled:
                brand_data = primary_brand.dict()
                search_terms = self.llm_service.generate_competitor_search_terms(brand_data)
            
            # If no LLM or no search terms, use fallback logic
            if not search_terms:
                search_terms = self._generate_fallback_search_terms(primary_brand)
            
            # Find potential competitor URLs
            competitor_urls = self.find_competitor_urls(search_terms, max_competitors * 2)
            
            # Filter out the primary brand URL
            competitor_urls = [url for url in competitor_urls if url != primary_brand.website_url]
            
            # Analyze each competitor
            competitors = []
            for url in competitor_urls[:max_competitors]:
                try:
                    logger.info(f"Analyzing competitor: {url}")
                    competitor_analysis = self.insights_extractor.extract_all_insights(url)
                    
                    # Calculate similarity if LLM is available
                    if self.llm_service.enabled:
                        similarity = self.llm_service.analyze_competitor_similarity(
                            primary_brand.dict(),
                            competitor_analysis.dict()
                        )
                        competitor_analysis.extraction_notes.append(f"Similarity score: {similarity:.2f}")
                    
                    competitors.append(competitor_analysis)
                    
                    # Add delay to avoid overwhelming servers
                    time.sleep(2)
                    
                except Exception as e:
                    logger.warning(f"Failed to analyze competitor {url}: {e}")
                    continue
            
            # Create analysis summary
            summary = self._create_analysis_summary(primary_brand, competitors, search_terms)
            
            return CompetitorAnalysis(
                primary_brand=primary_brand,
                competitors=competitors,
                analysis_summary=summary
            )
            
        except Exception as e:
            logger.error(f"Error in competitor analysis: {e}")
            return CompetitorAnalysis(
                primary_brand=primary_brand,
                competitors=[],
                analysis_summary=f"Competitor analysis failed: {str(e)}"
            )
    
    def _generate_fallback_search_terms(self, primary_brand: BrandContext) -> List[str]:
        """Generate search terms without LLM as fallback"""
        search_terms = []
        
        # Use product types
        if primary_brand.product_catalog:
            product_types = set()
            for product in primary_brand.product_catalog[:10]:  # Limit to first 10
                if product.product_type:
                    product_types.add(product.product_type.lower())
            search_terms.extend(list(product_types))
        
        # Use brand name keywords
        if primary_brand.brand_name:
            # Extract keywords from brand name
            name_words = re.findall(r'\b\w+\b', primary_brand.brand_name.lower())
            search_terms.extend(name_words[:3])  # Add first 3 words
        
        # Add generic terms based on common patterns
        generic_terms = ['fashion', 'beauty', 'cosmetics', 'clothing', 'accessories']
        search_terms.extend(generic_terms[:2])
        
        return search_terms[:8]  # Limit to 8 terms
    
    def _create_analysis_summary(self, primary_brand: BrandContext, competitors: List[BrandContext], search_terms: List[str]) -> str:
        """Create a summary of the competitor analysis"""
        summary_parts = [
            f"Competitor Analysis for {primary_brand.brand_name or primary_brand.website_url}",
            f"Search terms used: {', '.join(search_terms[:5])}",
            f"Found {len(competitors)} competitor(s)"
        ]
        
        if competitors:
            competitor_names = [comp.brand_name or comp.website_url for comp in competitors]
            summary_parts.append(f"Competitors analyzed: {', '.join(competitor_names)}")
            
            # Add product count comparison
            primary_product_count = primary_brand.total_products
            competitor_product_counts = [comp.total_products for comp in competitors]
            avg_competitor_products = sum(competitor_product_counts) / len(competitor_product_counts) if competitor_product_counts else 0
            
            summary_parts.append(f"Product catalog size - Primary: {primary_product_count}, Competitors avg: {avg_competitor_products:.0f}")
        
        return " | ".join(summary_parts)
    
    def get_market_insights(self, primary_brand: BrandContext, competitors: List[BrandContext]) -> Dict[str, Any]:
        """Generate market insights from competitor analysis"""
        insights = {
            "market_position": "unknown",
            "product_diversity": "unknown",
            "price_positioning": "unknown",
            "social_presence": "unknown"
        }
        
        if not competitors:
            return insights
        
        try:
            # Analyze product catalog size
            primary_products = primary_brand.total_products
            competitor_products = [comp.total_products for comp in competitors]
            avg_competitor_products = sum(competitor_products) / len(competitor_products)
            
            if primary_products > avg_competitor_products * 1.2:
                insights["market_position"] = "large_catalog"
            elif primary_products < avg_competitor_products * 0.8:
                insights["market_position"] = "focused_catalog"
            else:
                insights["market_position"] = "average_catalog"
            
            # Analyze social media presence
            primary_social_count = len(primary_brand.social_handles)
            competitor_social_counts = [len(comp.social_handles) for comp in competitors]
            avg_competitor_social = sum(competitor_social_counts) / len(competitor_social_counts)
            
            if primary_social_count > avg_competitor_social:
                insights["social_presence"] = "strong"
            elif primary_social_count < avg_competitor_social:
                insights["social_presence"] = "weak"
            else:
                insights["social_presence"] = "average"
            
            # Analyze product type diversity
            primary_types = set()
            for product in primary_brand.product_catalog:
                if product.product_type:
                    primary_types.add(product.product_type.lower())
            
            competitor_types = set()
            for competitor in competitors:
                for product in competitor.product_catalog:
                    if product.product_type:
                        competitor_types.add(product.product_type.lower())
            
            overlap = len(primary_types.intersection(competitor_types))
            unique_primary = len(primary_types - competitor_types)
            
            if unique_primary > overlap:
                insights["product_diversity"] = "unique_offerings"
            elif overlap > unique_primary:
                insights["product_diversity"] = "similar_to_market"
            else:
                insights["product_diversity"] = "balanced_portfolio"
                
        except Exception as e:
            logger.warning(f"Error generating market insights: {e}")
        
        return insights
