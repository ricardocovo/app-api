# CRUD API – FastAPI + SQL Server

A modern, asynchronous REST API built with FastAPI and SQLAlchemy, designed for SQL Server databases. This project demonstrates best practices for building scalable, maintainable APIs with async support, database migrations, and proper configuration management.

## Features

- **FastAPI**: Modern, fast web framework with automatic API documentation
- **Async/Await**: Full async support for high performance
- **SQLAlchemy 2.0**: ORM with async support for database operations
- **SQL Server**: Integrated with ODBC driver for SQL Server compatibility
- **Alembic**: Database migration management
- **Pydantic**: Data validation and settings management
- **Environment Configuration**: Secure configuration via `.env` files

## Requirements

- Python 3.8+
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
   DATABASE_URL=mssql+aioodbc://user:password@host/database?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes
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
│   │   ├── base.py             # Database base classes
│   │   └── session.py          # Database session management
│   ├── models/                 # SQLAlchemy ORM models
│   └── schemas/                # Pydantic request/response schemas
├── scripts/                    # Utility scripts
├── requirements.txt            # Python dependencies
└── README.md
```

## Dependencies

- **fastapi** - Web framework
- **uvicorn** - ASGI application server
- **sqlalchemy** - SQL toolkit and ORM with async support
- **aioodbc** - Async ODBC adapter
- **pyodbc** - ODBC database adapter
- **alembic** - Database migration tool
- **pydantic-settings** - Settings management
- **python-dotenv** - Environment variable management

## Configuration

Configuration is managed through environment variables in the `.env` file:

- `DATABASE_URL`: SQL Server connection string
- `APP_ENV`: Application environment (development, production)
- `API_V1_PREFIX`: API version prefix (default: `/api/v1`)

## Development

### Database Migrations

Use Alembic to manage database schema changes:

```bash
# Create a new migration
alembic revision --autogenerate -m "migration message"

# Apply migrations
alembic upgrade head

# Revert migrations
alembic downgrade -1
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