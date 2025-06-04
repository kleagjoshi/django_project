# JWT Authentication Implementation

This document explains how to use the JWT authentication system implemented in the Course Management System.

## Overview

The system now includes JWT (JSON Web Token) authentication with the following features:
- User registration
- User login
- Token refresh
- User logout (token blacklisting)
- User profile management
- Secure API endpoints

## API Endpoints

### Authentication Endpoints

#### 1. Register a New User
**POST** `/api/auth/register/`

**Request Body:**
```json
{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepassword123",
    "password_confirm": "securepassword123",
    "person_id": "12345678",
    "name": "John",
    "surname": "Doe",
    "father_name": "Robert",
    "birthday": "1990-01-01",
    "birth_place": "New York",
    "gender": "M"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "johndoe",
        "email": "john@example.com",
        "person_id": "12345678",
        "name": "John",
        "surname": "Doe",
        "father_name": "Robert",
        "birthday": "1990-01-01",
        "birth_place": "New York",
        "gender": "M",
        "is_enabled": true,
        "date_joined": "2023-12-01T10:00:00Z",
        "last_login": null
    }
}
```

#### 2. Login
**POST** `/api/auth/login/`

**Request Body:**
```json
{
    "username": "johndoe",
    "password": "securepassword123"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "johndoe",
        "email": "john@example.com",
        "person_id": "12345678",
        "name": "John",
        "surname": "Doe",
        "is_enabled": true
    }
}
```

#### 3. Refresh Token
**POST** `/api/auth/refresh/`

**Request Body:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### 4. Logout
**POST** `/api/auth/logout/`

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
    "message": "Successfully logged out"
}
```

#### 5. Get User Profile
**GET** `/api/auth/profile/`

**Headers:** `Authorization: Bearer <access_token>`

**Response:**
```json
{
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "person_id": "12345678",
    "name": "John",
    "surname": "Doe",
    "father_name": "Robert",
    "birthday": "1990-01-01",
    "birth_place": "New York",
    "gender": "M",
    "is_enabled": true,
    "date_joined": "2023-12-01T10:00:00Z",
    "last_login": "2023-12-01T10:30:00Z"
}
```

#### 6. Update User Profile
**PUT** `/api/auth/profile/`

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
    "email": "newemail@example.com",
    "name": "John Updated",
    "surname": "Doe Updated"
}
```

## How to Use JWT Authentication

### 1. Frontend Implementation

#### JavaScript/React Example:
```javascript
// Login function
async function login(username, password) {
    const response = await fetch('/api/auth/login/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password })
    });
    
    const data = await response.json();
    
    if (response.ok) {
        // Store tokens
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        localStorage.setItem('user', JSON.stringify(data.user));
        return data;
    }
    throw new Error(data.error || 'Login failed');
}

// Make authenticated requests
async function makeAuthenticatedRequest(url, options = {}) {
    const token = localStorage.getItem('access_token');
    
    const config = {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            ...options.headers
        }
    };
    
    let response = await fetch(url, config);
    
    // If token expired, try to refresh
    if (response.status === 401) {
        const refreshed = await refreshToken();
        if (refreshed) {
            config.headers.Authorization = `Bearer ${localStorage.getItem('access_token')}`;
            response = await fetch(url, config);
        }
    }
    
    return response;
}

// Refresh token function
async function refreshToken() {
    const refresh = localStorage.getItem('refresh_token');
    if (!refresh) return false;
    
    try {
        const response = await fetch('/api/auth/refresh/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh })
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access);
            return true;
        }
    } catch (error) {
        console.error('Token refresh failed:', error);
    }
    
    // Refresh failed, redirect to login
    logout();
    return false;
}

// Logout function
async function logout() {
    const refresh = localStorage.getItem('refresh_token');
    if (refresh) {
        try {
            await makeAuthenticatedRequest('/api/auth/logout/', {
                method: 'POST',
                body: JSON.stringify({ refresh })
            });
        } catch (error) {
            console.error('Logout request failed:', error);
        }
    }
    
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    window.location.href = '/login';
}
```

### 2. Python/Requests Example:
```python
import requests

class APIClient:
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
    
    def login(self, username, password):
        response = requests.post(f'{self.base_url}/api/auth/login/', json={
            'username': username,
            'password': password
        })
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access']
            self.refresh_token = data['refresh']
            return data
        else:
            raise Exception(f"Login failed: {response.text}")
    
    def get_headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def make_request(self, method, endpoint, **kwargs):
        url = f'{self.base_url}{endpoint}'
        headers = self.get_headers()
        
        response = requests.request(method, url, headers=headers, **kwargs)
        
        # Handle token refresh
        if response.status_code == 401 and self.refresh_token:
            if self.refresh_access_token():
                headers = self.get_headers()
                response = requests.request(method, url, headers=headers, **kwargs)
        
        return response
    
    def refresh_access_token(self):
        response = requests.post(f'{self.base_url}/api/auth/refresh/', json={
            'refresh': self.refresh_token
        })
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access']
            return True
        return False

# Usage
client = APIClient()
client.login('username', 'password')

# Make authenticated requests
response = client.make_request('GET', '/api/courses/')
courses = response.json()
```

## Token Configuration

The JWT tokens are configured with the following settings:

- **Access Token Lifetime**: 60 minutes
- **Refresh Token Lifetime**: 7 days
- **Token Rotation**: Enabled (new refresh token issued on refresh)
- **Blacklisting**: Enabled (old tokens are invalidated)

## Security Features

1. **Token Blacklisting**: Logout invalidates refresh tokens
2. **Token Rotation**: New refresh tokens issued on access token refresh
3. **User Validation**: Checks for active and enabled users
4. **CORS Configuration**: Properly configured for frontend applications
5. **Password Validation**: Django's built-in password validators

## API Documentation

Full API documentation is available at:
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`

## Testing Authentication

You can test the authentication endpoints using tools like:
- Postman
- curl
- Django REST Framework browsable API
- Swagger UI

### Example curl commands:

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"testpass123","password_confirm":"testpass123","person_id":"12345","name":"Test","surname":"User"}'

# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'

# Access protected endpoint
curl -X GET http://localhost:8000/api/courses/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

All existing API endpoints now require authentication using JWT tokens. 