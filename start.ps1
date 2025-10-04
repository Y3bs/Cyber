# Cyber Cafe Management System Startup Script
Write-Host "🚀 Starting Cyber Cafe Management System..." -ForegroundColor Green
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Creating template..." -ForegroundColor Yellow
    @"
# MongoDB Connection String
# Replace with your actual MongoDB connection string
DB_TOKEN=mongodb+srv://username:password@cluster.mongodb.net/

# Flask Secret Key
SECRET_KEY=cyber-cafe-secret-key-2024

# Flask Environment
FLASK_ENV=development
FLASK_DEBUG=True
"@ | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✅ .env file created. Please update with your MongoDB connection string." -ForegroundColor Green
    Write-Host ""
    Write-Host "📝 Edit the .env file and add your MongoDB connection string, then run this script again." -ForegroundColor Cyan
    Read-Host "Press Enter to exit"
    exit 0
}

# Install requirements if needed
Write-Host "📦 Checking dependencies..." -ForegroundColor Cyan
try {
    pip install -r requirements.txt --quiet
    Write-Host "✅ Dependencies are up to date" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Some dependencies might need manual installation" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🌐 Starting the application..." -ForegroundColor Green
Write-Host "📱 Open your browser to: http://localhost:5000" -ForegroundColor Cyan
Write-Host "🛑 Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the application
python app.py
