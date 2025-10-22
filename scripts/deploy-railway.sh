#!/bin/bash

# Railway Deployment Script
# This script deploys the FastAPI backend to Railway

echo "🚀 Deploying to Railway..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Check if logged in to Railway
echo "🔐 Checking Railway authentication..."
if ! railway whoami &> /dev/null; then
    echo "Please login to Railway:"
    railway login
fi

# Create project if not exists
echo "📦 Setting up Railway project..."
if [ ! -f railway.json ]; then
    railway init
fi

# Set environment variables
echo "⚙️ Setting environment variables..."
echo "Please set your environment variables:"
echo "railway variables set SECRET_KEY=your-secret-key-here"
echo "railway variables set DATABASE_URL=your-database-url-here"
echo "railway variables set STRIPE_SECRET_KEY=your-stripe-key"
echo "railway variables set RAZORPAY_KEY_ID=your-razorpay-id"
echo "railway variables set RAZORPAY_KEY_SECRET=your-razorpay-secret"

read -p "Have you set all required environment variables? (y/N): " confirm
if [[ $confirm != [yY] && $confirm != [yY][eE][sS] ]]; then
    echo "❌ Please set environment variables before deploying."
    exit 1
fi

# Deploy to Railway
echo "🚀 Deploying application..."
railway up

echo "✅ Deployment completed!"
echo "🌐 Your API should be available at your Railway domain"
echo "📖 Check Railway dashboard for deployment status: https://railway.app/dashboard"