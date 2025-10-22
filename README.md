# Learning Management System API

A comprehensive backend API for a Learning Management System built with **FastAPI**, featuring course management, user authentication, e-commerce functionality, and payment processing.

[![CI/CD Pipeline](https://github.com/guptasudhanshu992/learning-management-system-backend/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/guptasudhanshu992/learning-management-system-backend/actions/workflows/ci-cd.yml)
[![Production API](https://img.shields.io/badge/Production-api.priceactionrepository.com-green.svg)](https://api.priceactionrepository.com)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Features

- **Authentication & Authorization**: JWT-based authentication with role-based access control
- **Course Management**: Comprehensive course, chapter, and lesson management
- **E-commerce**: Shopping cart, wishlist, and course purchases
- **Payment Integration**: Stripe and Razorpay payment processing
- **Blog System**: Blog posts with comments and tagging
- **User Management**: Admin dashboard for user management
- **Security**: Rate limiting, CSRF protection, and input validation
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Database**: SQLAlchemy with SQLite (easily adaptable to PostgreSQL/MySQL)
- **Authentication**: JWT tokens with python-jose
- **Password Hashing**: bcrypt
- **Payment Processing**: Stripe & Razorpay
- **Validation**: Pydantic
- **Testing**: pytest
-- **Containerization**: (removed) Use Koyeb as primary deployment platform
- **CI/CD**: GitHub Actions

## 📋 Requirements

- Python 3.9+
- FastAPI
- SQLAlchemy
- All dependencies listed in `requirements.txt`

## 🔧 Quick Start

### Local Development

1. **Clone the repository:**
```bash
git clone https://github.com/guptasudhanshu992/learning-management-system-backend.git
cd learning-management-system-backend
```

2. **Create and activate virtual environment:**
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
# At minimum, set:
# - SECRET_KEY (generate a secure random string)
# - DATABASE_URL (optional, defaults to SQLite)
```

5. **Initialize the database:**
```bash
# The database will be created automatically on first run
# Optionally, you can use Alembic for migrations
alembic upgrade head
```

6. **Start the development server:**
```bash
uvicorn main:app --reload --port 8000
```

7. **Access the API:**
- **Local Development:**
  - API Documentation: http://localhost:8000/docs
  - Alternative docs: http://localhost:8000/redoc
  - Health check: http://localhost:8000/health
- **Production API:**
  - API Documentation: https://api.priceactionrepository.com/docs
  - Alternative docs: https://api.priceactionrepository.com/redoc
  - Health check: https://api.priceactionrepository.com/health

## ☁️ Koyeb Deployment (primary)

Koyeb is the recommended platform for deploying this backend. The project includes a GitHub Actions job to deploy to Koyeb automatically when code is pushed to `main`.

### Manual Koyeb deployment (quick)

1. Create an account at https://www.koyeb.com and obtain an API token.

2. Install the Koyeb CLI (optional but useful):
```bash
# macOS / Linux
curl -L "https://github.com/koyeb/koyeb-cli/releases/latest/download/koyeb-cli_linux_amd64.tar.gz" | tar xz
sudo mv koyeb /usr/local/bin/
koyeb version
```

3. Create a new app/service using the Koyeb dashboard or CLI. Example CLI flow:
```bash
# Authenticate
koyeb config set token <YOUR_KOYEB_TOKEN>

# Create the service (example using git build)
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

4. Add environment variables in the Koyeb dashboard or via the CLI (recommended):
```bash
koyeb services env set api SECRET_KEY="<your-secret-key>" --app lms-backend
koyeb services env set api DATABASE_URL="<your-db-url>" --app lms-backend
# and any other required keys (STRIPE, RAZORPAY, etc.)
```

5. Your service will be available on the Koyeb-provided domain. Use `/health` to verify.

## ☁️ Cloud Deployment

### Deploy to Railway

1. **Install Railway CLI:**
```bash
npm install -g @railway/cli
```

2. **Login and deploy:**
```bash
railway login
railway init
railway up
```

3. **Set environment variables:**
```bash
railway variables set SECRET_KEY=your-secret-key
railway variables set DATABASE_URL=your-database-url
# Add other required variables
```

### Deploy to Heroku

1. **Create Heroku app:**
```bash
heroku create your-app-name
```

2. **Set environment variables:**
```bash
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DATABASE_URL=your-database-url
```

3. **Deploy:**
```bash
git push heroku main
```

### Deploy to DigitalOcean App Platform

1. **Create `app.yaml`:**
```yaml
name: lms-backend
services:
- name: api
  source_dir: /
  github:
    repo: your-username/lms-backend
    branch: main
  run_command: uvicorn main:app --host 0.0.0.0 --port 8080
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: SECRET_KEY
    value: your-secret-key
```

2. **Deploy using doctl:**
```bash
doctl apps create --spec app.yaml
```

## 🔧 Environment Variables

Create a `.env` file based on `.env.example`:

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | JWT signing key | Yes |
| `DATABASE_URL` | Database connection string | No (defaults to SQLite) |
| `ALGORITHM` | JWT algorithm | No (defaults to HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | No (defaults to 30) |
| `STRIPE_SECRET_KEY` | Stripe secret key | Only for payments |
| `RAZORPAY_KEY_ID` | Razorpay key ID | Only for payments |
| `RAZORPAY_KEY_SECRET` | Razorpay secret | Only for payments |
| `BACKEND_CORS_ORIGINS` | Allowed CORS origins | No |

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

### Test Coverage
The project includes comprehensive test coverage for:
- Authentication endpoints
- CRUD operations
- Payment processing
- Input validation
- Security measures

## API Endpoints

### Authentication
- `POST /api/auth/register`: Register a new user
- `POST /api/auth/login`: Login and get access token
- `POST /api/auth/refresh-token`: Refresh access token
- `POST /api/auth/password-reset`: Request password reset
- `POST /api/auth/password-reset/confirm`: Reset password with token

### Users
- `GET /api/users/me`: Get current user
- `PUT /api/users/me`: Update current user
- `PUT /api/users/me/password`: Update current user password
- `GET /api/users`: Get all users (admin only)
- `POST /api/users`: Create new user (admin only)
- `GET /api/users/{user_id}`: Get user by ID (admin only)
- `PUT /api/users/{user_id}`: Update user (admin only)
- `DELETE /api/users/{user_id}`: Delete user (admin only)

### Courses
- `GET /api/courses`: Get all published courses with filters
- `POST /api/courses`: Create new course (instructor or admin only)
- `GET /api/courses/{course_id}`: Get course by ID
- `PUT /api/courses/{course_id}`: Update course (instructor or admin only)
- `DELETE /api/courses/{course_id}`: Delete course (instructor or admin only)
- `GET /api/courses/{course_id}/chapters`: Get all chapters for a course
- `POST /api/courses/{course_id}/chapters`: Create new chapter (instructor or admin only)
- `PUT /api/courses/{course_id}/chapters/{chapter_id}`: Update chapter (instructor or admin only)
- `DELETE /api/courses/{course_id}/chapters/{chapter_id}`: Delete chapter (instructor or admin only)
- `GET /api/courses/{course_id}/chapters/{chapter_id}/lessons`: Get all lessons for a chapter
- `POST /api/courses/{course_id}/chapters/{chapter_id}/lessons`: Create new lesson (instructor or admin only)
- `GET /api/courses/categories`: Get all categories
- `POST /api/courses/categories`: Create new category (admin only)
- `GET /api/courses/{course_id}/reviews`: Get all reviews for a course
- `POST /api/courses/{course_id}/reviews`: Create new review (authenticated user)

### Blogs
- `GET /api/blogs`: Get all published blog posts
- `POST /api/blogs`: Create new blog post (instructor or admin only)
- `GET /api/blogs/{post_id}`: Get blog post by ID
- `PUT /api/blogs/{post_id}`: Update blog post (author or admin only)
- `DELETE /api/blogs/{post_id}`: Delete blog post (author or admin only)
- `GET /api/blogs/{post_id}/comments`: Get all comments for a blog post
- `POST /api/blogs/{post_id}/comments`: Create new comment (authenticated user)

### Cart
- `GET /api/cart`: Get current user's cart
- `POST /api/cart`: Add item to cart
- `DELETE /api/cart/{item_id}`: Remove item from cart

### Wishlist
- `GET /api/wishlist`: Get current user's wishlist
- `POST /api/wishlist`: Add item to wishlist
- `DELETE /api/wishlist/{course_id}`: Remove item from wishlist

### Payment
- `POST /api/payment/stripe/create-intent`: Create payment intent with Stripe
- `POST /api/payment/stripe/verify`: Verify Stripe payment
- `POST /api/payment/razorpay/create-order`: Create order with Razorpay
- `POST /api/payment/razorpay/verify`: Verify Razorpay payment

## Database

The application uses SQLite by default. The database file will be created at `./lms.db` when you first run the application.

## Development

### Creating Database Migrations

We use Alembic for database migrations. To create a new migration:

```
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

### Running Tests

```
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.