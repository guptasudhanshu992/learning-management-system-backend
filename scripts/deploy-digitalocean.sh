#!/bin/bash

# DigitalOcean App Platform Deployment Script
# This script deploys the FastAPI backend to DigitalOcean App Platform

echo "🚀 Deploying to DigitalOcean App Platform..."

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
    echo "❌ doctl CLI not found. Please install it first:"
    echo "Visit: https://docs.digitalocean.com/reference/doctl/how-to/install/"
    exit 1
fi

# Check if authenticated with DigitalOcean
echo "🔐 Checking DigitalOcean authentication..."
if ! doctl account get &> /dev/null; then
    echo "Please authenticate with DigitalOcean:"
    doctl auth init
fi

# Update app.yaml with correct repository
read -p "Enter your GitHub username: " GITHUB_USERNAME
read -p "Enter your repository name (default: lms-backend): " REPO_NAME
REPO_NAME=${REPO_NAME:-lms-backend}

# Update app.yaml
sed -i "s/yourusername/$GITHUB_USERNAME/g" app.yaml
sed -i "s/lms-backend/$REPO_NAME/g" app.yaml

echo "📝 Updated app.yaml with your repository information"

# Create the app
echo "🚀 Creating DigitalOcean App..."
doctl apps create --spec app.yaml

echo "✅ App creation initiated!"
echo "📖 Check your DigitalOcean dashboard to complete the setup:"
echo "   1. Connect your GitHub repository"
echo "   2. Set environment variables (SECRET_KEY, payment keys)"
echo "   3. Deploy the app"
echo ""
echo "🌐 Visit: https://cloud.digitalocean.com/apps"

# List apps to show the created app
echo "📋 Your apps:"
doctl apps list