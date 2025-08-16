from pydantic import BaseModel, HttpUrl, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class Product(BaseModel):
    """Model for a single product"""
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    price: Optional[str] = None
    compare_at_price: Optional[str] = None
    vendor: Optional[str] = None
    product_type: Optional[str] = None
    handle: Optional[str] = None
    url: Optional[str] = None
    images: List[str] = []
    variants: List[Dict[str, Any]] = []
    tags: List[str] = []
    available: Optional[bool] = None


class FAQ(BaseModel):
    """Model for FAQ items"""
    question: str
    answer: str
    category: Optional[str] = None


class SocialHandle(BaseModel):
    """Model for social media handles"""
    platform: str
    url: str
    handle: Optional[str] = None


class ContactInfo(BaseModel):
    """Model for contact information"""
    emails: List[str] = []
    phone_numbers: List[str] = []
    address: Optional[str] = None


class Policy(BaseModel):
    """Model for various policies"""
    title: str
    content: str
    url: Optional[str] = None


class ImportantLink(BaseModel):
    """Model for important links"""
    title: str
    url: str
    description: Optional[str] = None


class BrandContext(BaseModel):
    """Main model for brand insights"""
    website_url: str
    brand_name: Optional[str] = None
    about_brand: Optional[str] = None
    
    # Product information
    product_catalog: List[Product] = []
    hero_products: List[Product] = []
    total_products: int = 0
    
    # Policies and legal
    privacy_policy: Optional[Policy] = None
    return_policy: Optional[Policy] = None
    refund_policy: Optional[Policy] = None
    terms_of_service: Optional[Policy] = None
    shipping_policy: Optional[Policy] = None
    
    # FAQ and support
    faqs: List[FAQ] = []
    
    # Social and contact
    social_handles: List[SocialHandle] = []
    contact_info: ContactInfo = ContactInfo()
    
    # Navigation and links
    important_links: List[ImportantLink] = []
    
    # Additional metadata
    currency: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    
    # Analysis metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now)
    extraction_success: bool = True
    extraction_notes: List[str] = []


class CompetitorAnalysis(BaseModel):
    """Model for competitor analysis (Bonus feature)"""
    primary_brand: BrandContext
    competitors: List[BrandContext] = []
    analysis_summary: Optional[str] = None


class APIResponse(BaseModel):
    """Standard API response model"""
    success: bool
    message: str
    data: Optional[BrandContext] = None
    error_code: Optional[str] = None


class WebsiteRequest(BaseModel):
    """Request model for the main API endpoint"""
    website_url: HttpUrl
