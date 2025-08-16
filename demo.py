#!/usr/bin/env python3
"""
Direct demonstration of the Shopify Insights Fetcher functionality.
This script runs the analysis directly without needing a web server.
"""

import json
from insights_extractor import InsightsExtractor
from competitor_service import CompetitorAnalysisService
from database import get_database
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demo_basic_analysis():
    """Demonstrate basic Shopify store analysis"""
    print("🔍 SHOPIFY STORE INSIGHTS FETCHER - DEMO")
    print("=" * 50)
    
    # Initialize the extractor
    extractor = InsightsExtractor()
    
    # Test stores
    test_stores = [
        "https://colourpop.com",
        "https://memy.co.in",
        "https://hairoriginals.com"
    ]
    
    for store_url in test_stores:
        try:
            print(f"\n🏪 Analyzing: {store_url}")
            print("-" * 30)
            
            # Extract insights
            brand_context = extractor.extract_all_insights(store_url)
            
            # Display results
            print(f"✅ Analysis completed successfully!")
            print(f"📝 Brand Name: {brand_context.brand_name or 'Not detected'}")
            print(f"🛍️  Total Products: {brand_context.total_products}")
            print(f"🏆 Hero Products: {len(brand_context.hero_products)}")
            print(f"❓ FAQs Found: {len(brand_context.faqs)}")
            print(f"📱 Social Handles: {len(brand_context.social_handles)}")
            
            # Show social handles
            if brand_context.social_handles:
                print("   Social Media:")
                for social in brand_context.social_handles[:3]:  # Show first 3
                    print(f"     - {social.platform.title()}: {social.url}")
            
            # Show policies found
            policies_found = 0
            policies = ['privacy_policy', 'return_policy', 'refund_policy', 'terms_of_service', 'shipping_policy']
            for policy in policies:
                if getattr(brand_context, policy, None):
                    policies_found += 1
            print(f"📋 Policies Found: {policies_found}/5")
            
            # Show contact info
            if brand_context.contact_info.emails:
                print(f"📧 Emails: {', '.join(brand_context.contact_info.emails[:2])}")
            
            # Show sample products
            if brand_context.product_catalog:
                print(f"🛒 Sample Products:")
                for product in brand_context.product_catalog[:3]:  # Show first 3
                    price = product.price or "N/A"
                    print(f"     - {product.title} (${price})")
            
            # Show extraction notes
            if brand_context.extraction_notes:
                print(f"📝 Notes: {', '.join(brand_context.extraction_notes)}")
            
            print(f"💾 Analysis Timestamp: {brand_context.analysis_timestamp}")
            
        except ValueError as e:
            print(f"❌ Error: {e}")
        except Exception as e:
            print(f"💥 Unexpected error: {e}")
        
        print("\n" + "="*50)

def demo_competitor_analysis():
    """Demonstrate competitor analysis functionality"""
    print("\n🎯 COMPETITOR ANALYSIS DEMO")
    print("=" * 30)
    
    try:
        # Initialize services
        extractor = InsightsExtractor()
        competitor_service = CompetitorAnalysisService()
        
        # Analyze primary brand
        primary_url = "https://colourpop.com"
        print(f"🏪 Primary Brand: {primary_url}")
        
        brand_context = extractor.extract_all_insights(primary_url)
        print(f"✅ Primary analysis complete: {brand_context.brand_name}")
        
        # Perform competitor analysis
        print("\n🔍 Finding competitors...")
        competitor_analysis = competitor_service.analyze_competitors(brand_context, max_competitors=2)
        
        print(f"📊 Analysis Summary: {competitor_analysis.analysis_summary}")
        print(f"🏢 Competitors Found: {len(competitor_analysis.competitors)}")
        
        for i, competitor in enumerate(competitor_analysis.competitors, 1):
            print(f"\n   Competitor {i}: {competitor.brand_name or competitor.website_url}")
            print(f"     Products: {competitor.total_products}")
            print(f"     Social Handles: {len(competitor.social_handles)}")
            
    except Exception as e:
        print(f"❌ Competitor analysis error: {e}")

def demo_data_export():
    """Demonstrate data export functionality"""
    print("\n💾 DATA EXPORT DEMO")
    print("=" * 20)
    
    try:
        extractor = InsightsExtractor()
        brand_context = extractor.extract_all_insights("https://memy.co.in")
        
        # Export to JSON
        output_file = "brand_analysis_sample.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(brand_context.dict(), f, indent=2, default=str)
        
        print(f"✅ Data exported to: {output_file}")
        print(f"📄 File size: {len(open(output_file).read())} characters")
        
        # Show sample of exported data structure
        sample_data = {
            "website_url": brand_context.website_url,
            "brand_name": brand_context.brand_name,
            "total_products": brand_context.total_products,
            "policies_count": sum(1 for policy in ['privacy_policy', 'return_policy', 'refund_policy', 'terms_of_service', 'shipping_policy'] if getattr(brand_context, policy, None)),
            "social_handles_count": len(brand_context.social_handles),
            "faqs_count": len(brand_context.faqs)
        }
        
        print("\n📋 Sample exported data structure:")
        print(json.dumps(sample_data, indent=2))
        
    except Exception as e:
        print(f"❌ Export error: {e}")

def main():
    """Main demo function"""
    print("🚀 Welcome to Shopify Store Insights Fetcher!")
    print("This demo shows the core functionality without needing a web server.\n")
    
    # Basic analysis demo
    demo_basic_analysis()
    
    # Competitor analysis demo (may take longer)
    try:
        demo_competitor_analysis()
    except Exception as e:
        print(f"⚠️  Competitor analysis skipped: {e}")
    
    # Data export demo
    try:
        demo_data_export()
    except Exception as e:
        print(f"⚠️  Data export demo skipped: {e}")
    
    print("\n🎉 Demo completed!")
    print("\n💡 Next steps:")
    print("1. Run 'python demo.py' to see this demo")
    print("2. Start the API server: 'uvicorn main:app --port 8001'")
    print("3. Visit http://localhost:8001/docs for interactive API docs")
    print("4. Use the Postman collection for API testing")
    print("5. Add OpenAI API key to .env for enhanced features")

if __name__ == "__main__":
    main()
