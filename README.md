# Authentication & Authorization Microservice

A production-ready token-based authentication and authorization microservice built with FastAPI. This service implements attribute-based access control (ABAC) and provides persistent login capabilities through refresh tokens.

## Features

- 🔐 **Token-based Authentication**: JWT access tokens with refresh token mechanism
- 🔄 **Persistent Login**: Device-based persistent login using refresh tokens
- 🛡️ **Attribute-Based Authorization**: Fine-grained permission control based on attributes
- 🚀 **Production Ready**: Industry-standard structure, error handling, and security practices
- 📝 **OpenAPI Documentation**: Auto-generated API documentation
- 🔒 **Security**: Password hashing with Argon2 (OWASP recommended), secure token handling
- 🗄️ **MySQL Integration**: Uses existing MySQL database schema

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Service](#running-the-service)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Project Structure](#project-structure)
- [Security Considerations](#security-considerations)

## Prerequisites

Before you begin, ensure you have the following installed:

1. **Python 3.9+** - [Download Python](https://www.python.org/downloads/)
2. **MySQL 5.7+ or 8.0+** - [Download MySQL](https://dev.mysql.com/downloads/mysql/)
3. **pip** - Python package manager (usually comes with Python)
4. **Git** (optional) - For version control

### Verify Installation

```bash
# Check Python version
python --version  # Should be 3.9 or higher

# Check pip
pip --version

# Check MySQL
mysql --version
```

## Installation

### 1. Clone or Navigate to Project Directory

```bash
cd wecare
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file and update with your settings:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Edit `.env` file with your configuration (see [Configuration](#configuration) section).

## Configuration

The service uses environment variables for configuration. Key settings in `.env`:

### Database Configuration

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=wecare
DB_CHARSET=utf8mb4
```

### JWT Configuration

```env
# IMPORTANT: Generate a secure secret key for production
# Use: openssl rand -hex 32
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
```

### Security Settings

```env
# Argon2 password hashing parameters
ARGON2_TIME_COST=2
ARGON2_MEMORY_COST=65536
ARGON2_PARALLELISM=4
ALLOWED_ORIGINS=*
```

## Database Setup

### 1. Ensure MySQL is Running

```bash
# Check MySQL service status
# Windows
sc query MySQL80

# Linux/Mac
sudo systemctl status mysql
```

### 2. Verify Database and Tables

The service expects the following database structure:

**Database:** `wecare`

**Table: `user`**
```sql
CREATE TABLE IF NOT EXISTS `user` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(100) UNIQUE NOT NULL,
    `email` VARCHAR(255) UNIQUE NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `full_name` VARCHAR(255),
    `is_active` BOOLEAN DEFAULT TRUE,
    `is_superuser` BOOLEAN DEFAULT FALSE,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `last_login` DATETIME,
    `refresh_token` TEXT,
    `device_id` VARCHAR(255),
    INDEX `idx_username` (`username`),
    INDEX `idx_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Table: `user_resource_permission`**
```sql
CREATE TABLE IF NOT EXISTS `user_resource_permission` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `resource` VARCHAR(255) NOT NULL,
    `action` VARCHAR(100) NOT NULL,
    `attributes` TEXT,
    `is_active` BOOLEAN DEFAULT TRUE,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_resource` (`resource`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 3. Create Test User (Optional)

You can create a test user using the provided utility script:

```bash
python scripts/create_user.py
```

Or programmatically using the service's `get_password_hash()` function to generate Argon2 password hashes.

**Note:** Argon2 hashes are longer and more secure than bcrypt. Always use the provided hashing functions to generate password hashes.

## Running the Service

### Development Mode

```bash
# Activate virtual environment first
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Run with auto-reload
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or use the built-in runner:

```bash
python app/main.py
```

### Production Mode

```bash
# Using uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Or with gunicorn (install separately)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Verify Service is Running

Open your browser and navigate to:
- **API Documentation (Swagger UI):** http://localhost:8000/docs
- **Alternative Docs (ReDoc):** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

## API Endpoints

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication Endpoints

#### 1. Login
**POST** `/api/v1/auth/login`

Authenticate user and receive access/refresh tokens.

**Request Body:**
```json
{
    "username": "john_doe",
    "password": "securepassword123",
    "device_id": "device-uuid-12345"  // Optional
}
```

**Response:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800
}
```

**Status Codes:**
- `200 OK`: Login successful
- `401 Unauthorized`: Invalid credentials

---

#### 2. Refresh Token
**POST** `/api/v1/auth/refresh`

Get new access and refresh tokens using refresh token.

**Request Body:**
```json
{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "device_id": "device-uuid-12345"  // Optional
}
```

**Response:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800
}
```

**Status Codes:**
- `200 OK`: Tokens refreshed successfully
- `401 Unauthorized`: Invalid or expired refresh token

---

#### 3. Logout
**POST** `/api/v1/auth/logout`

Invalidate refresh token and logout user.

**Headers:**
```
Authorization: Bearer {access_token}
X-Device-ID: device-uuid-12345  // Optional
```

**Response:**
```json
{
    "message": "Successfully logged out"
}
```

**Status Codes:**
- `200 OK`: Logout successful
- `401 Unauthorized`: Invalid token

---

#### 4. Get Current User
**GET** `/api/v1/auth/me`

Get information about the currently authenticated user.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:**
```json
{
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00",
    "last_login": "2024-01-01T12:00:00"
}
```

**Status Codes:**
- `200 OK`: User information retrieved
- `401 Unauthorized`: Invalid token
- `403 Forbidden`: User inactive

---

#### 5. Verify Token
**GET** `/api/v1/auth/verify`

Verify if the current access token is valid.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:**
```json
{
    "valid": true,
    "user_id": 1,
    "username": "john_doe"
}
```

**Status Codes:**
- `200 OK`: Token is valid
- `401 Unauthorized`: Invalid token

---

### Permission Endpoints

#### 6. Check Permission
**POST** `/api/v1/permissions/check`

Check if user has permission to perform an action on a resource (Attribute-Based Access Control).

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
    "resource": "users",
    "action": "read",
    "attributes": {
        "department": "IT",
        "location": "US"
    }
}
```

**Response:**
```json
{
    "allowed": true,
    "resource": "users",
    "action": "read",
    "message": "Permission granted"
}
```

**Status Codes:**
- `200 OK`: Permission check completed
- `401 Unauthorized`: Invalid token
- `403 Forbidden`: Permission denied

---

#### 7. Get My Permissions
**GET** `/api/v1/permissions/my-permissions`

Get all permissions for the current user.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:**
```json
{
    "user_id": 1,
    "username": "john_doe",
    "is_superuser": false,
    "permissions": [
        {
            "resource": "users",
            "action": "read",
            "attributes": {
                "department": "IT"
            }
        },
        {
            "resource": "orders",
            "action": "write",
            "attributes": null
        }
    ]
}
```

**Status Codes:**
- `200 OK`: Permissions retrieved
- `401 Unauthorized`: Invalid token

---

## Usage Examples

### Example 1: Login Flow (Mobile/Web App)

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 1. Login
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "username": "john_doe",
        "password": "securepassword123",
        "device_id": "mobile-device-12345"
    }
)

tokens = login_response.json()
access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]

# 2. Use access token for authenticated requests
headers = {"Authorization": f"Bearer {access_token}"}
user_info = requests.get(f"{BASE_URL}/auth/me", headers=headers)
print(user_info.json())

# 3. Refresh token when access token expires
refresh_response = requests.post(
    f"{BASE_URL}/auth/refresh",
    json={
        "refresh_token": refresh_token,
        "device_id": "mobile-device-12345"
    }
)
new_tokens = refresh_response.json()
```

### Example 2: JavaScript/TypeScript (Web App)

```javascript
const BASE_URL = 'http://localhost:8000/api/v1';

// Login
async function login(username, password, deviceId) {
    const response = await fetch(`${BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username,
            password,
            device_id: deviceId
        })
    });
    
    if (response.ok) {
        const tokens = await response.json();
        // Store tokens securely
        localStorage.setItem('access_token', tokens.access_token);
        localStorage.setItem('refresh_token', tokens.refresh_token);
        return tokens;
    } else {
        throw new Error('Login failed');
    }
}

// Authenticated request
async function getCurrentUser() {
    const accessToken = localStorage.getItem('access_token');
    const response = await fetch(`${BASE_URL}/auth/me`, {
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    });
    
    if (response.status === 401) {
        // Token expired, refresh it
        await refreshToken();
        return getCurrentUser(); // Retry
    }
    
    return response.json();
}

// Refresh token
async function refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    const response = await fetch(`${BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            refresh_token: refreshToken
        })
    });
    
    if (response.ok) {
        const tokens = await response.json();
        localStorage.setItem('access_token', tokens.access_token);
        localStorage.setItem('refresh_token', tokens.refresh_token);
    } else {
        // Refresh failed, redirect to login
        window.location.href = '/login';
    }
}
```

### Example 3: Check Permission

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"
access_token = "your-access-token"

headers = {"Authorization": f"Bearer {access_token}"}

# Check if user can read users in IT department
permission_check = requests.post(
    f"{BASE_URL}/permissions/check",
    headers=headers,
    json={
        "resource": "users",
        "action": "read",
        "attributes": {
            "department": "IT"
        }
    }
)

result = permission_check.json()
if result["allowed"]:
    print("User has permission")
else:
    print("Permission denied")
```

## Project Structure

```
wecare/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   │
│   ├── api/                    # API layer
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py       # API router
│   │       ├── dependencies.py # API dependencies
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── auth.py     # Authentication endpoints
│   │           └── permissions.py # Permission endpoints
│   │
│   ├── core/                   # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration settings
│   │   ├── database.py        # Database connection
│   │   ├── security.py        # Security utilities (JWT, password hashing)
│   │   └── exceptions.py      # Custom exceptions
│   │
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py            # User model
│   │   └── user_resource_permission.py # Permission model
│   │
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── auth.py            # Authentication schemas
│   │   ├── user.py            # User schemas
│   │   └── permission.py      # Permission schemas
│   │
│   └── services/               # Business logic
│       ├── __init__.py
│       ├── auth_service.py    # Authentication service
│       └── permission_service.py # Permission service
│
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore file
└── README.md                  # This file
```

## Security Considerations

### Production Deployment Checklist

1. **Change Secret Key**: Generate a secure random secret key:
   ```bash
   openssl rand -hex 32
   ```

2. **Use HTTPS**: Always use HTTPS in production. Never send tokens over HTTP.

3. **Secure Token Storage**: 
   - **Mobile Apps**: Use secure storage (Keychain on iOS, Keystore on Android)
   - **Web Apps**: Use httpOnly cookies or secure localStorage with XSS protection

4. **CORS Configuration**: Restrict `ALLOWED_ORIGINS` to your actual domains:
   ```env
   ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
   ```

5. **Database Security**:
   - Use strong database passwords
   - Limit database user permissions
   - Use connection pooling
   - Enable SSL for database connections

6. **Environment Variables**: Never commit `.env` file to version control.

7. **Token Expiration**: Adjust token expiration times based on your security requirements.

8. **Rate Limiting**: Consider adding rate limiting to prevent brute force attacks.

9. **Logging**: Implement proper logging and monitoring for security events.

10. **Input Validation**: All inputs are validated using Pydantic schemas.

## Troubleshooting

### Database Connection Issues

```bash
# Test MySQL connection
mysql -h localhost -P 3306 -u root -p

# Verify database exists
SHOW DATABASES;
USE wecare;
SHOW TABLES;
```

### Port Already in Use

```bash
# Find process using port 8000
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000

# Kill process or change PORT in .env
```

### Import Errors

```bash
# Ensure virtual environment is activated
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## License

This project is provided as-is for use in the WeCare application.

## Support

For issues or questions, please contact the development team.

