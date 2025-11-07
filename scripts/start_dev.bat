@echo off
REM Development startup script for Windows

echo Starting Dog Food API in development mode...

REM Check if .env file exists
if not exist .env (
    echo Creating .env file from template...
    copy env.example .env
    echo Please edit .env file with your configuration before continuing.
    pause
    exit /b 1
)

REM Start services with docker-compose
echo Starting services with Docker Compose...
docker-compose up -d postgres redis

REM Wait for services to be ready
echo Waiting for services to be ready...
timeout /t 10 /nobreak > nul

REM Initialize database
echo Initializing database...
docker-compose exec -T postgres psql -U postgres -d dog_food_db -c "SELECT 1;" > nul 2>&1
if errorlevel 1 (
    echo Creating database...
    docker-compose exec -T postgres createdb -U postgres dog_food_db
)

REM Run migrations
echo Running database migrations...
alembic upgrade head

REM Initialize with sample data
echo Initializing with sample data...
python scripts/init_db.py

REM Start the API
echo Starting FastAPI application...
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
