# Learning Management System Backend - GitHub Deployment Guide

This guide will help you deploy your FastAPI backend to GitHub and various cloud platforms.

## 📋 Prerequisites

- Git installed on your system
- GitHub account
- Python 3.9 or higher
- Virtual environment set up

## 🚀 Quick GitHub Setup

### 1. Initialize Git Repository

```bash
# Navigate to your backend directory
cd backend

# Initialize git repository (if not already done)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: FastAPI LMS backend"
```

### 2. Create GitHub Repository

1. Go to [GitHub](https://github.com) and create a new repository
2. Name it `lms-backend` (or your preferred name)
3. Don't initialize with README (we already have one)

### 3. Connect Local Repository to GitHub

```bash
# Add GitHub remote (replace with your username)
git remote add origin https://github.com/yourusername/lms-backend.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## 🔧 Environment Setup

### 1. Copy Environment Configuration

```bash
cp .env.example .env
```

### 2. Update Environment Variables

Edit `.env` file with your configuration:

```env
SECRET_KEY=your-super-secret-key-here-min-32-characters
DATABASE_URL=sqlite:///./app.db
STRIPE_SECRET_KEY=sk_test_your_stripe_key
RAZORPAY_KEY_ID=rzp_test_your_key
RAZORPAY_KEY_SECRET=your_razorpay_secret
```

## 🏗️ Deployment Options

### Option 1: Railway (Recommended for beginners)

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Run deployment script:**
   ```bash
   chmod +x scripts/deploy-railway.sh
   ./scripts/deploy-railway.sh
   ```

### Option 2: Heroku

1. **Install Heroku CLI** from [here](https://devcenter.heroku.com/articles/heroku-cli)

2. **Run deployment script:**
   ```bash
   chmod +x scripts/deploy-heroku.sh
   ./scripts/deploy-heroku.sh your-app-name
   ```

### Option 3: DigitalOcean App Platform

1. **Install doctl CLI** from [here](https://docs.digitalocean.com/reference/doctl/how-to/install/)

2. **Run deployment script:**
   ```bash
   chmod +x scripts/deploy-digitalocean.sh
   ./scripts/deploy-digitalocean.sh
   ```

### Option 4: Koyeb (recommended production)

1. **Create a Koyeb account** at https://www.koyeb.com and obtain an API token.

2. **Install Koyeb CLI (optional):**
```bash
# macOS / Linux
curl -L "https://github.com/koyeb/koyeb-cli/releases/latest/download/koyeb-cli_linux_amd64.tar.gz" | tar xz
sudo mv koyeb /usr/local/bin/
koyeb version
```

3. **Create and deploy via CLI (example):**
```bash
# Authenticate
koyeb config set token <YOUR_KOYEB_TOKEN>

# Create the service
koyeb services create api \
   --app lms-backend \
   --git "github.com/<your-username>/<your-repo>" \
   --git-branch main \
   --git-build-command "pip install -r requirements.txt" \
   --git-run-command "uvicorn main:app --host 0.0.0.0 --port 8000" \
   --ports 8000:http \
   --routes "/:8000" \
   --instance-type nano
```

## 🔐 GitHub Secrets Setup (for CI/CD)

If you want to use GitHub Actions for automated deployment, set these secrets in your GitHub repository:

### Required Secrets:
- `SECRET_KEY`: Your application secret key
- `KOYEB_TOKEN`: Koyeb API token (for automated deployments)
- `RAILWAY_TOKEN`: Railway API token (only if you use Railway)

### Optional Secrets:
- `STRIPE_SECRET_KEY`: Stripe secret key
- `RAZORPAY_KEY_ID`: Razorpay key ID
- `RAZORPAY_KEY_SECRET`: Razorpay secret key

To add secrets:
1. Go to your GitHub repository
2. Click Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add each secret

## 🧪 Testing Deployment

After deployment, test your API:

1. **Health Check:**
   ```bash
   curl https://your-app-url.com/health
   ```

2. **API Documentation:**
   Visit: `https://your-app-url.com/docs`

3. **Test Authentication:**
   ```bash
   curl -X POST "https://your-app-url.com/api/auth/register" \
        -H "Content-Type: application/json" \
        -d '{"email":"test@example.com","password":"testpass123","full_name":"Test User"}'
   ```

## 📊 Monitoring and Logs

### Railway
- Dashboard: https://railway.app/dashboard
- View logs in the Railway dashboard

### Heroku
- Dashboard: https://dashboard.heroku.com/apps
- View logs: `heroku logs --tail -a your-app-name`

### DigitalOcean
- Dashboard: https://cloud.digitalocean.com/apps
- View logs in the DigitalOcean dashboard

## 🔧 Troubleshooting

### Common Issues:

1. **Environment Variables Not Set:**
   - Make sure all required environment variables are set in your deployment platform
   - Check the `.env.example` file for required variables

2. **Database Connection Issues:**
   - For production, consider using PostgreSQL instead of SQLite
   - Update `DATABASE_URL` in your environment variables

3. **CORS Issues:**
   - Update `BACKEND_CORS_ORIGINS` in your environment variables
   - Include your frontend domain in the CORS origins

4. **Port Issues:**
   - Most platforms automatically set the PORT environment variable
   - The application is configured to use the provided PORT or default to 8000

### Getting Help:

1. Check the deployment platform's documentation
2. Review application logs for error messages
3. Ensure all dependencies are listed in `requirements.txt`
4. Verify environment variables are correctly set

## 🔄 Continuous Deployment

The repository includes GitHub Actions workflows that will:
- Run tests on every push
- Check code quality and security
- Deploy to Koyeb (when `KOYEB_TOKEN` is configured in repository secrets)

When you push to `main` and `KOYEB_TOKEN` is set, the `deploy-koyeb` job will build and deploy the service automatically.

## 📈 Next Steps

1. Set up database backups
2. Configure monitoring and alerting
3. Set up custom domain
4. Implement rate limiting for production
5. Set up SSL certificates (usually handled by the platform)
6. Consider using a managed database service for production