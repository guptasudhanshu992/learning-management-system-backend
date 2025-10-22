#!/bin/bash

# Production Deployment Script for Price Action Repository
# Deploy the FastAPI backend to api.priceactionrepository.com

echo "🚀 Deploying to Production (api.priceactionrepository.com)..."

# Check if Koyeb CLI is installed
if ! command -v koyeb &> /dev/null; then
    echo "❌ Koyeb CLI not found. Installing..."
    curl -L "https://github.com/koyeb/koyeb-cli/releases/latest/download/koyeb-cli_linux_amd64.tar.gz" | tar xz
    sudo mv koyeb /usr/local/bin/
fi

# Check if logged in to Koyeb
echo "🔐 Checking Koyeb authentication..."
if ! koyeb config get token &> /dev/null; then
    echo "Please set your Koyeb token:"
    read -p "Enter your Koyeb API token: " KOYEB_TOKEN
    koyeb config set token $KOYEB_TOKEN
fi

# Deploy to production
echo "🚀 Deploying to api.priceactionrepository.com..."
koyeb services create api \
  --app lms-backend \
  --git "github.com/guptasudhanshu992/learning-management-system-backend" \
  --git-branch main \
  --git-build-command "pip install -r requirements.txt" \
  --git-run-command "uvicorn main:app --host 0.0.0.0 --port 8000" \
  --ports 8000:http \
  --routes "/:8000" \
  --env SECRET_KEY="$(openssl rand -base64 32)" \
  --env ALGORITHM=HS256 \
  --env ACCESS_TOKEN_EXPIRE_MINUTES=30 \
  --env PROJECT_NAME="Learning Management System API" \
  --env VERSION=1.0.0 \
  --env DEBUG=False \
  --env ENVIRONMENT=production \
  --env BACKEND_URL=https://api.priceactionrepository.com \
  --env 'CORS_ORIGINS=["https://priceactionrepository.com","https://www.priceactionrepository.com","https://app.priceactionrepository.com","https://dashboard.priceactionrepository.com"]' \
  --instance-type nano

echo "⚙️ Setting up custom domain..."
# Note: Domain setup might need to be done via Koyeb dashboard
echo "📝 Please configure the custom domain 'api.priceactionrepository.com' in your Koyeb dashboard:"
echo "   1. Go to your Koyeb dashboard"
echo "   2. Select your service"
echo "   3. Go to Settings > Domains"
echo "   4. Add custom domain: api.priceactionrepository.com"
echo "   5. Follow DNS setup instructions"

echo ""
echo "✅ Production deployment initiated!"
echo "🌐 Your API will be available at: https://api.priceactionrepository.com"
echo "📖 API Documentation: https://api.priceactionrepository.com/docs"
echo "🏥 Health Check: https://api.priceactionrepository.com/health"
echo ""
echo "⚠️ Remember to:"
echo "   1. Set up DNS records for api.priceactionrepository.com"
echo "   2. Configure payment gateway secrets in Koyeb dashboard"
echo "   3. Set up database backups"
echo "   4. Configure monitoring and alerts"