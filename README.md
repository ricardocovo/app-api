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
   DATABASE_URL=******host/database?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes
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
│   └── schemas/                # Pydantic request/response schemas
├── alembic/
│   ├── env.py                  # Async-aware Alembic environment
│   └── versions/               # Migration scripts
├── tests/                      # Pytest test suite
│   ├── conftest.py             # Shared async fixtures (SQLite in-memory)
│   └── test_models.py          # ORM model unit tests
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

## Dependencies

- **fastapi** - Web framework
- **uvicorn** - ASGI application server
- **sqlalchemy** - SQL toolkit and ORM with async support
- **aioodbc** - Async ODBC adapter
- **pyodbc** - ODBC database adapter
- **alembic** - Database migration tool
- **pydantic-settings** - Settings management
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
