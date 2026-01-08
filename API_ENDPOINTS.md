# API Endpoints Quick Reference

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication Endpoints

### 1. Login
**POST** `/auth/login`

**Request:**
```json
{
    "username": "string",
    "password": "string",
    "device_id": "string (optional)"
}
```

**Response:**
```json
{
    "access_token": "string",
    "refresh_token": "string",
    "token_type": "bearer",
    "expires_in": 1800
}
```

---

### 2. Refresh Token
**POST** `/auth/refresh`

**Request:**
```json
{
    "refresh_token": "string",
    "device_id": "string (optional)"
}
```

**Response:**
```json
{
    "access_token": "string",
    "refresh_token": "string",
    "token_type": "bearer",
    "expires_in": 1800
}
```

---

### 3. Logout
**POST** `/auth/logout`

**Headers:**
```
Authorization: Bearer {access_token}
X-Device-ID: string (optional)
```

**Response:**
```json
{
    "message": "Successfully logged out"
}
```

---

### 4. Get Current User
**GET** `/auth/me`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:**
```json
{
    "id": 1,
    "username": "string",
    "email": "string",
    "full_name": "string",
    "is_active": true,
    "is_superuser": false,
    "created_at": "datetime",
    "updated_at": "datetime",
    "last_login": "datetime"
}
```

---

### 5. Verify Token
**GET** `/auth/verify`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:**
```json
{
    "valid": true,
    "user_id": 1,
    "username": "string"
}
```

---

## Permission Endpoints

### 6. Check Permission
**POST** `/permissions/check`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request:**
```json
{
    "resource": "string",
    "action": "string",
    "attributes": {
        "key": "value"
    }
}
```

**Response:**
```json
{
    "allowed": true,
    "resource": "string",
    "action": "string",
    "message": "string"
}
```

---

### 7. Get My Permissions
**GET** `/permissions/my-permissions`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:**
```json
{
    "user_id": 1,
    "username": "string",
    "is_superuser": false,
    "permissions": [
        {
            "resource": "string",
            "action": "string",
            "attributes": {}
        }
    ]
}
```

---

## Status Codes

- `200 OK` - Request successful
- `401 Unauthorized` - Authentication required or failed
- `403 Forbidden` - Permission denied
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

## Notes

- All authenticated endpoints require `Authorization: Bearer {access_token}` header
- Access tokens expire in 30 minutes (configurable)
- Refresh tokens expire in 30 days (configurable)
- Use `device_id` for persistent login across app restarts
- Superusers have all permissions automatically

## User Management Endpoints

### 8. Create User
**POST** `/users/`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request:**
```json
{
    "username": "string",
    "email": "user@example.com",
    "password": "string",
    "full_name": "string (optional)"
}
```

**Response:**
```json
{
    "id": 1,
    "username": "string",
    "email": "string",
    "full_name": "string",
    "is_active": true,
    "is_superuser": false,
    "created_at": "datetime",
    "updated_at": "datetime",
    "last_login": null
}
```

---

### 9. Update User
**PUT** `/users/{user_id}`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request:**
```json
{
    "email": "new@example.com",
    "full_name": "New Name",
    "password": "newpassword",
    "is_active": true
}
```

**Response:**
```json
{ /* updated user object same as create response */ }
```

---

### 10. Delete User
**DELETE** `/users/{user_id}`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:**
```json
{
    "message": "User deleted"
}
```



