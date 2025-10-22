#!/bin/bash

# Koyeb Deployment Script
# This script deploys the FastAPI backend to Koyeb

echo "🚀 Deploying to Koyeb..."

# Check if Koyeb CLI is installed
if ! command -v koyeb &> /dev/null; then
    echo "❌ Koyeb CLI not found. Installing..."
    
    # Detect OS and install appropriate version
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    
    case $ARCH in
        x86_64) ARCH="amd64" ;;
        arm64|aarch64) ARCH="arm64" ;;
        *) echo "❌ Unsupported architecture: $ARCH" && exit 1 ;;
    esac
    
    # Download and install Koyeb CLI
    curl -L "https://github.com/koyeb/koyeb-cli/releases/latest/download/koyeb-cli_${OS}_${ARCH}.tar.gz" | tar xz
    sudo mv koyeb /usr/local/bin/
    
    echo "✅ Koyeb CLI installed"
fi

# Check if logged in to Koyeb
echo "🔐 Checking Koyeb authentication..."
if ! koyeb profile get &> /dev/null; then
    echo "Please login to Koyeb with your API token:"
    echo "Visit https://app.koyeb.com/account/api to get your token"
    read -p "Enter your Koyeb API token: " KOYEB_TOKEN
    koyeb config set token "$KOYEB_TOKEN"
fi

# Get app and service names
read -p "Enter your app name (default: lms-backend): " APP_NAME
APP_NAME=${APP_NAME:-lms-backend}

read -p "Enter your service name (default: api): " SERVICE_NAME  
SERVICE_NAME=${SERVICE_NAME:-api}

read -p "Enter your GitHub repository (username/repo-name): " GITHUB_REPO

if [ -z "$GITHUB_REPO" ]; then
    echo "❌ GitHub repository is required for Koyeb deployment"
    exit 1
fi

# Create Koyeb app if it doesn't exist
echo "📦 Setting up Koyeb app: $APP_NAME"
if ! koyeb apps get "$APP_NAME" &> /dev/null; then
    echo "Creating new Koyeb app: $APP_NAME"
    koyeb apps create "$APP_NAME"
fi

# Deploy service
echo "🚀 Deploying service: $SERVICE_NAME"
koyeb services create "$SERVICE_NAME" \
    --app "$APP_NAME" \
    --git "github.com/$GITHUB_REPO" \
    --git-branch main \
    --git-build-command "pip install -r requirements.txt" \
    --git-run-command "uvicorn main:app --host 0.0.0.0 --port 8000" \
    --ports 8000:http \
    --routes /:8000 \
    --env SECRET_KEY="$(openssl rand -base64 32)" \
    --env ALGORITHM=HS256 \
    --env ACCESS_TOKEN_EXPIRE_MINUTES=30 \
    --env PROJECT_NAME="Learning Management System API" \
    --env VERSION=1.0.0 \
    --env DEBUG=False \
    --env ENVIRONMENT=production \
    --instance-type nano

echo ""
echo "⚙️ Setting additional environment variables..."
echo "Please run these commands to set your payment gateway keys:"
echo ""
echo "koyeb services update $SERVICE_NAME --app $APP_NAME --env STRIPE_SECRET_KEY=your-stripe-key"
echo "koyeb services update $SERVICE_NAME --app $APP_NAME --env RAZORPAY_KEY_ID=your-razorpay-id"
echo "koyeb services update $SERVICE_NAME --app $APP_NAME --env RAZORPAY_KEY_SECRET=your-razorpay-secret"
echo ""

read -p "Have you noted down the commands above? (y/N): " confirm
if [[ $confirm != [yY] && $confirm != [yY][eE][sS] ]]; then
    echo "⚠️ Please set your payment gateway environment variables manually."
fi

echo "✅ Deployment initiated!"
echo ""
echo "📊 Check deployment status:"
echo "koyeb services get $SERVICE_NAME --app $APP_NAME"
echo ""
echo "🌐 Your API will be available at:"
echo "https://$APP_NAME-$SERVICE_NAME.koyeb.app"
echo ""
echo "📖 API Documentation:"
echo "https://$APP_NAME-$SERVICE_NAME.koyeb.app/docs"