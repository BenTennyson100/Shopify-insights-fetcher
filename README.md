# Shopify Store Insights Fetcher

A comprehensive Python application built with FastAPI that extracts detailed insights from Shopify stores without using the official Shopify API. The application provides structured analysis of product catalogs, policies, FAQs, social media presence, and more.

## 🚀 Features

### Mandatory Features (✅ Implemented)

- **Product Catalog Extraction**: Complete product listings from `/products.json` endpoint
- **Hero Products Identification**: Products featured on the homepage
- **Policy Extraction**: Privacy policy, return/refund policies, terms of service
- **FAQ Collection**: Brand FAQs from various page structures
- **Social Media Handles**: Instagram, Facebook, Twitter, TikTok, YouTube, LinkedIn, Pinterest
- **Contact Information**: Email addresses, phone numbers, physical addresses
- **Brand Context**: About the brand, description, and story
- **Important Links**: Order tracking, contact us, blogs, support links

### Bonus Features (🔶 Partially Implemented)

- **LLM Enhancement**: Uses OpenAI API to structure unorganized data
- **Competitor Analysis**: Search term generation for finding similar brands
- **Database Persistence**: MySQL integration for storing analysis results

### Technical Excellence (✅ Implemented)

- **Clean Code**: OOP principles, SOLID design patterns
- **Comprehensive Error Handling**: 401, 500, and validation errors
- **RESTful API Design**: Well-structured endpoints with proper HTTP methods
- **Data Validation**: Pydantic models for request/response validation
- **Auto-Documentation**: FastAPI automatic API documentation
- **Logging**: Comprehensive logging throughout the application

## 📋 Requirements

- Python 3.8+
- MySQL (optional, for database persistence)
- OpenAI API Key (optional, for LLM features)

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd shopify-insights-fetcher
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**:
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

5. **Database Setup (Optional)**:
   ```python
   # Run this once to create database tables
   python -c "from database import db_manager; db_manager.create_tables()"
   ```

## 🔧 Configuration

Create a `.env` file with the following variables:

```bash
# Optional: OpenAI API Key for enhanced data processing
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Database URL for data persistence
DATABASE_URL=mysql+pymysql://username:password@localhost/shopify_insights

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

## 🚀 Usage

### Starting the API Server

```bash
python main.py
```

The API will be available at:
- **Main API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Endpoints

#### 1. Analyze Shopify Store

**POST** `/analyze`

Extracts comprehensive insights from a Shopify store.

**Request Body**:
```json
{
  "website_url": "https://colourpop.com"
}
```

**Response Example**:
```json
{
  "success": true,
  "message": "Analysis completed successfully",
  "data": {
    "website_url": "https://colourpop.com",
    "brand_name": "ColourPop Cosmetics",
    "about_brand": "Clean brand description...",
    "product_catalog": [
      {
        "id": "123456",
        "title": "Lippie Pencil",
        "price": "6.00",
        "description": "Product description...",
        "images": ["https://..."],
        "available": true
      }
    ],
    "hero_products": [...],
    "social_handles": [
      {
        "platform": "instagram",
        "url": "https://instagram.com/colourpopcosmetics",
        "handle": "colourpopcosmetics"
      }
    ],
    "contact_info": {
      "emails": ["help@colourpop.com"],
      "phone_numbers": ["+1-xxx-xxx-xxxx"]
    },
    "faqs": [
      {
        "question": "Do you offer international shipping?",
        "answer": "Yes, we ship worldwide..."
      }
    ],
    "privacy_policy": {
      "title": "Privacy Policy",
      "content": "Policy content...",
      "url": "https://colourpop.com/pages/privacy-policy"
    },
    "important_links": [...],
    "total_products": 150,
    "currency": "USD",
    "analysis_timestamp": "2024-01-15T10:30:00Z",
    "extraction_success": true
  }
}
```

#### 2. Competitor Analysis (Bonus)

**POST** `/analyze-with-competitors`

Analyzes a store and generates competitor search terms.

#### 3. Health Check

**GET** `/health`

Returns service health status and feature availability.

#### 4. Supported Features

**GET** `/supported-features`

Lists all available features and their implementation status.

## 📊 Data Models

### BrandContext (Main Response Model)
- **Brand Information**: Name, description, currency, country
- **Products**: Full catalog and hero products
- **Policies**: Privacy, return, refund, terms, shipping
- **Social Media**: All social platform handles
- **Contact**: Emails, phones, address
- **FAQs**: Question-answer pairs
- **Links**: Important navigation links
- **Metadata**: Analysis timestamp, success status, notes

## 🧪 Testing

### Manual Testing with Postman

1. **Import the provided Postman collection** (see `postman_collection.json`)
2. **Test with sample Shopify stores**:
   - https://colourpop.com
   - https://memy.co.in  
   - https://hairoriginals.com

### API Testing Examples

```bash
# Basic analysis
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"website_url": "https://colourpop.com"}'

# Health check
curl -X GET "http://localhost:8000/health"
```

## 🏗️ Architecture

```
shopify-insights-fetcher/
├── main.py              # FastAPI application and routes
├── models.py            # Pydantic data models
├── scraper.py           # Web scraping utilities
├── insights_extractor.py # Core extraction logic
├── llm_service.py       # OpenAI integration
├── database.py          # Database models and operations
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
└── README.md           # Documentation
```

### Key Components

1. **ShopifyScraper**: Handles web scraping and Shopify-specific endpoint access
2. **InsightsExtractor**: Main business logic for extracting structured insights
3. **LLMService**: OpenAI integration for enhancing unstructured data
4. **DatabaseManager**: Optional persistence layer with MySQL
5. **FastAPI App**: RESTful API with comprehensive error handling

## 🔍 Supported Shopify Stores

The application works with any Shopify store. It automatically detects if a website is powered by Shopify and extracts available data. Examples of supported stores:

- **Fashion**: Fashion Nova, Gymshark, Steve Madden
- **Beauty**: ColourPop, Jeffree Star Cosmetics
- **Lifestyle**: Allbirds, Bulletproof
- **Gaming**: Fangamer, G FUEL

## ⚡ Performance & Scalability

- **Concurrent Processing**: FastAPI's async support
- **Caching**: BeautifulSoup and session reuse
- **Error Recovery**: Graceful degradation for missing data
- **Rate Limiting**: Built-in request throttling
- **Memory Efficient**: Streaming and pagination support

## 🛡️ Error Handling

- **401 Unauthorized**: Invalid or non-Shopify URLs
- **500 Internal Server Error**: Processing failures with detailed logs
- **422 Validation Error**: Invalid request format
- **Comprehensive Logging**: All operations logged with appropriate levels

## 🔮 Future Enhancements

1. **Advanced Competitor Analysis**: Real web search integration
2. **Image Analysis**: Product image classification
3. **Price Tracking**: Historical price monitoring
4. **Performance Metrics**: Response time optimization
5. **Batch Processing**: Multiple store analysis
6. **Export Features**: CSV, Excel, PDF reports

## 📝 Development Guidelines

- **Code Style**: Follow PEP 8 standards
- **Testing**: Add unit tests for new features
- **Documentation**: Update README for new endpoints
- **Error Handling**: Always include appropriate exception handling
- **Logging**: Use structured logging for debugging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:
1. Check the [documentation](http://localhost:8000/docs) when running
2. Review the logs for error details
3. Ensure environment variables are properly configured
4. Verify the target website is a Shopify store

## 📊 Example Analysis Results

The application successfully extracts comprehensive insights from Shopify stores, including:

- **150+ products** from large stores like ColourPop
- **5-20 FAQs** depending on store structure  
- **3-8 social media handles** across major platforms
- **Complete policy suite** (privacy, returns, shipping, etc.)
- **10-30 important links** for navigation and support

This makes it an invaluable tool for competitor analysis, market research, and e-commerce intelligence gathering.
