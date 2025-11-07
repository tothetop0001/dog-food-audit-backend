# Dog Food API

A comprehensive FastAPI project for dog food data scraping and REST API services.

## Features

- **Web Scraping**: Automated collection of dog food data from various sources
- **REST API**: Complete API for reading dog food information
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Task Scheduling**: Automated scraping with Celery and Redis
- **Docker Support**: Full containerization with Docker Compose
- **Monitoring**: Celery Flower for task monitoring
- **Logging**: Structured logging with JSON format
- **Testing**: Comprehensive test suite with pytest

## Project Structure

```
dog-food-api/
├── app/
│   ├── api/                    # FastAPI routes
│   │   └── v1/
│   │       ├── endpoints/      # API endpoints
│   │       └── api.py         # Router configuration
│   ├── core/                  # Core configuration
│   │   ├── config.py         # Settings management
│   │   ├── database.py       # Database configuration
│   │   └── logging.py        # Logging setup
│   ├── models/               # SQLAlchemy models
│   │   └── dog_food.py      # Dog food models
│   ├── schemas/              # Pydantic schemas
│   │   └── dog_food.py      # API schemas
│   ├── scrapers/             # Web scraping modules
│   │   ├── base.py          # Base scraper class
│   │   └── dog_food_scraper.py
│   ├── services/             # Business logic
│   │   ├── dog_food_service.py
│   │   └── scraping_service.py
│   ├── tasks/                # Background tasks
│   │   └── scraping_tasks.py
│   └── main.py              # FastAPI application
├── alembic/                 # Database migrations
├── scripts/                 # Utility scripts
├── tests/                   # Test suite
├── docker-compose.yml       # Docker Compose configuration
├── Dockerfile              # Docker image
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Quick Start

### Using Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd dog-food-api
   ```

2. **Start the services**
   ```bash
   docker-compose up -d
   ```

3. **Initialize the database**
   ```bash
   docker-compose exec api python scripts/init_db.py
   ```

4. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - API Base URL: http://localhost:8000/api/v1
   - Celery Flower: http://localhost:5555

### Manual Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Set up the database**
   ```bash
   # Create PostgreSQL database
   createdb dog_food_db
   
   # Run migrations
   alembic upgrade head
   
   # Initialize with sample data
   python scripts/init_db.py
   ```

4. **Start Redis**
   ```bash
   redis-server
   ```

5. **Start the application**
   ```bash
   # Start FastAPI
   uvicorn app.main:app --reload
   
   # Start Celery worker (in another terminal)
   celery -A app.tasks.scraping_tasks worker --loglevel=info
   
   # Start Celery beat (in another terminal)
   celery -A app.tasks.scraping_tasks beat --loglevel=info
   ```

## API Endpoints

### Products
- `GET /api/v1/products/` - List all products
- `GET /api/v1/products/{product_id}` - Get a specific product
- `POST /api/v1/products/` - Create a new product

### Score
- `GET /api/v1/score/` - Compute a score for a product
  - Query params: `base_name` (required), `topper_name`, `storage_type`, `packaging_size`

### Scraping
- `POST /api/v1/scraping/run` - Run scraping job (background)
- `POST /api/v1/scraping/run-sync` - Run scraping job (synchronous)
- `GET /api/v1/scraping/stats` - Get scraping statistics

## Configuration

The application uses environment variables for configuration. Copy `env.example` to `.env` and modify as needed:

```bash
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/dog_food_db
DATABASE_URL_ASYNC=postgresql+asyncpg://username:password@localhost:5432/dog_food_db

# Redis
REDIS_URL=redis://localhost:6379/0

# API
API_V1_STR=/api/v1
PROJECT_NAME=Dog Food API
DEBUG=True

# Scraping
SCRAPING_INTERVAL_HOURS=24
SCRAPING_BATCH_SIZE=100
SCRAPING_DELAY_SECONDS=1
```

## Scraping

The scraping system is designed to be:
- **Respectful**: Includes delays between requests
- **Robust**: Handles errors gracefully with retries
- **Scalable**: Uses async operations and batching
- **Scheduled**: Runs automatically via Celery Beat

### Manual Scraping

```bash
# Run scraping manually
python scripts/run_scraping.py

# Or via API
curl -X POST http://localhost:8000/api/v1/scraping/run-sync
```

### Scheduled Scraping

- In local development via API, background tasks run using the local task runner (`app/tasks/local_tasks.py`).
- In Docker, Celery Beat schedules scraping; adjust schedule in `app/tasks/scraping_tasks.py`.

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
isort .
```

### Type Checking

```bash
mypy app/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

## Monitoring

- **API Health**: http://localhost:8000/health
- **Celery Flower**: http://localhost:5555
- **Logs**: Structured JSON logs in the console

## Production Deployment

1. **Set production environment variables**
2. **Use a production database**
3. **Configure proper CORS settings**
4. **Set up monitoring and alerting**
5. **Use a reverse proxy (nginx)**
6. **Enable SSL/TLS**

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.
"# dog-food-audit-backend" 
