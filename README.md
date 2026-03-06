# Spine CRM API

Email automation CRM for prospect management.

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL
- pip

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
alembic upgrade head

# Start the server
python -m uvicorn app.main:app --reload
```

Server runs at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

---

## 📋 Features

### ✅ Implemented

- **User Authentication** (JWT-based)
  - Register, login, refresh tokens
  - Protected routes with user isolation

- **Products Management**
  - CRUD operations for products
  - User-scoped product ownership

- **Prospects Management**
  - CRUD operations for prospects
  - Create prospects with product interests in one step
  - User-scoped prospect ownership

- **Prospect-Product Relationships** 🆕
  - Link products to prospects with notes
  - Update relationship notes
  - Remove product interests
  - Automatic creation via `product_interest_ids`

- **Security**
  - IDOR protection (users can only access their own data)
  - JWT authentication on all protected routes
  - Input validation

---

## 🔑 Authentication

### Register

```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

### Login

```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=SecurePass123!
```

**Response:**

```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### Using the token

Include in all protected requests:

```http
Authorization: Bearer <access_token>
```

---

## 📦 Products API

### Create Product

```http
POST /api/products/
Authorization: Bearer <token>
Content-Type: application/json

{
  "item_number": "WIDGET-001",
  "name": "Super Widget",
  "short_description": "Amazing product"
}
```

### List Products

```http
GET /api/products/
Authorization: Bearer <token>
```

### Get Product

```http
GET /api/products/{id}
Authorization: Bearer <token>
```

### Update Product

```http
PATCH /api/products/{id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "short_description": "Updated description"
}
```

### Delete Product

```http
DELETE /api/products/{id}
Authorization: Bearer <token>
```

---

## 👥 Prospects API

### Create Prospect (Simple)

```http
POST /api/prospects/
Authorization: Bearer <token>
Content-Type: application/json

{
  "first_name": "Jane",
  "last_name": "Smith",
  "email": "jane@example.com",
  "phone_number": "+1234567890",
  "company_name": "Acme Corp",
  "position": "CEO",
  "source": "trade_show",
  "source_notes": "Met at conference"
}
```

### Create Prospect with Product Interests 🆕

```http
POST /api/prospects/
Authorization: Bearer <token>
Content-Type: application/json

{
  "first_name": "Jane",
  "last_name": "Smith",
  "email": "jane@example.com",
  "company_name": "Acme Corp",
  "position": "CEO",
  "source": "referral",
  "product_interest_ids": [1, 2, 3]
}
```

**This will:**

1. Create the prospect
2. Automatically create links to products 1, 2, and 3

### List Prospects

```http
GET /api/prospects/
Authorization: Bearer <token>
```

### Get Prospect

```http
GET /api/prospects/{id}
Authorization: Bearer <token>
```

### Update Prospect

```http
PUT /api/prospects/{id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "first_name": "Jane",
  "last_name": "Smith",
  "email": "jane@example.com",
  "company_name": "Acme Corp",
  "position": "CTO",
  "source": "referral",
  "status": "qualified"
}
```

### Delete Prospect

```http
DELETE /api/prospects/{id}
Authorization: Bearer <token>
```

---

## 🔗 Prospect-Product Relationships API 🆕

### Add Product Interest

```http
POST /api/prospects/{prospect_id}/products
Authorization: Bearer <token>
Content-Type: application/json

{
  "product_id": 1,
  "notes": "Very interested in this product"
}
```

### List Product Interests

```http
GET /api/prospects/{prospect_id}/products
Authorization: Bearer <token>
```

**Response:**

```json
[
  {
    "id": 1,
    "prospect_id": 1,
    "product_id": 1,
    "notes": "Very interested",
    "product": {
      "id": 1,
      "name": "Super Widget",
      "item_number": "WIDGET-001"
    }
  }
]
```

### Update Product Interest Notes

```http
PATCH /api/prospects/{prospect_id}/products/{product_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "product_id": 1,
  "notes": "Updated: Extremely interested!"
}
```

### Remove Product Interest

```http
DELETE /api/prospects/{prospect_id}/products/{product_id}
Authorization: Bearer <token>
```

---

## 🔒 Security

### User Isolation

All resources are scoped to the authenticated user:

- Users can only see/modify their own products
- Users can only see/modify their own prospects
- Users can only manage product interests for their own prospects

### IDOR Protection

Attempting to access another user's resources returns `404 Not Found` (not `403 Forbidden`) to prevent resource enumeration.

**Example:**

```http
GET /api/prospects/1
Authorization: Bearer <other_user_token>

Response: 404 Not Found
{
  "detail": "Prospect with ID 1 not found"
}
```

---

## 🗄️ Database Schema

### Users

- `id` (PK)
- `email` (unique)
- `hashed_password`
- `first_name`, `last_name`
- `gmail_connected`, `outlook_connected`

### Products

- `id` (PK)
- `user_id` (FK → users)
- `item_number` (unique per user)
- `name`
- `short_description`

### Prospects

- `id` (PK)
- `user_id` (FK → users)
- `email` (unique)
- `first_name`, `last_name`
- `phone_number`, `position`
- `company_name`, `company_size`, `market`
- `source`, `source_notes`, `status`

### Prospect-Products (Junction Table)

- `id` (PK)
- `prospect_id` (FK → prospects)
- `product_id` (FK → products)
- `notes`
- Unique constraint on (`prospect_id`, `product_id`)

---

## 🧪 Testing

### Manual Testing

1. Start the server: `python -m uvicorn app.main:app --reload`
2. Open Swagger UI: `http://localhost:8000/docs`
3. Register a user
4. Authorize with the token (🔒 button)
5. Test all endpoints

### Reset Database (Development)

```bash
python reset_db.py
```

**⚠️ WARNING:** This deletes ALL data!

### Check Database Status

```bash
python check_db.py
```

---

## 📝 Changelog

### v1.1.0 (2026-03-06)

**Added:**

- Prospect-Product relationship management (4 new endpoints)
- Create prospects with product interests in one step via `product_interest_ids`
- IDOR protection on all prospect-product routes
- Validation for duplicate product links
- Validation for non-existent products

**Fixed:**

- DELETE `/api/products/{id}` now works correctly (was returning 500 error)

**Security:**

- Enhanced user isolation on all prospect-product operations
- Returns 404 instead of 403 for better security

---

## 🐛 Known Issues

None at this time.

---

## 📞 Support

For issues or questions, please open an issue on GitHub.

---

## 📄 License

[Your License Here]
