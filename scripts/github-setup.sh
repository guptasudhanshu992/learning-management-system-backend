#!/bin/bash

# GitHub Repository Setup Script
# This script helps initialize and push your backend to GitHub

echo "📚 FastAPI Backend GitHub Setup"
echo "================================"

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi

# Get repository information
read -p "Enter your GitHub username: " GITHUB_USERNAME
read -p "Enter repository name (default: lms-backend): " REPO_NAME
REPO_NAME=${REPO_NAME:-lms-backend}

# Check if already in a git repository
if [ -d ".git" ]; then
    echo "📁 Git repository already exists"
    
    # Check if origin remote exists
    if git remote get-url origin &> /dev/null; then
        echo "🔗 Remote origin already configured:"
        git remote get-url origin
        read -p "Do you want to update it? (y/N): " update_remote
        if [[ $update_remote == [yY] ]]; then
            git remote set-url origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git
            echo "✅ Remote origin updated"
        fi
    else
        # Add remote origin
        git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git
        echo "✅ Remote origin added"
    fi
else
    # Initialize git repository
    echo "🔧 Initializing Git repository..."
    git init
    
    # Add remote origin
    git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git
    echo "✅ Git repository initialized and remote added"
fi

# Check if .env file exists and is not in .gitignore
if [ -f ".env" ] && ! grep -q "^\.env$" .gitignore; then
    echo "⚠️ Warning: .env file exists but may not be in .gitignore"
    echo "   Make sure .env is in .gitignore to avoid committing secrets!"
fi

# Add all files
echo "📦 Adding files to git..."
git add .

# Create commit
echo "💾 Creating commit..."
if git diff --staged --quiet; then
    echo "ℹ️ No changes to commit"
else
    read -p "Enter commit message (default: Initial commit - FastAPI LMS Backend): " COMMIT_MESSAGE
    COMMIT_MESSAGE=${COMMIT_MESSAGE:-"Initial commit - FastAPI LMS Backend"}
    git commit -m "$COMMIT_MESSAGE"
    echo "✅ Commit created"
fi

# Set main branch
git branch -M main

# Push to GitHub
echo "🚀 Pushing to GitHub..."
if git push -u origin main; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo ""
    echo "🌐 Your repository is now available at:"
    echo "   https://github.com/$GITHUB_USERNAME/$REPO_NAME"
    echo ""
    echo "📖 Next steps:"
    echo "   1. Visit your GitHub repository"
    echo "   2. Update README.md if needed"
    echo "   3. Set up deployment (see DEPLOYMENT.md)"
    echo "   4. Configure GitHub Secrets for CI/CD"
    echo ""
    echo "🚀 Ready to deploy? Check out these options:"
    echo "   • Railway: ./scripts/deploy-railway.sh"
    echo "   • Heroku: ./scripts/deploy-heroku.sh your-app-name"
    echo "   • DigitalOcean: ./scripts/deploy-digitalocean.sh"
else
    echo ""
    echo "❌ Failed to push to GitHub"
    echo "📋 Make sure you have:"
    echo "   1. Created the repository on GitHub"
    echo "   2. Have the correct permissions"
    echo "   3. Set up authentication (SSH keys or token)"
    echo ""
    echo "🔐 To set up authentication:"
    echo "   • GitHub CLI: gh auth login"
    echo "   • SSH: https://docs.github.com/en/authentication/connecting-to-github-with-ssh"
fi