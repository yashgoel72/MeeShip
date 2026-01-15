# Meesho Image Optimizer API Documentation

## Overview

The Meesho Image Optimizer provides a RESTful API for image optimization services. This document describes all available endpoints, request/response formats, and authentication requirements.

## Base URL

```
Development: http://localhost:8000/api/v1
Production: https://api.meesho-optimizer.com/api/v1
```

## Authentication

Most endpoints require JWT (JSON Web Token) authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

---

## Endpoints

### Health Check

#### GET /health

Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-08T12:00:00Z"
}
```

---

### Authentication

#### POST /auth/register

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "full_name": "John Doe"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-08T12:00:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid input data
- `409 Conflict` - Email already registered

---

#### POST /auth/login

Authenticate and receive access tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid credentials
- `403 Forbidden` - Account disabled

---

#### GET /auth/me

Get current user information.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-08T12:00:00Z"
}
```

---

### Image Optimization

#### POST /images/optimize

Optimize a single image.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Request Body (form-data):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| image | file | Yes | Image file (JPEG, PNG, WebP) |
| quality | integer | No | Output quality (1-100, default: 80) |
| format | string | No | Output format (jpeg, png, webp) |
| max_width | integer | No | Maximum width in pixels |
| max_height | integer | No | Maximum height in pixels |
| preserve_metadata | boolean | No | Keep EXIF data (default: false) |

**Response (200 OK):**
```json
{
  "success": true,
  "original": {
    "filename": "photo.jpg",
    "size_bytes": 2500000,
    "width": 4000,
    "height": 3000,
    "format": "jpeg"
  },
  "optimized": {
    "filename": "photo_optimized.jpg",
    "size_bytes": 500000,
    "width": 1920,
    "height": 1440,
    "format": "jpeg",
    "url": "https://cdn.example.com/optimized/photo_optimized.jpg"
  },
  "compression_ratio": 0.8,
  "processing_time_ms": 1250
}
```

**Error Responses:**
- `400 Bad Request` - Invalid image or parameters
- `413 Payload Too Large` - Image exceeds size limit
- `415 Unsupported Media Type` - Unsupported image format

---

#### POST /images/batch

Optimize multiple images in batch.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Request Body (form-data):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| images | file[] | Yes | Array of image files (max 10) |
| quality | integer | No | Output quality (1-100) |
| format | string | No | Output format |

**Response (200 OK):**
```json
{
  "success": true,
  "total_images": 5,
  "processed": 5,
  "failed": 0,
  "results": [
    {
      "original_filename": "image1.jpg",
      "success": true,
      "optimized_url": "https://cdn.example.com/optimized/image1.jpg",
      "compression_ratio": 0.75
    }
  ],
  "total_processing_time_ms": 5000
}
```

---

#### GET /images/history

Get optimization history for the authenticated user.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| page | integer | No | Page number (default: 1) |
| limit | integer | No | Items per page (default: 20, max: 100) |
| from_date | string | No | Filter from date (ISO 8601) |
| to_date | string | No | Filter to date (ISO 8601) |

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "abc123",
      "original_filename": "photo.jpg",
      "original_size": 2500000,
      "optimized_size": 500000,
      "format": "jpeg",
      "created_at": "2024-01-08T12:00:00Z",
      "download_url": "https://cdn.example.com/optimized/photo.jpg"
    }
  ],
  "total": 150,
  "page": 1,
  "pages": 8,
  "limit": 20
}
```

---

### User Settings

#### GET /users/settings

Get user preferences and settings.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "default_quality": 80,
  "default_format": "webp",
  "preserve_metadata": false,
  "notification_email": true,
  "api_key": "sk_live_xxx..."
}
```

---

#### PATCH /users/settings

Update user settings.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "default_quality": 85,
  "default_format": "jpeg",
  "preserve_metadata": true
}
```

**Response (200 OK):**
```json
{
  "message": "Settings updated successfully",
  "settings": {
    "default_quality": 85,
    "default_format": "jpeg",
    "preserve_metadata": true
  }
}
```

---

## Error Handling

All errors follow a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Invalid request data |
| UNAUTHORIZED | 401 | Missing or invalid token |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| CONFLICT | 409 | Resource already exists |
| RATE_LIMITED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Server error |

---

## Rate Limiting

API requests are rate-limited to prevent abuse:

| Plan | Requests/minute | Batch size |
|------|-----------------|------------|
| Free | 10 | 5 images |
| Pro | 100 | 20 images |
| Enterprise | 1000 | 50 images |

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704715200
```

---

## SDKs and Examples

### Python Example

```python
import requests

API_URL = "http://localhost:8000/api/v1"
TOKEN = "your_jwt_token"

headers = {"Authorization": f"Bearer {TOKEN}"}

# Optimize an image
with open("image.jpg", "rb") as f:
    response = requests.post(
        f"{API_URL}/images/optimize",
        headers=headers,
        files={"image": f},
        data={"quality": 80, "format": "webp"}
    )

result = response.json()
print(f"Compressed: {result['compression_ratio']*100}%")
```

### JavaScript Example

```javascript
const API_URL = 'http://localhost:8000/api/v1';
const TOKEN = 'your_jwt_token';

async function optimizeImage(file) {
  const formData = new FormData();
  formData.append('image', file);
  formData.append('quality', '80');

  const response = await fetch(`${API_URL}/images/optimize`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${TOKEN}`
    },
    body: formData
  });

  return response.json();
}
```

---

## Changelog

### v1.0.0 (2024-01-08)
- Initial API release
- Image optimization endpoints
- User authentication
- Batch processing support