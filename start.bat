@echo off
echo 🚀 Starting Cyber Cafe Management System...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python first.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️  .env file not found. Creating template...
    (
        echo # MongoDB Connection String
        echo # Replace with your actual MongoDB connection string
        echo DB_TOKEN=mongodb+srv://username:password@cluster.mongodb.net/
        echo.
        echo # Flask Secret Key
        echo SECRET_KEY=cyber-cafe-secret-key-2024
        echo.
        echo # Flask Environment
        echo FLASK_ENV=development
        echo FLASK_DEBUG=True
    ) > .env
    echo ✅ .env file created. Please update with your MongoDB connection string.
    echo.
    echo 📝 Edit the .env file and add your MongoDB connection string, then run this script again.
    pause
    exit /b 0
)

echo 📦 Installing dependencies...
pip install -r requirements.txt --quiet

echo.
echo 🌐 Starting the application...
echo 📱 Open your browser to: http://localhost:5000
echo 🛑 Press Ctrl+C to stop the server
echo.

python app.py
