# Database Configuration Guide

This guide explains how to set up and use the Learning Management System with different database configurations for development and production environments.

## Overview

The LMS backend supports two database configurations:
- **Development**: SQLite (local file database)
- **Production**: PostgreSQL (Neon or other PostgreSQL providers)

## Environment Setup

### Development Environment (SQLite)

1. **Copy the development environment file:**
   ```bash
   cp .env.development .env
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database:**
   ```bash
   python init_db.py --init
   ```

4. **Start the development server:**
   ```bash
   uvicorn main:app --reload
   ```

### Production Environment (Neon PostgreSQL)

#### Step 1: Set up Neon Database

1. **Create a Neon account** at [neon.tech](https://neon.tech)
2. **Create a new project** and database
3. **Copy the connection string** from your Neon dashboard

#### Step 2: Configure Environment

1. **Copy the production environment template:**
   ```bash
   cp .env.production .env
   ```

2. **Update the `.env` file** with your Neon database URL:
   ```bash
   # Replace with your actual Neon connection string
   DATABASE_URL=postgresql://username:password@host/database?sslmode=require
   
   # Or use individual components
   POSTGRES_HOST=your-host.neon.tech
   POSTGRES_USER=your-username
   POSTGRES_PASSWORD=your-password
   POSTGRES_DB=your-database
   ```

3. **Set other production variables:**
   ```bash
   ENVIRONMENT=production
   SECRET_KEY=your-secure-secret-key
   FRONTEND_URL=https://your-frontend-domain.com
   ```

#### Step 3: Deploy and Migrate

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

3. **Start the production server:**
   ```bash
   python deploy.py
   ```

## Database Management Commands

### Initialize Database
```bash
# Create all tables
python init_db.py --init
```

### Reset Database
```bash
# Drop and recreate all tables (WARNING: This deletes all data!)
python init_db.py --reset
```

### Migration Commands
```bash
# Generate a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback to previous migration
alembic downgrade -1

# Show current migration status
alembic current

# Show migration history
alembic history
```

## Environment Variables

### Required for All Environments
- `ENVIRONMENT`: Set to "development" or "production"
- `SECRET_KEY`: Secure secret key for JWT tokens
- `FRONTEND_URL`: URL of your frontend application

### Database Configuration
- `DATABASE_URL`: Complete database connection string (recommended)
- OR use individual components:
  - `POSTGRES_HOST`: Database host
  - `POSTGRES_USER`: Database username
  - `POSTGRES_PASSWORD`: Database password
  - `POSTGRES_DB`: Database name
  - `POSTGRES_PORT`: Database port (default: 5432)

### Optional Configuration
- `DEBUG`: Enable debug mode (development only)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `RATE_LIMIT_PER_SECOND`: API rate limiting
- `STRIPE_SECRET_KEY`: Stripe payment integration
- `RAZORPAY_KEY_ID` & `RAZORPAY_KEY_SECRET`: Razorpay payment integration

## Database Schema

The application uses SQLAlchemy ORM with the following main models:
- **User**: User accounts and authentication
- **Course**: Course information and content
- **Blog**: Blog posts and articles
- **Cart**: Shopping cart items
- **Wishlist**: User wishlist items
- **Payment**: Payment transactions

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Verify your database URL is correct
   - Check network connectivity to your database
   - Ensure your database server is running

2. **Migration Errors**
   - Check that your database user has sufficient privileges
   - Verify that the database exists
   - Review migration files for conflicts

3. **Environment Issues**
   - Ensure the `.env` file is in the correct location
   - Verify all required environment variables are set
   - Check for typos in variable names

### Database URL Formats

**SQLite (Development):**
```
sqlite:///./lms.db
```

**PostgreSQL (Production - Neon):**
```
postgresql://username:password@host/database?sslmode=require
```

**PostgreSQL (Local):**
```
postgresql://username:password@localhost:5432/database_name
```

## Performance Considerations

### Development (SQLite)
- Suitable for development and testing
- File-based, no network overhead
- Limited concurrent connections
- Automatic WAL mode for better concurrency

### Production (PostgreSQL)
- Designed for production workloads
- Full ACID compliance
- Excellent concurrent connection handling
- Connection pooling configured
- SSL connections for security

## Security Notes

1. **Never commit `.env` files** with real credentials to version control
2. **Use strong passwords** for production databases
3. **Enable SSL/TLS connections** in production
4. **Regularly update** your database credentials
5. **Use environment-specific secrets** for different environments

## Support

For database-related issues:
1. Check the application logs for error messages
2. Verify your environment configuration
3. Test database connectivity independently
4. Review the migration history for conflicts

For Neon-specific issues, consult the [Neon documentation](https://neon.tech/docs).