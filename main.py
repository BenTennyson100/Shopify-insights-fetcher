from fastapi import FastAPI, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging
import traceback
from datetime import datetime
import uvicorn

from models import BrandContext, APIResponse, WebsiteRequest, CompetitorAnalysis
from insights_extractor import InsightsExtractor
from llm_service import LLMService
from competitor_service import CompetitorAnalysisService
from database import get_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Shopify Store Insights Fetcher",
    description="API for extracting comprehensive insights from Shopify stores including products, policies, FAQs, and more.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
insights_extractor = InsightsExtractor()
llm_service = LLMService()
competitor_service = CompetitorAnalysisService()
db_manager = get_database()


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "message": "Shopify Store Insights Fetcher API",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "insights_extractor": "active",
            "llm_service": "active" if llm_service.enabled else "disabled (no API key)",
        },
        "timestamp": datetime.now().isoformat()
    }


@app.post("/analyze", 
         response_model=APIResponse,
         tags=["Analysis"],
         summary="Analyze Shopify Store",
         description="Extract comprehensive insights from a Shopify store URL")
async def analyze_shopify_store(request: WebsiteRequest):
    """
    Analyze a Shopify store and extract comprehensive insights including:
    - Product catalog and hero products
    - Policies (privacy, return, refund, etc.)
    - FAQs and customer support information  
    - Social media handles
    - Contact information
    - Important navigation links
    - Brand information and description
    """
    try:
        website_url = str(request.website_url)
        logger.info(f"Starting analysis for: {website_url}")
        
        # Extract insights
        brand_context = insights_extractor.extract_all_insights(website_url)
        
        # Enhance data using LLM if available
        if llm_service.enabled:
            try:
                # Enhance brand description
                if brand_context.about_brand:
                    enhanced_description = llm_service.enhance_brand_description(
                        brand_context.about_brand, 
                        brand_context.brand_name
                    )
                    if enhanced_description:
                        brand_context.about_brand = enhanced_description
                
                # Try to extract additional FAQs using LLM from main page content
                html_content, soup = insights_extractor.scraper.get_page_content(website_url)
                if soup and len(brand_context.faqs) < 3:  # If we have few FAQs, try to get more
                    page_text = soup.get_text()[:5000]  # Get first 5000 characters
                    additional_faqs = llm_service.structure_faqs(page_text)
                    
                    # Add unique FAQs
                    existing_questions = {faq.question.lower() for faq in brand_context.faqs}
                    for faq in additional_faqs:
                        if faq.question.lower() not in existing_questions:
                            brand_context.faqs.append(faq)
                            existing_questions.add(faq.question.lower())
                
                brand_context.extraction_notes.append("Enhanced data using LLM processing")
                
            except Exception as e:
                logger.warning(f"LLM enhancement failed: {e}")
                brand_context.extraction_notes.append("LLM enhancement partially failed")
        
        # Log successful analysis
        logger.info(f"Analysis completed for {website_url}. Products: {brand_context.total_products}, FAQs: {len(brand_context.faqs)}")
        
        # Save to database if available
        if db_manager and db_manager.SessionLocal:
            try:
                brand_id = db_manager.save_brand_analysis(brand_context)
                if brand_id:
                    brand_context.extraction_notes.append(f"Saved to database with ID: {brand_id}")
            except Exception as e:
                logger.warning(f"Failed to save to database: {e}")
                brand_context.extraction_notes.append("Database save failed")
        
        return APIResponse(
            success=True,
            message="Analysis completed successfully",
            data=brand_context
        )
        
    except ValueError as e:
        # Handle validation errors (e.g., not a Shopify store)
        logger.warning(f"Validation error for {website_url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    
    except Exception as e:
        # Handle internal server errors
        logger.error(f"Internal error analyzing {website_url}: {e}")
        logger.error(traceback.format_exc())
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/analyze-with-competitors",
         response_model=CompetitorAnalysis,
         tags=["Analysis", "Bonus"],
         summary="Analyze Store with Competitor Analysis",
         description="Analyze a Shopify store and find similar competitor stores (Bonus feature)")
async def analyze_with_competitors(request: WebsiteRequest, background_tasks: BackgroundTasks):
    """
    Analyze a Shopify store and find similar competitors.
    This bonus feature finds and analyzes actual competitor stores.
    """
    try:
        # First, analyze the primary brand
        primary_analysis = await analyze_shopify_store(request)
        
        if not primary_analysis.success or not primary_analysis.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to analyze primary brand"
            )
        
        # Perform comprehensive competitor analysis
        competitor_analysis = competitor_service.analyze_competitors(
            primary_analysis.data, 
            max_competitors=3
        )
        
        # Save competitor analysis to database if available
        if db_manager and db_manager.SessionLocal:
            try:
                for competitor in competitor_analysis.competitors:
                    db_manager.save_brand_analysis(competitor)
                logger.info(f"Saved {len(competitor_analysis.competitors)} competitors to database")
            except Exception as e:
                logger.warning(f"Failed to save competitors to database: {e}")
        
        return competitor_analysis
        
    except Exception as e:
        logger.error(f"Error in competitor analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Competitor analysis failed: {str(e)}"
        )


@app.get("/supported-features", tags=["Info"])
async def supported_features():
    """Get list of supported features and their availability"""
    return {
        "mandatory_features": {
            "product_catalog": "✅ Available",
            "hero_products": "✅ Available", 
            "privacy_policy": "✅ Available",
            "return_refund_policies": "✅ Available",
            "brand_faqs": "✅ Available",
            "social_handles": "✅ Available",
            "contact_details": "✅ Available",
            "brand_context": "✅ Available",
            "important_links": "✅ Available"
        },
        "bonus_features": {
            "competitor_analysis": "✅ Available (finds and analyzes actual competitors)",
            "database_persistence": "✅ Available" if db_manager and db_manager.SessionLocal else "❌ Requires database configuration",
            "llm_enhancement": "✅ Available" if llm_service.enabled else "❌ Requires OpenAI API key"
        },
        "enhancements": {
            "error_handling": "✅ Comprehensive",
            "data_validation": "✅ Pydantic models",
            "clean_code": "✅ OOP principles, SOLID design",
            "api_documentation": "✅ FastAPI auto-docs"
        }
    }


# Exception handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "details": exc.errors()
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "error_code": "HTTP_ERROR",
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
