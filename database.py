from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, JSON, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.mysql import LONGTEXT
from datetime import datetime
from typing import Optional, List
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+pymysql://user:password@localhost/shopify_insights')

Base = declarative_base()


class BrandAnalysis(Base):
    """Main table for storing brand analysis data"""
    __tablename__ = "brand_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    website_url = Column(String(500), unique=True, index=True, nullable=False)
    brand_name = Column(String(255))
    about_brand = Column(Text)
    currency = Column(String(10))
    country = Column(String(100))
    total_products = Column(Integer, default=0)
    extraction_success = Column(Boolean, default=True)
    extraction_notes = Column(JSON)
    analysis_timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    products = relationship("Product", back_populates="brand", cascade="all, delete-orphan")
    hero_products = relationship("HeroProduct", back_populates="brand", cascade="all, delete-orphan")
    social_handles = relationship("SocialHandle", back_populates="brand", cascade="all, delete-orphan")
    faqs = relationship("FAQ", back_populates="brand", cascade="all, delete-orphan")
    policies = relationship("Policy", back_populates="brand", cascade="all, delete-orphan")
    important_links = relationship("ImportantLink", back_populates="brand", cascade="all, delete-orphan")
    contact_info = relationship("ContactInfo", back_populates="brand", uselist=False, cascade="all, delete-orphan")


class Product(Base):
    """Table for storing product information"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    shopify_id = Column(String(100))
    brand_id = Column(Integer, ForeignKey("brand_analyses.id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    price = Column(String(50))
    compare_at_price = Column(String(50))
    vendor = Column(String(255))
    product_type = Column(String(255))
    handle = Column(String(255))
    url = Column(String(500))
    images = Column(JSON)
    variants = Column(JSON)
    tags = Column(JSON)
    available = Column(Boolean)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    brand = relationship("BrandAnalysis", back_populates="products")


class HeroProduct(Base):
    """Table for storing hero products (products featured on homepage)"""
    __tablename__ = "hero_products"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brand_analyses.id"), nullable=False)
    product_handle = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    brand = relationship("BrandAnalysis", back_populates="hero_products")


class SocialHandle(Base):
    """Table for storing social media handles"""
    __tablename__ = "social_handles"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brand_analyses.id"), nullable=False)
    platform = Column(String(50), nullable=False)
    url = Column(String(500), nullable=False)
    handle = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    brand = relationship("BrandAnalysis", back_populates="social_handles")


class FAQ(Base):
    """Table for storing FAQ information"""
    __tablename__ = "faqs"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brand_analyses.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    brand = relationship("BrandAnalysis", back_populates="faqs")


class Policy(Base):
    """Table for storing policy information"""
    __tablename__ = "policies"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brand_analyses.id"), nullable=False)
    policy_type = Column(String(100), nullable=False)  # privacy_policy, return_policy, etc.
    title = Column(String(500), nullable=False)
    content = Column(LONGTEXT)
    url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    brand = relationship("BrandAnalysis", back_populates="policies")


class ImportantLink(Base):
    """Table for storing important navigation links"""
    __tablename__ = "important_links"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brand_analyses.id"), nullable=False)
    title = Column(String(500), nullable=False)
    url = Column(String(500), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    brand = relationship("BrandAnalysis", back_populates="important_links")


class ContactInfo(Base):
    """Table for storing contact information"""
    __tablename__ = "contact_info"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brand_analyses.id"), nullable=False)
    emails = Column(JSON)
    phone_numbers = Column(JSON)
    address = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    brand = relationship("BrandAnalysis", back_populates="contact_info")


class DatabaseManager:
    """Database manager class for handling database operations"""
    
    def __init__(self, database_url: str = DATABASE_URL):
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        self._initialize()
    
    def _initialize(self):
        """Initialize database connection"""
        try:
            self.engine = create_engine(self.database_url, echo=False)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.info("Database connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            self.engine = None
            self.SessionLocal = None
    
    def create_tables(self):
        """Create all tables in the database"""
        if self.engine:
            try:
                Base.metadata.create_all(bind=self.engine)
                logger.info("Database tables created successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to create tables: {e}")
                return False
        return False
    
    def get_session(self) -> Optional[Session]:
        """Get a database session"""
        if self.SessionLocal:
            return self.SessionLocal()
        return None
    
    def save_brand_analysis(self, brand_context) -> Optional[int]:
        """Save brand analysis to database"""
        if not self.SessionLocal:
            logger.warning("Database not available, skipping save")
            return None
        
        session = self.get_session()
        try:
            # Check if analysis already exists
            existing = session.query(BrandAnalysis).filter(
                BrandAnalysis.website_url == brand_context.website_url
            ).first()
            
            if existing:
                # Update existing record
                brand_analysis = existing
                brand_analysis.updated_at = datetime.utcnow()
            else:
                # Create new record
                brand_analysis = BrandAnalysis()
            
            # Update brand analysis fields
            brand_analysis.website_url = brand_context.website_url
            brand_analysis.brand_name = brand_context.brand_name
            brand_analysis.about_brand = brand_context.about_brand
            brand_analysis.currency = brand_context.currency
            brand_analysis.country = brand_context.country
            brand_analysis.total_products = brand_context.total_products
            brand_analysis.extraction_success = brand_context.extraction_success
            brand_analysis.extraction_notes = brand_context.extraction_notes
            brand_analysis.analysis_timestamp = brand_context.analysis_timestamp
            
            if not existing:
                session.add(brand_analysis)
            
            session.commit()
            session.refresh(brand_analysis)
            brand_id = brand_analysis.id
            
            # Clear existing related data if updating
            if existing:
                session.query(Product).filter(Product.brand_id == brand_id).delete()
                session.query(HeroProduct).filter(HeroProduct.brand_id == brand_id).delete()
                session.query(SocialHandle).filter(SocialHandle.brand_id == brand_id).delete()
                session.query(FAQ).filter(FAQ.brand_id == brand_id).delete()
                session.query(Policy).filter(Policy.brand_id == brand_id).delete()
                session.query(ImportantLink).filter(ImportantLink.brand_id == brand_id).delete()
                session.query(ContactInfo).filter(ContactInfo.brand_id == brand_id).delete()
                session.commit()
            
            # Save products
            for product in brand_context.product_catalog:
                db_product = Product(
                    brand_id=brand_id,
                    shopify_id=product.id,
                    title=product.title,
                    description=product.description,
                    price=product.price,
                    compare_at_price=product.compare_at_price,
                    vendor=product.vendor,
                    product_type=product.product_type,
                    handle=product.handle,
                    url=product.url,
                    images=product.images,
                    variants=product.variants,
                    tags=product.tags,
                    available=product.available
                )
                session.add(db_product)
            
            # Save hero products
            for hero_product in brand_context.hero_products:
                db_hero = HeroProduct(
                    brand_id=brand_id,
                    product_handle=hero_product.handle
                )
                session.add(db_hero)
            
            # Save social handles
            for social in brand_context.social_handles:
                db_social = SocialHandle(
                    brand_id=brand_id,
                    platform=social.platform,
                    url=social.url,
                    handle=social.handle
                )
                session.add(db_social)
            
            # Save FAQs
            for faq in brand_context.faqs:
                db_faq = FAQ(
                    brand_id=brand_id,
                    question=faq.question,
                    answer=faq.answer,
                    category=faq.category
                )
                session.add(db_faq)
            
            # Save policies
            policies = [
                ('privacy_policy', brand_context.privacy_policy),
                ('return_policy', brand_context.return_policy),
                ('refund_policy', brand_context.refund_policy),
                ('terms_of_service', brand_context.terms_of_service),
                ('shipping_policy', brand_context.shipping_policy)
            ]
            
            for policy_type, policy in policies:
                if policy:
                    db_policy = Policy(
                        brand_id=brand_id,
                        policy_type=policy_type,
                        title=policy.title,
                        content=policy.content,
                        url=policy.url
                    )
                    session.add(db_policy)
            
            # Save important links
            for link in brand_context.important_links:
                db_link = ImportantLink(
                    brand_id=brand_id,
                    title=link.title,
                    url=link.url,
                    description=link.description
                )
                session.add(db_link)
            
            # Save contact info
            if brand_context.contact_info:
                db_contact = ContactInfo(
                    brand_id=brand_id,
                    emails=brand_context.contact_info.emails,
                    phone_numbers=brand_context.contact_info.phone_numbers,
                    address=brand_context.contact_info.address
                )
                session.add(db_contact)
            
            session.commit()
            logger.info(f"Saved brand analysis for {brand_context.website_url} with ID {brand_id}")
            return brand_id
            
        except Exception as e:
            logger.error(f"Error saving brand analysis: {e}")
            session.rollback()
            return None
        finally:
            session.close()
    
    def get_brand_analysis(self, website_url: str) -> Optional[BrandAnalysis]:
        """Get brand analysis by website URL"""
        if not self.SessionLocal:
            return None
        
        session = self.get_session()
        try:
            return session.query(BrandAnalysis).filter(
                BrandAnalysis.website_url == website_url
            ).first()
        except Exception as e:
            logger.error(f"Error retrieving brand analysis: {e}")
            return None
        finally:
            session.close()
    
    def get_all_brands(self, limit: int = 100) -> List[BrandAnalysis]:
        """Get all brand analyses with limit"""
        if not self.SessionLocal:
            return []
        
        session = self.get_session()
        try:
            return session.query(BrandAnalysis).limit(limit).all()
        except Exception as e:
            logger.error(f"Error retrieving all brands: {e}")
            return []
        finally:
            session.close()


# Global database manager instance
db_manager = DatabaseManager()


def get_database() -> DatabaseManager:
    """Get database manager instance"""
    return db_manager
