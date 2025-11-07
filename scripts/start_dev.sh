#!/bin/bash
# Development startup script

echo "Starting Dog Food API in development mode..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp env.example .env
    echo "Please edit .env file with your configuration before continuing."
    exit 1
fi

# Start services with docker-compose
echo "Starting services with Docker Compose..."
docker-compose up -d postgres redis

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Initialize database
echo "Initializing database..."
docker-compose exec -T postgres psql -U postgres -d dog_food_db -c "SELECT 1;" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Creating database..."
    docker-compose exec -T postgres createdb -U postgres dog_food_db
fi

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Initialize with sample data
echo "Initializing with sample data..."
python scripts/init_db.py

# Start the API
echo "Starting FastAPI application..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
