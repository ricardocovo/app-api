# CRUD API – FastAPI + SQL Server

A modern, asynchronous REST API built with FastAPI and SQLAlchemy, designed for SQL Server databases. This project demonstrates best practices for building scalable, maintainable APIs with async support, database migrations, and proper configuration management.

## Features

- **FastAPI**: Modern, fast web framework with automatic API documentation
- **Async/Await**: Full async support for high performance
- **SQLAlchemy 2.0**: ORM with async support and typed `Mapped[]` column declarations
- **SQL Server**: Integrated with ODBC driver for SQL Server compatibility
- **Alembic**: Database migration management (async-aware `env.py`)
- **Pydantic**: Data validation and settings management
- **Environment Configuration**: Secure configuration via `.env` files

## Requirements

- Python 3.12+
- SQL Server database
- ODBC Driver 18 for SQL Server (for SQL Server connectivity)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd app-api
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure the database connection:
   - Copy `.env.example` to `.env` (if available) or create a `.env` file
   - Set your SQL Server connection string:
   ```
   DATABASE_URL=mssql+pyodbc://username:password@hostname/database?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes
   ```

## Running the Application

Start the development server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

- **API Documentation (Swagger UI)**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Project Structure

```
app-api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── api/
│   │   └── routes/             # API route handlers
│   ├── core/
│   │   └── config.py           # Configuration management
│   ├── crud/                   # CRUD operations
│   ├── db/
│   │   ├── base.py             # DeclarativeBase + model imports for Alembic
│   │   └── session.py          # Async engine and session factory
│   ├── models/                 # SQLAlchemy 2.0 ORM models
│   │   ├── user.py             # User model
│   │   ├── profile.py          # Profile model
│   │   ├── profile_follow.py   # ProfileFollow model
│   │   └── profile_channel.py  # ProfileChannel model
│   └── schemas/                # Pydantic v2 request/response schemas
│       ├── user.py             # User schemas
│       ├── profile.py          # Profile schemas
│       ├── profile_follow.py   # ProfileFollow schemas
│       ├── profile_channel.py  # ProfileChannel schemas
│       └── pagination.py       # PaginationParams + Page[T] wrapper
├── alembic/
│   ├── env.py                  # Async-aware Alembic environment
│   └── versions/               # Migration scripts
├── tests/                      # Pytest test suite
│   ├── conftest.py             # Shared async fixtures (SQLite in-memory)
│   ├── test_models.py          # ORM model unit tests
│   └── test_schemas.py         # Pydantic schema unit tests
├── scripts/                    # Utility scripts
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
└── README.md
```

## Data Models

The API uses four SQLAlchemy 2.0 ORM models with typed `Mapped[]` columns, integer identity PKs, and explicit bidirectional relationships.

### Column naming convention

ERD fields are defined in camelCase. Python attributes use snake_case throughout:

| ERD (camelCase)  | Python attribute (snake_case) |
|------------------|-------------------------------|
| `userId`         | `user_id`                     |
| `displayName`    | `display_name`                |
| `passwordHash`   | `password_hash`               |
| `followerId`     | `follower_id`                 |
| `profileId`      | `profile_id`                  |
| `channelName`    | `channel_name`                |
| `channelUrl`     | `channel_url`                 |
| `createdAt`      | `created_at`                  |
| `updatedAt`      | `updated_at`                  |

### Entity relationships

```
User ──(1-N)──> Profile ──(1-N)──> ProfileFollow
                        └──(1-N)──> ProfileChannel
User ──(1-N)──> ProfileFollow  (as follower)
```

| Model            | Table              | PK | Notable columns                                                        |
|------------------|--------------------|----|------------------------------------------------------------------------|
| `User`           | `users`            | id | username, email, password_hash, created_at                             |
| `Profile`        | `profiles`         | id | user_id (FK→users), display_name, bio, created_at, updated_at          |
| `ProfileFollow`  | `profile_follows`  | id | follower_id (FK→users), profile_id (FK→profiles), created_at           |
| `ProfileChannel` | `profile_channels` | id | profile_id (FK→profiles), channel_name, channel_url, created_at, updated_at |

All FK columns use `ondelete="CASCADE"`.

## Pydantic Schemas

The `app/schemas/` package exposes **four variants** for every entity plus shared pagination utilities.

### Schema conventions

| Variant    | Purpose                                                    |
|------------|------------------------------------------------------------|
| `Base`     | Shared fields (inherited by `Create` and `Read`)           |
| `Create`   | Required fields for insert; excludes server-generated fields (`id`, timestamps) |
| `Update`   | All fields `Optional` for partial PATCH semantics          |
| `Read`     | Full record (id + timestamps); `model_config = ConfigDict(from_attributes=True)` enables ORM-mode serialisation |

- **Field naming**: API fields use **snake_case** (matching ORM attributes).
- **Email validation**: `UserCreate` / `UserUpdate` use `pydantic.EmailStr` (requires `pydantic[email]`).
- **URL validation**: `ProfileChannelCreate` / `ProfileChannelUpdate` use `pydantic.HttpUrl`.
- **Auth tokens excluded**: `User.accessToken` / `User.refreshToken` are intentionally omitted this iteration.

### Per-entity schemas

| Entity           | Schemas                                                         |
|------------------|-----------------------------------------------------------------|
| `User`           | `UserBase`, `UserCreate`, `UserUpdate`, `UserRead`              |
| `Profile`        | `ProfileBase`, `ProfileCreate`, `ProfileUpdate`, `ProfileRead`  |
| `ProfileFollow`  | `ProfileFollowBase`, `ProfileFollowCreate`, `ProfileFollowUpdate`, `ProfileFollowRead` |
| `ProfileChannel` | `ProfileChannelBase`, `ProfileChannelCreate`, `ProfileChannelUpdate`, `ProfileChannelRead` |

### Pagination utilities

`PaginationParams` captures `page` and `size` query parameters and exposes a computed `offset` property.  
`Page[T]` is a generic response envelope:

```python
from app.schemas import Page, PaginationParams

params = PaginationParams(page=2, size=10)
page = Page.create(items=results, total=total_count, params=params)
# → Page(items=[...], total=42, page=2, size=10, pages=5)
```


## Dependencies

- **fastapi** - Web framework
- **uvicorn** - ASGI application server
- **sqlalchemy** - SQL toolkit and ORM with async support
- **aioodbc** - Async ODBC adapter
- **pyodbc** - ODBC database adapter
- **alembic** - Database migration tool
- **pydantic-settings** - Settings management
- **pydantic[email]** - Data validation with email support (requires `email-validator`)
- **python-dotenv** - Environment variable management
- **pytest / pytest-asyncio / aiosqlite** - Test infrastructure

## Configuration

Configuration is managed through environment variables in the `.env` file:

- `DATABASE_URL`: SQL Server connection string
- `APP_ENV`: Application environment (development, production)
- `API_V1_PREFIX`: API version prefix (default: `/api/v1`)

## Development

### Database Migrations

Use Alembic to manage database schema changes:

```bash
# Apply all pending migrations (creates tables on first run)
alembic upgrade head

# Revert all migrations (drops all tables)
alembic downgrade base

# Revert the last migration
alembic downgrade -1

# Create a new auto-generated migration (requires a running DB)
alembic revision --autogenerate -m "migration message"
```

### Running Tests

Tests use an in-memory SQLite database and do **not** require a running SQL Server:

```bash
pytest
```

**Test Structure:**
- `tests/test_utils.py` - Reusable test utilities and helper functions
- `tests/test_models.py` - ORM model unit tests
- `tests/test_schemas.py` - Pydantic schema validation tests
- `tests/test_crud.py` - CRUD operation tests
- `tests/test_routes.py` - Basic route integration tests
- `tests/test_users_e2e.py` - Comprehensive User E2E tests (60+ tests)
- `tests/test_profiles_e2e.py` - Comprehensive Profile E2E tests (40+ tests)
- `tests/test_follows_e2e.py` - Comprehensive Follow E2E tests (30+ tests)
- `tests/test_channels_e2e.py` - Comprehensive Channel E2E tests (35+ tests)

**Run specific test files:**
```bash
# E2E tests for users
pytest tests/test_users_e2e.py -v

# E2E tests for profiles
pytest tests/test_profiles_e2e.py -v

# E2E tests for follows
pytest tests/test_follows_e2e.py -v

# E2E tests for channels
pytest tests/test_channels_e2e.py -v

# Run all tests with coverage
pytest tests/ -v --cov=app
```

**E2E Test Coverage:**
The E2E tests cover over 180 scenarios including:
- **Happy path operations**: Create, read, list, update, delete for each entity
- **Error cases**: Invalid FK references, duplicate records, missing fields, invalid types
- **Pagination**: Valid/invalid page sizes, boundary conditions
- **Cascading deletes**: Verify that deleting parent entities properly cascades
- **Workflows**: Realistic multi-step user journeys (registration, profile setup, social interactions)

### API Routes

Routes are organized in `app/api/routes/`. To add new endpoints:

1. Create a new router module in `app/api/routes/`
2. Define your route handlers
3. Register the router in `app/main.py`

## Health Check

The API includes a health check endpoint:

```
GET /health
```

Response: `{"status": "ok"}`

## License

[Add your license information here]
