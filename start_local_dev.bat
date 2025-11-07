@echo off
REM Local Development Startup Script for Windows

echo ========================================
echo   Dog Food API - Local Development
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ and try again
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo Creating .env file from template...
    copy env.example .env
    echo.
    echo IMPORTANT: Please edit the .env file with your PostgreSQL credentials
    echo before continuing. Press any key to open the file...
    pause
    notepad .env
)

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Check if PostgreSQL is running
echo Checking PostgreSQL connection...
python -c "import psycopg2; psycopg2.connect('postgresql://postgres:password@localhost:5432/dog_food_db')" >nul 2>&1
if errorlevel 1 (
    echo WARNING: Cannot connect to PostgreSQL
    echo Please make sure:
    echo 1. PostgreSQL is installed and running
    echo 2. Database 'dog_food_db' exists
    echo 3. Your credentials in .env are correct
    echo.
    echo You can create the database with:
    echo createdb -U postgres dog_food_db
    echo.
    echo Press any key to continue anyway...
    pause
)

REM Run database migrations
echo Running database migrations...
alembic upgrade head

REM Initialize with sample data
echo Initializing with sample data...
python scripts/init_db.py

REM Start the development server
echo.
echo Starting development server...
echo API will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python app/main_local.py
