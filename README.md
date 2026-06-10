# CRUD API – FastAPI + SQL Server

A modern, asynchronous REST API built with FastAPI and SQLAlchemy, designed for SQL Server databases. This project demonstrates best practices for building scalable, maintainable APIs with async support, database migrations, and proper configuration management.

## Architecture

### High-Level Request Flow

```mermaid
graph LR
    Client["Client"]
    Uvicorn["Uvicorn Server"]
    FastAPI["FastAPI Application"]
    Routes["Route Handlers"]
    CRUD["CRUD Operations"]
    SQLAlchemy["SQLAlchemy ORM"]
    Database["SQL Server Database"]
    
    Client -->|HTTP Request| Uvicorn
    Uvicorn -->|Route| FastAPI
    FastAPI -->|Dispatch| Routes
    Routes -->|Query/Mutate| CRUD
    CRUD -->|Generate SQL| SQLAlchemy
    SQLAlchemy -->|ODBC/aioodbc| Database
    Database -->|Result| SQLAlchemy
    SQLAlchemy -->|ORM Objects| CRUD
    CRUD -->|Data| Routes
    Routes -->|Pydantic Schema| FastAPI
    FastAPI -->|JSON Response| Uvicorn
    Uvicorn -->|HTTP Response| Client
```

### Project Structure & Components

```mermaid
graph TB
    App["app/"]
    Main["main.py<br/>FastAPI App"]
    API["api/routes/<br/>Endpoint Handlers"]
    Core["core/config.py<br/>Environment Config"]
    CRUD["crud/<br/>Database Operations"]
    DB["db/<br/>ORM Setup"]
    Models["models/<br/>SQLAlchemy ORM"]
    Schemas["schemas/<br/>Pydantic v2"]
    
    App --> Main
    App --> API
    App --> Core
    App --> CRUD
    App --> DB
    App --> Models
    App --> Schemas
    
    API -->|Uses| CRUD
    API -->|Validates| Schemas
    CRUD -->|Queries| Models
    Models -->|Uses| DB
    DB -->|Configured by| Core
    Schemas -->|Serializes| Models
```

### Data Model Relationships

```mermaid
erDiagram
    USER ||--o{ PROFILE : "has"
    USER ||--o{ PROFILE_FOLLOW : "follower"
    PROFILE ||--o{ PROFILE_FOLLOW : "followed"
    PROFILE ||--o{ PROFILE_CHANNEL : "has"
    
    USER {
        int id PK
        string username UK
        string email UK
        string password_hash
        timestamp created_at
        timestamp updated_at
    }
    
    PROFILE {
        int id PK
        int user_id FK
        string display_name
        string bio
        timestamp created_at
        timestamp updated_at
    }
    
    PROFILE_FOLLOW {
        int id PK
        int follower_id FK
        int profile_id FK
        timestamp created_at
    }
    
    PROFILE_CHANNEL {
        int id PK
        int profile_id FK
        string channel_name
        string channel_url
        timestamp created_at
        timestamp updated_at
    }
```

### Async Request Flow

```mermaid
sequenceDiagram
    participant Client as HTTP Client
    participant Server as Uvicorn
    participant Route as Route Handler
    participant DB as SQLAlchemy
    participant ODBC as aioodbc
    participant SQL as SQL Server
    
    Client->>Server: GET /api/v1/profiles?page=1
    activate Server
    Server->>Route: Dispatch Request
    activate Route
    Route->>DB: Session.query(Profile)
    activate DB
    DB->>ODBC: Execute SQL
    activate ODBC
    ODBC->>SQL: ODBC Query
    activate SQL
    SQL-->>ODBC: Result Set
    deactivate SQL
    ODBC-->>DB: Rows
    deactivate ODBC
    DB-->>Route: ORM Objects
    deactivate DB
    Route->>Route: Serialize to Pydantic
    Route-->>Server: JSON Response
    deactivate Route
    Server-->>Client: HTTP 200 + JSON
    deactivate Server
```

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

### Layer Overview

```mermaid
graph TB
    subgraph Presentation["Presentation Layer"]
        FastAPI["FastAPI<br/>Swagger UI / ReDoc"]
    end
    
    subgraph API["API Layer"]
        Routes["Route Handlers<br/>(app/api/routes/)"]
        Schemas["Pydantic Schemas<br/>(app/schemas/)"]
    end
    
    subgraph Business["Business Logic Layer"]
        CRUD["CRUD Operations<br/>(app/crud/)"]
    end
    
    subgraph Data["Data Layer"]
        Models["SQLAlchemy Models<br/>(app/models/)"]
        Session["Session Factory<br/>(app/db/session.py)"]
    end
    
    subgraph External["External"]
        Database["SQL Server<br/>Database"]
        Config["Config Management<br/>(app/core/config.py)"]
    end
    
    FastAPI --> Routes
    Routes --> Schemas
    Routes --> CRUD
    Schemas --> Models
    CRUD --> Models
    Models --> Session
    Session --> Database
    Config -.->|Environment| Routes
    Config -.->|Connection| Session
    
    style Presentation fill:#e1f5ff
    style API fill:#f3e5f5
    style Business fill:#e8f5e9
    style Data fill:#fff3e0
    style External fill:#f5f5f5
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

### Technology Stack Overview

```mermaid
graph LR
    subgraph Frontend["Frontend / Client"]
        HTTP["HTTP Client"]
    end
    
    subgraph Server["Application Server"]
        Uvicorn["Uvicorn<br/>ASGI Server"]
        FastAPI["FastAPI<br/>Web Framework"]
    end
    
    subgraph DataAccess["Data Access & ORM"]
        SQLAlchemy["SQLAlchemy 2.0<br/>ORM + QueryAPI"]
        Alembic["Alembic<br/>Migrations"]
    end
    
    subgraph Async["Async I/O"]
        aioodbc["aioodbc<br/>Async ODBC"]
    end
    
    subgraph Database["Database"]
        MSSQL["SQL Server<br/>Database"]
    end
    
    subgraph Utils["Utilities"]
        Pydantic["Pydantic v2<br/>Validation"]
        DotEnv["python-dotenv<br/>Config"]
    end
    
    HTTP --> Uvicorn
    Uvicorn --> FastAPI
    FastAPI --> SQLAlchemy
    FastAPI --> Pydantic
    SQLAlchemy --> aioodbc
    aioodbc --> MSSQL
    Alembic --> MSSQL
    FastAPI --> DotEnv
    
    style Frontend fill:#bbdefb
    style Server fill:#c8e6c9
    style DataAccess fill:#ffe0b2
    style Async fill:#f8bbd0
    style Database fill:#d1c4e9
    style Utils fill:#e0f2f1
```

### Package Details

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

### Development Workflow

```mermaid
graph LR
    Dev["Developer<br/>Changes Code"]
    Tests["Run Tests<br/>pytest"]
    Migrate["Run Migrations<br/>alembic upgrade"]
    Server["Start Server<br/>uvicorn --reload"]
    Test["Test API<br/>Swagger UI"]
    Debug["Fix Issues<br/>Iterate"]
    
    Dev -->|Create/Edit| Tests
    Tests -->|Fix?| Debug
    Tests -->|Pass| Migrate
    Debug -->|Retry| Tests
    Migrate -->|Success| Server
    Server -->|Running| Test
    Test -->|Issues| Debug
    Test -->|OK| Dev
    
    style Dev fill:#c8e6c9
    style Tests fill:#fff9c4
    style Migrate fill:#ffe0b2
    style Server fill:#bbdefb
    style Test fill:#f8bbd0
    style Debug fill:#ffccbc
```

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
