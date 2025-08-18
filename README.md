# Wealth Investment API - Backend

A modern, fast, and secure backend API for a wealth investment platform built with FastAPI, MongoDB, and JWT authentication.

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [File Structure](#file-structure)
- [Key Components](#key-components)
- [Technology Stack](#technology-stack)
- [API Endpoints](#api-endpoints)
- [Environment Configuration](#environment-configuration)
- [Getting Started](#getting-started)
- [Database Schema](#database-schema)
- [Security Features](#security-features)
- [Development Notes](#development-notes)

## 🎯 Project Overview

The Wealth Investment API backend is a comprehensive investment management system that provides:

- **User Authentication & Authorization** with JWT tokens
- **Investment Package Management** with CRUD operations
- **Investment Tracking** and portfolio management
- **Transaction Management** for deposits, withdrawals, and ROI
- **Cryptocurrency Price Integration** via external APIs
- **Admin Panel** for user and package management

## 📁 File Structure

```
backend/
├── main.py              # Main FastAPI application with all endpoints
├── models.py            # Database models (User, Package, Investment, Transaction)
├── database.py          # MongoDB connection and configuration
├── start.py             # Application startup script
├── manage.py            # Admin management utilities
├── requirements.txt     # Python dependencies
├── .env                 # Environment configuration
└── __pycache__/         # Python cache files
```

## 🔧 Key Components

### 1. **Main Application (`main.py`)**
- **FastAPI app** with CORS middleware
- **JWT authentication** system with OAuth2 password bearer
- **Complete REST API** with comprehensive endpoints
- **Pydantic models** for request/response validation
- **Error handling** and HTTP status codes

### 2. **Database Models (`models.py`)**
- **User**: Authentication and profile data with email/username uniqueness
- **Package**: Investment package definitions with min/max investment limits
- **Investment**: User investment records with status tracking
- **Transaction**: Financial transaction tracking with type classification
- **Enums**: Status and type definitions for consistency

### 3. **Database Configuration (`database.py`)**
- **MongoDB** connection with Motor (async driver)
- **Beanie ODM** for document modeling and validation
- **Connection retry logic** with multiple fallback strategies
- **Environment-based configuration** for different deployment scenarios
- **Connection pooling** and timeout management

### 4. **Management Tools**
- **`start.py`**: Development server startup with hot reload
- **`manage.py`**: Admin user promotion utility with command-line interface

## 🛠 Technology Stack

### Core Framework
- **FastAPI** (v0.104.1) - Modern, fast web framework with automatic API documentation
- **Uvicorn** (v0.24.0) - Lightning-fast ASGI server

### Database
- **MongoDB** - NoSQL document database for flexible data storage
- **Motor** (v3.3.2) - Async MongoDB driver for high-performance operations
- **Beanie** (v1.23.6) - ODM for MongoDB with Pydantic integration

### Authentication & Security
- **Python-Jose** (v3.3.0) - JWT token creation and validation
- **Passlib** (v1.7.4) - Password hashing with bcrypt algorithm

### Data Validation & Processing
- **Pydantic** (v2.5.0) - Data validation and serialization
- **Python-multipart** (v0.0.6) - Form data handling for file uploads

### Utilities
- **Requests** (v2.31.0) - HTTP client for external API calls
- **Python-dotenv** (v1.0.0) - Environment variable management

## 🔌 API Endpoints

### Authentication
- `POST /register` - User registration with email validation
- `POST /token` - User login and JWT token generation
- `GET /users/me` - Get current authenticated user profile

### User Management
- `GET /users` - List all users (admin only)
- `PUT /users/{user_id}` - Update user profile information
- `PUT /admin/users/{user_id}` - Admin user management (activate/deactivate)

### Investment Packages
- `GET /packages` - List all active investment packages
- `POST /packages` - Create new investment package (admin only)
- `PUT /packages/{package_id}` - Update package details (admin only)
- `DELETE /packages/{package_id}` - Delete package (admin only)

### Investments
- `GET /investments` - List user's investment portfolio
- `POST /investments` - Create new investment in a package
- `GET /investments/{investment_id}` - Get specific investment details

### Transactions
- `GET /transactions` - List user's transaction history
- `POST /transactions` - Create new transaction (deposit/withdrawal)
- `PUT /transactions/{transaction_id}` - Update transaction status

### Crypto Integration
- `GET /crypto/prices` - Get current cryptocurrency prices
- `GET /crypto/price/{symbol}` - Get specific cryptocurrency price

## ⚙️ Environment Configuration

The `.env` file contains all necessary configuration:

```env
# Database Configuration - MongoDB
MONGODB_URL=mongodb://username:password@cluster.mongodb.net/database
DATABASE_NAME=wealthinvest

# JWT Configuration
SECRET_KEY=your-super-secret-jwt-key-change-this-immediately
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=2880

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Environment
ENVIRONMENT=development

# API Keys for Crypto Prices
COINAPI_KEY=your-coinapi-key-here
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- MongoDB instance (local or MongoDB Atlas)
- Git for version control

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd project/backend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Setup**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit .env with your configuration
   nano .env
   ```

4. **Database Setup**
   - Ensure MongoDB is running
   - Update `MONGODB_URL` in `.env` file
   - The application will automatically create collections

### Running the Application

#### Development Mode
```bash
# Using the startup script
python start.py

# Or directly with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Production Mode
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Admin Management

```bash
# Promote a user to admin role
python manage.py user@example.com
```

### API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🗄️ Database Schema

### Users Collection
```json
{
  "_id": "ObjectId",
  "email": "user@example.com",        // Unique, indexed
  "username": "johndoe",              // Unique, indexed
  "first_name": "John",
  "last_name": "Doe",
  "hashed_password": "bcrypt_hash",
  "is_active": true,
  "is_admin": false,
  "subscription_plan": "Basic",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Packages Collection
```json
{
  "_id": "ObjectId",
  "name": "Basic Plan",               // Indexed
  "description": "A basic investment package",
  "min_investment": 100.0,
  "max_investment": 1000.0,
  "duration_days": 30,
  "roi_percentage": 5.0,
  "is_active": true                   // Indexed
}
```

### Investments Collection
```json
{
  "_id": "ObjectId",
  "amount": 500.0,
  "package_id": "package_object_id",  // Indexed
  "user_id": "user_object_id",        // Indexed
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-02-01T00:00:00Z",
  "status": "active"                  // Indexed
}
```

### Transactions Collection
```json
{
  "_id": "ObjectId",
  "user_id": "user_object_id",        // Indexed
  "type": "deposit",                  // deposit, withdrawal, investment, roi
  "amount": 100.0,
  "status": "completed",              // pending, completed, failed
  "description": "Initial deposit",
  "created_at": "2024-01-01T00:00:00Z"
}
```

## 🔒 Security Features

- **JWT-based authentication** with configurable expiration
- **Password hashing** using bcrypt with salt rounds
- **CORS protection** with configurable allowed origins
- **Input validation** with Pydantic models
- **Admin role management** for privileged operations
- **Environment variable** protection for sensitive data
- **Database connection** with SSL/TLS support

## 💡 Development Notes

### Architecture Patterns
- **Async/await** throughout the codebase for non-blocking operations
- **Dependency injection** for authentication and database access
- **Repository pattern** with Beanie ODM
- **Modular design** with separate concerns

### Error Handling
- **Comprehensive exception handling** with proper HTTP status codes
- **Database connection retry logic** with multiple fallback strategies
- **Input validation** with detailed error messages
- **Graceful degradation** for external service failures

### Performance Optimizations
- **Database indexing** on frequently queried fields
- **Connection pooling** for MongoDB operations
- **Async operations** for I/O-bound tasks
- **Caching strategies** for external API calls

### Code Quality
- **Type hints** throughout the codebase
- **Pydantic models** for data validation
- **Comprehensive documentation** with docstrings
- **Environment-based configuration** for different deployment scenarios

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the error logs for debugging information

---

**Built with ❤️ using FastAPI and MongoDB**
