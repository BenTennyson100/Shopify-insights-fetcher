#!/usr/bin/env python3
"""
Simple test script to demonstrate the Shopify Insights Fetcher API functionality.
Run this script after starting the main API server to test basic functionality.
"""

import requests
import json
import sys
import time
from typing import Dict, Any

# API Configuration
BASE_URL = "http://localhost:8000"

def test_health_check() -> bool:
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check: {data['status']}")
            print(f"   Services: {data['services']}")
            return True
        else:
            print(f"❌ Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health Check Error: {e}")
        return False

def test_supported_features() -> bool:
    """Test the supported features endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/supported-features")
        if response.status_code == 200:
            data = response.json()
            print("✅ Supported Features:")
            
            print("   Mandatory Features:")
            for feature, status in data['mandatory_features'].items():
                print(f"     {feature}: {status}")
            
            print("   Bonus Features:")
            for feature, status in data['bonus_features'].items():
                print(f"     {feature}: {status}")
            
            return True
        else:
            print(f"❌ Supported Features Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Supported Features Error: {e}")
        return False

def test_shopify_analysis(website_url: str) -> Dict[str, Any]:
    """Test the main analysis endpoint"""
    try:
        print(f"\n🔍 Analyzing: {website_url}")
        
        payload = {"website_url": website_url}
        response = requests.post(
            f"{BASE_URL}/analyze",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60  # 60 second timeout for analysis
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                brand_data = data['data']
                print(f"✅ Analysis Successful for {website_url}")
                print(f"   Brand Name: {brand_data.get('brand_name', 'N/A')}")
                print(f"   Total Products: {brand_data.get('total_products', 0)}")
                print(f"   FAQs Found: {len(brand_data.get('faqs', []))}")
                print(f"   Social Handles: {len(brand_data.get('social_handles', []))}")
                print(f"   Policies Found: {sum(1 for policy in ['privacy_policy', 'return_policy', 'refund_policy', 'terms_of_service', 'shipping_policy'] if brand_data.get(policy))}")
                print(f"   Hero Products: {len(brand_data.get('hero_products', []))}")
                
                if brand_data.get('extraction_notes'):
                    print(f"   Notes: {', '.join(brand_data['extraction_notes'])}")
                
                return brand_data
            else:
                print(f"❌ Analysis Failed: {data.get('message', 'Unknown error')}")
                return {}
        else:
            print(f"❌ Analysis Request Failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('message', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text}")
            return {}
    except requests.exceptions.Timeout:
        print(f"⏰ Analysis Timeout: {website_url} took too long to analyze")
        return {}
    except Exception as e:
        print(f"❌ Analysis Error: {e}")
        return {}

def test_invalid_url() -> bool:
    """Test error handling with invalid URL"""
    try:
        print("\n🧪 Testing error handling with invalid URL...")
        
        payload = {"website_url": "https://google.com"}
        response = requests.post(
            f"{BASE_URL}/analyze",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 401:
            print("✅ Error handling works correctly (401 for non-Shopify site)")
            return True
        else:
            print(f"❌ Expected 401 error, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def main():
    """Main test runner"""
    print("🚀 Starting Shopify Insights Fetcher API Tests")
    print("=" * 50)
    
    # Test 1: Health Check
    if not test_health_check():
        print("💥 Health check failed. Make sure the API server is running.")
        sys.exit(1)
    
    print()
    
    # Test 2: Supported Features
    if not test_supported_features():
        print("💥 Supported features test failed.")
        sys.exit(1)
    
    # Test 3: Error Handling
    test_invalid_url()
    
    # Test 4: Actual Shopify Store Analysis
    test_stores = [
        "https://colourpop.com",
        "https://memy.co.in",
        "https://hairoriginals.com"
    ]
    
    successful_analyses = []
    
    for store_url in test_stores:
        result = test_shopify_analysis(store_url)
        if result:
            successful_analyses.append((store_url, result))
        
        # Add delay between requests to be respectful
        time.sleep(3)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print(f"✅ Successful analyses: {len(successful_analyses)}/{len(test_stores)}")
    
    if successful_analyses:
        print("\nSuccessful stores:")
        for url, data in successful_analyses:
            print(f"  - {url}: {data.get('brand_name', 'Unknown')} ({data.get('total_products', 0)} products)")
    
    # Test 5: Competitor Analysis (if available)
    if successful_analyses:
        print("\n🎯 Testing competitor analysis...")
        first_store = successful_analyses[0][0]
        try:
            payload = {"website_url": first_store}
            response = requests.post(
                f"{BASE_URL}/analyze-with-competitors",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120  # Longer timeout for competitor analysis
            )
            
            if response.status_code == 200:
                data = response.json()
                competitors_found = len(data.get('competitors', []))
                print(f"✅ Competitor analysis completed: {competitors_found} competitors found")
                if data.get('analysis_summary'):
                    print(f"   Summary: {data['analysis_summary']}")
            else:
                print(f"❌ Competitor analysis failed: {response.status_code}")
        except requests.exceptions.Timeout:
            print("⏰ Competitor analysis timeout (this is normal for the first run)")
        except Exception as e:
            print(f"❌ Competitor analysis error: {e}")
    
    print("\n🎉 Testing completed!")
    print("\n💡 To explore more features:")
    print(f"   - Visit the API docs: {BASE_URL}/docs")
    print(f"   - Import the Postman collection: postman_collection.json")
    print(f"   - Check the logs for detailed analysis information")

if __name__ == "__main__":
    main()
