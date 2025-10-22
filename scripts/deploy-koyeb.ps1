# PowerShell Koyeb Deployment Script for Windows
# This script deploys the FastAPI backend to Koyeb

Write-Host "🚀 Deploying to Koyeb..." -ForegroundColor Green

# Check if Koyeb CLI is installed
try {
    koyeb --version | Out-Null
    Write-Host "✅ Koyeb CLI found" -ForegroundColor Green
} catch {
    Write-Host "❌ Koyeb CLI not found. Please install it manually:" -ForegroundColor Red
    Write-Host "Visit: https://www.koyeb.com/docs/cli/installation" -ForegroundColor Yellow
    Write-Host "Or download from: https://github.com/koyeb/koyeb-cli/releases" -ForegroundColor Yellow
    exit 1
}

# Check if logged in to Koyeb
Write-Host "🔐 Checking Koyeb authentication..." -ForegroundColor Yellow
try {
    koyeb profile get | Out-Null
    Write-Host "✅ Already authenticated with Koyeb" -ForegroundColor Green
} catch {
    Write-Host "Please login to Koyeb with your API token:" -ForegroundColor Yellow
    Write-Host "Visit https://app.koyeb.com/account/api to get your token" -ForegroundColor Cyan
    $KoyebToken = Read-Host "Enter your Koyeb API token"
    koyeb config set token $KoyebToken
}

# Get app and service names
$AppName = Read-Host "Enter your app name (press Enter for 'lms-backend')"
if ([string]::IsNullOrWhiteSpace($AppName)) { $AppName = "lms-backend" }

$ServiceName = Read-Host "Enter your service name (press Enter for 'api')"
if ([string]::IsNullOrWhiteSpace($ServiceName)) { $ServiceName = "api" }

$GitHubRepo = Read-Host "Enter your GitHub repository (username/repo-name)"
if ([string]::IsNullOrWhiteSpace($GitHubRepo)) {
    Write-Host "❌ GitHub repository is required for Koyeb deployment" -ForegroundColor Red
    exit 1
}

# Create Koyeb app if it doesn't exist
Write-Host "📦 Setting up Koyeb app: $AppName" -ForegroundColor Yellow
try {
    koyeb apps get $AppName | Out-Null
    Write-Host "✅ App already exists: $AppName" -ForegroundColor Green
} catch {
    Write-Host "Creating new Koyeb app: $AppName" -ForegroundColor Yellow
    koyeb apps create $AppName
}

# Generate secret key
$SecretKey = [System.Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))

# Deploy service
Write-Host "🚀 Deploying service: $ServiceName" -ForegroundColor Yellow
koyeb services create $ServiceName `
    --app $AppName `
    --git "github.com/$GitHubRepo" `
    --git-branch main `
    --git-build-command "pip install -r requirements.txt" `
    --git-run-command "uvicorn main:app --host 0.0.0.0 --port 8000" `
    --ports 8000:http `
    --routes "/:8000" `
    --env "SECRET_KEY=$SecretKey" `
    --env "ALGORITHM=HS256" `
    --env "ACCESS_TOKEN_EXPIRE_MINUTES=30" `
    --env "PROJECT_NAME=Learning Management System API" `
    --env "VERSION=1.0.0" `
    --env "DEBUG=False" `
    --env "ENVIRONMENT=production" `
    --instance-type nano

Write-Host ""
Write-Host "⚙️ Setting additional environment variables..." -ForegroundColor Yellow
Write-Host "Please run these commands to set your payment gateway keys:" -ForegroundColor Cyan
Write-Host ""
Write-Host "koyeb services update $ServiceName --app $AppName --env STRIPE_SECRET_KEY=your-stripe-key" -ForegroundColor White
Write-Host "koyeb services update $ServiceName --app $AppName --env RAZORPAY_KEY_ID=your-razorpay-id" -ForegroundColor White
Write-Host "koyeb services update $ServiceName --app $AppName --env RAZORPAY_KEY_SECRET=your-razorpay-secret" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "Have you noted down the commands above? (y/N)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "⚠️ Please set your payment gateway environment variables manually." -ForegroundColor Yellow
}

Write-Host "✅ Deployment initiated!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Check deployment status:" -ForegroundColor Cyan
Write-Host "koyeb services get $ServiceName --app $AppName" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Your API will be available at:" -ForegroundColor Cyan
Write-Host "https://$AppName-$ServiceName.koyeb.app" -ForegroundColor White
Write-Host ""
Write-Host "📖 API Documentation:" -ForegroundColor Cyan
Write-Host "https://$AppName-$ServiceName.koyeb.app/docs" -ForegroundColor White