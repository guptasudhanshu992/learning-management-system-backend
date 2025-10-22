#!/bin/bash

# Heroku Deployment Script
# This script deploys the FastAPI backend to Heroku

echo "🚀 Deploying to Heroku..."

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI not found. Please install it first:"
    echo "Visit: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Check if logged in to Heroku
echo "🔐 Checking Heroku authentication..."
if ! heroku auth:whoami &> /dev/null; then
    echo "Please login to Heroku:"
    heroku login
fi

# Get app name
if [ -z "$1" ]; then
    read -p "Enter your Heroku app name: " APP_NAME
else
    APP_NAME=$1
fi

# Create Heroku app if it doesn't exist
echo "📦 Setting up Heroku app..."
if ! heroku apps:info $APP_NAME &> /dev/null; then
    echo "Creating new Heroku app: $APP_NAME"
    heroku create $APP_NAME
fi

# Add Heroku remote if not exists
if ! git remote get-url heroku &> /dev/null; then
    heroku git:remote -a $APP_NAME
fi

# Set environment variables
echo "⚙️ Setting environment variables..."
heroku config:set SECRET_KEY=$(openssl rand -base64 32) -a $APP_NAME
heroku config:set ALGORITHM=HS256 -a $APP_NAME
heroku config:set ACCESS_TOKEN_EXPIRE_MINUTES=30 -a $APP_NAME
heroku config:set PROJECT_NAME="Learning Management System API" -a $APP_NAME
heroku config:set VERSION=1.0.0 -a $APP_NAME
heroku config:set DEBUG=False -a $APP_NAME
heroku config:set ENVIRONMENT=production -a $APP_NAME

echo "💳 Please set your payment gateway keys:"
echo "heroku config:set STRIPE_SECRET_KEY=your-stripe-key -a $APP_NAME"
echo "heroku config:set RAZORPAY_KEY_ID=your-razorpay-id -a $APP_NAME"
echo "heroku config:set RAZORPAY_KEY_SECRET=your-razorpay-secret -a $APP_NAME"

read -p "Have you set payment gateway keys? (y/N): " confirm
if [[ $confirm != [yY] && $confirm != [yY][eE][sS] ]]; then
    echo "⚠️ Continuing without payment gateway configuration."
fi

# Create Procfile if not exists
if [ ! -f Procfile ]; then
    echo "📝 Creating Procfile..."
    echo "web: uvicorn main:app --host=0.0.0.0 --port=\${PORT:-8000}" > Procfile
fi

# Deploy to Heroku
echo "🚀 Deploying application..."
git add .
git commit -m "Deploy to Heroku" || echo "No changes to commit"
git push heroku main

echo "✅ Deployment completed!"
echo "🌐 Your API is available at: https://$APP_NAME.herokuapp.com"
echo "📖 API Documentation: https://$APP_NAME.herokuapp.com/docs"