# Local Development Setup (Without Docker)

This guide will help you set up the Dog Food API for local development without Docker.

## Prerequisites

1. **Python 3.11+** installed on your system
2. **PostgreSQL** installed and running
3. **Git** (optional, for version control)

## Step 1: Install Python Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Or install in a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 2: Set Up PostgreSQL Database

### Create Database
```bash
# Connect to PostgreSQL
psql -U postgres

# Create the database
CREATE DATABASE dog_food_db;

# Create a user (optional)
CREATE USER dog_food_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE dog_food_db TO dog_food_user;

# Exit PostgreSQL
\q
```

### Alternative: Using createdb command
```bash
createdb -U postgres dog_food_db
```

## Step 3: Configure Environment

```bash
# Copy the environment template
copy env.example .env  # Windows
# or
cp env.example .env    # Linux/Mac

# Edit .env file with your PostgreSQL credentials
```

Update the `.env` file with your PostgreSQL settings:
```env
# Database Configuration (Local PostgreSQL)
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/dog_food_db
DATABASE_URL_ASYNC=postgresql+asyncpg://postgres:your_password@localhost:5432/dog_food_db

# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME=Dog Food API
VERSION=0.1.0
DEBUG=True
SECRET_KEY=your-secret-key-here

# Scraping Configuration
SCRAPING_INTERVAL_HOURS=24
SCRAPING_BATCH_SIZE=100
SCRAPING_DELAY_SECONDS=1

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=text
```

## Step 4: Set Up Database Schema

```bash
# Run database migrations
alembic upgrade head
```

## Step 5: Initialize with Sample Data

```bash
# Run the setup script
python scripts/setup_local_dev.py

# Or manually initialize
python scripts/init_db.py
```

## Step 6: Start the Development Server

```bash
# Start the local development server
python app/main_local.py

# Or using uvicorn directly
uvicorn app.main_local:app --reload --host 0.0.0.0 --port 8000
```

## Step 7: Access the API

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Setup Info**: http://localhost:8000/setup
- **API Base URL**: http://localhost:8000/api/v1

## Optional: Redis for Background Tasks

If you want to use Redis for background tasks (instead of the memory broker):

### Install Redis
- **Windows**: Download from https://github.com/microsoftarchive/redis/releases
- **Linux**: `sudo apt-get install redis-server`
- **Mac**: `brew install redis`

### Start Redis
```bash
# Windows
redis-server

# Linux/Mac
redis-server
```

### Update .env
```env
REDIS_URL=redis://localhost:6379/0
```

## Development Commands

### Run Tests
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

### Database Operations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Manual Scraping
```bash
# Run scraping manually
python scripts/run_scraping.py

# Or via API
curl -X POST http://localhost:8000/api/v1/scraping/run-sync
```

## Project Structure

```
dog-food-api/
├── app/
│   ├── main_local.py          # Local development entry point
│   ├── core/
│   │   ├── config.py          # Production configuration
│   │   ├── local_config.py    # Local development configuration
│   │   ├── database.py        # Database setup
│   │   └── logging.py         # Logging configuration
│   ├── models/                # Database models
│   ├── schemas/               # Pydantic schemas
│   ├── api/                   # FastAPI routes
│   ├── services/              # Business logic
│   ├── scrapers/              # Web scraping
│   └── tasks/
│       ├── scraping_tasks.py  # Celery tasks (production)
│       └── local_tasks.py     # Local task runner
├── scripts/
│   ├── setup_local_dev.py     # Local setup script
│   ├── init_db.py            # Database initialization
│   └── run_scraping.py       # Manual scraping
├── tests/                     # Test suite
├── alembic/                   # Database migrations
├── .env                       # Environment variables
└── requirements.txt           # Python dependencies
```

## Troubleshooting

### Database Connection Issues
1. Make sure PostgreSQL is running
2. Check your credentials in `.env`
3. Verify the database exists
4. Check if the port (5432) is correct

### Import Errors
1. Make sure you're in the project root directory
2. Check if all dependencies are installed
3. Verify your Python path

### Migration Issues
1. Make sure the database exists
2. Check your database URL in `.env`
3. Try running `alembic upgrade head` again

### Scraping Issues
1. Check your internet connection
2. Verify the scraping delay settings
3. Check the logs for specific errors

## API Endpoints

### Dog Foods
- `GET /api/v1/dog-foods/` - Search and filter dog foods
- `GET /api/v1/dog-foods/{id}` - Get specific dog food
- `POST /api/v1/dog-foods/` - Create new dog food
- `PUT /api/v1/dog-foods/{id}` - Update dog food
- `DELETE /api/v1/dog-foods/{id}` - Delete dog food

### Brands
- `GET /api/v1/brands/` - Get all brands
- `POST /api/v1/brands/` - Create new brand

### Categories
- `GET /api/v1/categories/` - Get all categories
- `POST /api/v1/categories/` - Create new category

### Scraping
- `POST /api/v1/scraping/run` - Run scraping job (background)
- `POST /api/v1/scraping/run-sync` - Run scraping job (synchronous)
- `GET /api/v1/scraping/stats` - Get scraping statistics

## Next Steps

1. **Customize the scrapers** in `app/scrapers/dog_food_scraper.py`
2. **Add more API endpoints** in `app/api/v1/endpoints/`
3. **Extend the database models** in `app/models/`
4. **Add more tests** in `tests/`
5. **Configure production settings** when ready to deploy

## Support

If you encounter any issues:
1. Check the logs in the console
2. Verify your environment configuration
3. Make sure all prerequisites are installed
4. Check the troubleshooting section above
