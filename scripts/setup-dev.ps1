# PowerShell Setup Script for Windows
# This script sets up a local development environment on Windows

Write-Host "🔧 Setting up development environment..." -ForegroundColor Green

# Check Python version
try {
    $pythonVersion = (python --version 2>&1).Split(' ')[1]
    $requiredVersion = [Version]"3.9.0"
    $currentVersion = [Version]$pythonVersion
    
    if ($currentVersion -ge $requiredVersion) {
        Write-Host "✅ Python $pythonVersion is compatible" -ForegroundColor Green
    } else {
        Write-Host "❌ Python 3.9 or higher is required. Found: $pythonVersion" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Python not found. Please install Python 3.9 or higher" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
if (!(Test-Path "venv")) {
    python -m venv venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "🔌 Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "⬆️ Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "📚 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Install development dependencies
Write-Host "🛠️ Installing development dependencies..." -ForegroundColor Yellow
pip install pytest pytest-cov black flake8 isort bandit safety

# Create .env file if it doesn't exist
if (!(Test-Path ".env")) {
    Write-Host "📝 Creating .env file..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "⚠️ Please update .env file with your configuration" -ForegroundColor Yellow
} else {
    Write-Host "✅ .env file already exists" -ForegroundColor Green
}

# Initialize database
Write-Host "🗄️ Initializing database..." -ForegroundColor Yellow
if (!(Test-Path "app.db")) {
    python -c @"
from app.db.database import engine
from app.db import models
models.Base.metadata.create_all(bind=engine)
print('Database initialized successfully!')
"@
} else {
    Write-Host "✅ Database already exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "✅ Development environment setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 To start the development server:" -ForegroundColor Cyan
Write-Host "   venv\Scripts\Activate.ps1  # (if not already activated)"
Write-Host "   uvicorn main:app --reload"
Write-Host ""
Write-Host "📖 API Documentation will be available at:" -ForegroundColor Cyan
Write-Host "   http://localhost:8000/docs"
Write-Host ""
Write-Host "🧪 To run tests:" -ForegroundColor Cyan
Write-Host "   pytest"