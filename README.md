# Assignment Scraper

A comprehensive, production-ready web scraping solution built with FastAPI, featuring microservices architecture, advanced scraping techniques, and modern Python patterns.

## ✨ Features

- **Undetectable scraping** with Zendriver (Chrome DevTools Protocol)
- **Multi-target scraping** (job listings, member clubs, support resources)  
- **Asynchronous processing** with Celery
- **RESTful API** with FastAPI
- **Database migrations** with Alembic
- **Monitoring** with Prometheus & Grafana
- **Docker containerization** for easy deployment
- **Chat interface** for conversational interaction with scraped data

## Features

### 🚀 Core Capabilities
- **Multi-website scraping** with support for job listings, member clubs, and support resources
- **Undetectable scraping** with [Zendriver](https://github.com/cdpdriver/zendriver) using Chrome DevTools Protocol
- **Modern scraping techniques** using BeautifulSoup, Playwright, and Selenium as fallbacks
- **Anti-bot protection bypass** with automatic cookie/profile management
- **Intelligent data extraction** with configurable CSS selectors and XPath
- **Asynchronous operations** for high-performance concurrent scraping
- **Background task processing** with Celery for scalable operations

### 🏗️ Architecture
- **Clean Architecture** with Domain-Driven Design (DDD) principles
- **Microservices-ready** with proper separation of concerns
- **Dependency Injection** using FastAPI's built-in DI system
- **Repository Pattern** for data persistence abstraction
- **Use Cases** for business logic encapsulation

### 🔧 Advanced Features
- **Rate limiting** and intelligent request throttling
- **User agent rotation** to avoid detection
- **Circuit breaker pattern** for resilient service communication
- **Caching layer** with Redis for improved performance
- **Database migrations** with Alembic
- **Monitoring & Metrics** with Prometheus and Grafana
- **Structured logging** for better observability

## Technology Stack

- **Backend**: FastAPI 0.104+ (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache/Message Broker**: Redis
- **Task Queue**: Celery
- **Web Scraping**: **Zendriver** (undetectable), BeautifulSoup4, Playwright, Selenium
- **HTTP Client**: httpx with async support
- **Monitoring**: Prometheus, Grafana
- **Containerization**: Docker & Docker Compose
- **Database Migrations**: Alembic

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### 1. Clone and Setup
```bash
git clone <repository-url>
cd assignment-scraper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 3. Database Setup
```bash
# Start database with Docker
docker-compose up -d postgres redis

# Run database migrations
alembic upgrade head
```

### 4. Start Application
```bash
# Development mode
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# With Docker Compose (recommended)
docker-compose up
```

### 5. Start Workers (Optional)
```bash
# In separate terminals
celery -A src.infrastructure.celery.worker worker --loglevel=info
celery -A src.infrastructure.celery.worker beat --loglevel=info
```

## API Documentation

Once running, access interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Job Management
- `POST /api/v1/jobs` - Create scraping job
- `GET /api/v1/jobs` - List jobs with pagination
- `GET /api/v1/jobs/{job_id}` - Get specific job
- `POST /api/v1/jobs/{job_id}/execute` - Execute job
- `DELETE /api/v1/jobs/{job_id}` - Delete job

#### Data Retrieval
- `GET /api/v1/jobs/{job_id}/data` - Get job results
- `GET /api/v1/data` - Query scraped data

#### Utility
- `POST /api/v1/validate-url` - Validate URL accessibility
- `POST /api/v1/bulk-scrape` - Bulk scraping operation
- `POST /api/v1/search-jobs` - Search job listings

## Usage Examples

### Basic Scraping Job
```python
import httpx

# Create a scraping job
job_data = {
    "name": "Job Listings Scraper",
    "targets": [
        {
            "url": "https://example-jobs.com",
            "data_type": "job_listing",
            "selectors": {
                "title": ".job-title",
                "company": ".company-name",
                "location": ".job-location"
            }
        }
    ],
    "config": {
        "delay_between_requests": 2,
        "max_retries": 3
    }
}

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/jobs",
        json=job_data
    )
    job = response.json()
    print(f"Created job: {job['id']}")

    # Execute the job
    await client.post(f"http://localhost:8000/api/v1/jobs/{job['id']}/execute")
```

### Bulk URL Validation
```python
urls_to_validate = [
    "https://example1.com",
    "https://example2.com",
    "https://example3.com"
]

validation_data = {"url": url}
for url in urls_to_validate:
    response = await client.post(
        "http://localhost:8000/api/v1/validate-url",
        json={"url": url}
    )
    result = response.json()
    print(f"{url}: {'✓' if result['is_valid'] else '✗'}")
```

### Zendriver Demo - Undetectable Scraping

Experience the power of undetectable web scraping with our Zendriver demonstration:

```bash
# Run the interactive Zendriver demo
python examples/zendriver_demo.py
```

The demo showcases:
- **Bot detection bypass** - Test against anti-bot detection systems
- **Job board scraping** - Extract data from protected job sites like Indeed
- **Dynamic content handling** - JavaScript-heavy sites with AJAX loading
- **Browser fingerprinting** - Advanced evasion techniques
- **Cookie management** - Session handling and authentication

**Features demonstrated:**
- 🚀 **Undetectable scraping** using Chrome DevTools Protocol
- 🛡️ **Anti-bot protection bypass** with realistic browser behavior
- ⚡ **Async-first design** for high-performance operations
- 🍪 **Automatic cookie/session management**
- 🖥️ **Real browser viewport** and user agent handling

## 🤖 Chat Interface

The Assignment Scraper now includes a **conversational AI interface** that allows you to interact with scraped data using natural language!

### Chat Endpoints

#### **POST `/api/v1/chat`** - Chat with Scraped Data
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What job listings are available?",
    "job_id": null,
    "data_type": "job_listing"
  }'
```

**Response:**
```json
{
  "response": "I found 15 job listings. Here are the top 3:\n\n1. **Python Developer** at TechCorp\n   📍 Sydney, NSW\n\n2. **Data Scientist** at DataCorp\n   📍 Melbourne, VIC\n\n3. **Software Engineer** at StartupCo\n   📍 Brisbane, QLD\n\n... and 12 more positions.",
  "data_used": ["uuid1", "uuid2", "uuid3"],
  "suggestions": [
    "Show me the salary ranges for these positions",
    "What are the common requirements?",
    "Which locations have the most jobs?"
  ],
  "conversation_id": "conv-123",
  "metadata": {
    "intent": "search_jobs",
    "data_count": 15
  }
}
```

### Example Chat Queries

**🔍 Job-Related Queries:**
```bash
# Count jobs
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "How many job listings do we have?"}'

# Job requirements
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the common job requirements?"}'

# Location-based search
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me jobs in Sydney"}'
```

**🏢 Club/Organization Queries:**
```bash
# Find clubs
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What soccer clubs have been found?"}'

# Club locations
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "How many clubs are in each location?"}'
```

**📋 Data Summary Queries:**
```bash
# Overview
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Give me a summary of all scraped data"}'

# Recent data
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What was scraped recently?"}'
```

#### **POST `/api/v1/data-summary`** - Get Data Summary
```bash
curl -X POST "http://localhost:8000/api/v1/data-summary" \
  -H "Content-Type: application/json" \
  -d '{
    "data_type": null,
    "job_id": null,
    "date_range": "last_week"
  }'
```

#### **GET `/api/v1/chat/suggestions`** - Get Chat Suggestions
```bash
curl "http://localhost:8000/api/v1/chat/suggestions"
```

### Chat Features

- **🎯 Intent Recognition:** Automatically understands what you're asking about
- **🔍 Smart Filtering:** Filter by job ID, data type, or date range  
- **💡 Suggestions:** Get follow-up question suggestions
- **📊 Rich Responses:** Formatted responses with markdown, emojis, and structure
- **🗣️ Conversation History:** Maintain context across multiple messages

### Supported Data Types

The chat interface can query three types of scraped data based on the PDF requirements:

1. **`job_listing`** - Job opportunities from Medrecruit
2. **`member_club`** - Soccer clubs from AZ Soccer Association  
3. **`support_resource`** - Support resources from HP Support

## Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Application
APP_NAME=AssignmentScraper
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db

# Redis
REDIS_URL=redis://localhost:6379/0

# Scraping
REQUEST_TIMEOUT=30
MAX_RETRIES=3
RATE_LIMIT=10
DELAY_BETWEEN_REQUESTS=1

# Security
SECRET_KEY=your-secret-key-here
```

### Scraping Configuration

Configure scraping behavior per job:

```json
{
  "config": {
    "delay_between_requests": 2,
    "max_retries": 3,
    "timeout": 30,
    "use_proxy": false,
    "javascript_enabled": true,
    "custom_headers": {
      "User-Agent": "Custom Bot 1.0"
    }
  }
}
```

## Docker Deployment

### Full Stack with Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Scale workers
docker-compose up -d --scale worker=3

# Stop services
docker-compose down
```

### Production Deployment
```bash
# Build production image
docker build -t assignment-scraper:latest .

# Run with environment variables
docker run -d \
  --name scraper-api \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_URL=redis://... \
  assignment-scraper:latest
```

## Monitoring

### Health Checks
- **Application**: `GET /health`
- **Database**: Automatic health checks in Docker Compose
- **Redis**: Automatic health checks in Docker Compose

### Metrics & Monitoring
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

### Logging
Structured JSON logging with configurable levels:
```bash
# View application logs
docker-compose logs -f api

# View worker logs
docker-compose logs -f worker
```

## Development

### Project Structure
```
assignment-scraper/
├── src/
│   ├── api/                    # API layer (FastAPI routes)
│   ├── application/           # Application services & use cases
│   ├── domain/               # Domain entities & business logic
│   ├── infrastructure/       # External services & implementations
│   └── config/              # Configuration management
├── alembic/                 # Database migrations
├── tests/                   # Test suites
├── docker-compose.yml       # Local development setup
├── Dockerfile              # Container definition
└── requirements.txt        # Python dependencies
```

### Adding New Scrapers

1. **Create Domain Entity** (if needed):
```python
# src/domain/entities/scraping.py
@dataclass
class CustomDataType:
    field1: str
    field2: Optional[str] = None
```

2. **Implement Scraper Service**:
```python
# src/infrastructure/services/custom_scraper.py
class CustomScraperService(WebScraperService):
    async def scrape_url(self, target: ScrapingTarget) -> ScrapedData:
        # Implement custom scraping logic
        pass
```

3. **Add Use Case**:
```python
# src/application/use_cases/custom_use_cases.py
class CustomScrapingUseCase:
    def __init__(self, scraper: CustomScraperService):
        self.scraper = scraper
```

4. **Create API Endpoint**:
```python
# src/main.py
@app.post("/api/v1/custom-scrape")
async def custom_scrape(request: CustomRequest):
    # Implementation
```

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_scraping.py -v
```

### Code Quality
```bash
# Format code
black src/
isort src/

# Lint code
flake8 src/
mypy src/
```

## Performance & Scalability

### Horizontal Scaling
- **API Servers**: Scale FastAPI instances behind a load balancer
- **Workers**: Scale Celery workers with `docker-compose up --scale worker=N`
- **Database**: Use read replicas and connection pooling
- **Cache**: Redis Cluster for high availability

### Performance Optimization
- **Connection Pooling**: Configured for database and HTTP clients
- **Async Operations**: Non-blocking I/O throughout the application
- **Caching**: Redis caching for frequently accessed data
- **Rate Limiting**: Configurable per-domain rate limits

### Monitoring & Alerting
- **Application Metrics**: Custom Prometheus metrics
- **System Metrics**: CPU, memory, disk usage
- **Business Metrics**: Scraping success rates, job duration
- **Alerting**: Grafana alerts for critical thresholds

## Security

### Best Practices
- **No hardcoded secrets**: All sensitive data in environment variables
- **Input validation**: Pydantic models for request validation
- **Rate limiting**: Protection against abuse
- **CORS**: Configurable CORS policies
- **Non-root containers**: Docker containers run as non-root user

### Authentication (Optional Extension)
The application is ready for authentication integration:
- JWT token support (commented in code)
- OAuth2 flow implementation
- API key authentication

## Troubleshooting

### Common Issues

1. **Database Connection Failed**:
```bash
# Check database status
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
alembic upgrade head
```

2. **Playwright Browser Issues**:
```bash
# Reinstall browsers
playwright install --force

# Install system dependencies
playwright install-deps
```

3. **Worker Not Processing Jobs**:
```bash
# Check worker status
docker-compose logs worker

# Restart worker
docker-compose restart worker

# Check Redis connection
docker-compose exec redis redis-cli ping
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions and support:
- Create an issue on GitHub
- Check the [API documentation](http://localhost:8000/docs)
- Review the troubleshooting section above

---

**Built with ❤️ using FastAPI and modern Python practices** 