#!/bin/bash

# Setup Development Environment
# This script sets up a local development environment

echo "🔧 Setting up development environment..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then 
    echo "✅ Python $python_version is compatible"
else
    echo "❌ Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Install development dependencies
echo "🛠️ Installing development dependencies..."
pip install pytest pytest-cov black flake8 isort bandit safety

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️ Please update .env file with your configuration"
else
    echo "✅ .env file already exists"
fi

# Initialize database
echo "🗄️ Initializing database..."
if [ ! -f "app.db" ]; then
    python -c "
from app.db.database import engine
from app.db import models
models.Base.metadata.create_all(bind=engine)
print('Database initialized successfully!')
"
else
    echo "✅ Database already exists"
fi

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "🚀 To start the development server:"
echo "   source venv/bin/activate  # (if not already activated)"
echo "   uvicorn main:app --reload"
echo ""
echo "📖 API Documentation will be available at:"
echo "   http://localhost:8000/docs"
echo ""
echo "🧪 To run tests:"
echo "   pytest"