# Copilot Instructions for `app-api`

## Build, test, and lint commands

### Environment setup
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run the API locally
```powershell
uvicorn app.main:app --reload
```

### Database migrations
```powershell
alembic upgrade head
```

### Tests
```powershell
# Full suite
pytest

# Single file
pytest tests\test_users_e2e.py -v

# Single test
pytest tests\test_users_e2e.py::TestUserCreate::test_create_user_success -q
```

### Build (container image)
```powershell
docker build -t app-api:local .
```

### Linting
No dedicated lint/type-check command is configured in this repository (`ruff`, `flake8`, `mypy`, and `pyproject.toml`/`setup.cfg` lint sections are absent).

## High-level architecture

- **Entry point and routing:** `app/main.py` creates the FastAPI app, exposes `/health`, and mounts entity routers under `settings.API_V1_PREFIX` (default `/api/v1`).
- **Request/data flow:** Route handlers in `app/api/routes/*` validate input with Pydantic schemas, call async CRUD functions in `app/crud/*`, and return schema-based responses.
- **Database layer:** `app/db/session.py` creates the async SQLAlchemy engine/session from `DATABASE_URL`; routes consume DB sessions via `Depends(get_db)`.
- **Model and migration wiring:** `app/db/base.py` imports all ORM models so Alembic autogenerate can discover metadata.
- **Testing architecture:** `tests/conftest.py` overrides `get_db` to use in-memory SQLite (`sqlite+aiosqlite:///:memory:`) with `StaticPool`, so tests run without SQL Server.
- **Deployment path:** `.github/workflows/deploy.yml` builds/pushes Docker image to ACR and updates Azure Container App, binding `DATABASE_URL` from Key Vault via managed identity.

## Key conventions in this codebase

- **Error mapping in routes:** Database integrity conflicts are translated to **HTTP 409** with explicit `await db.rollback()`; missing entities return **HTTP 404**.
- **Pagination contract:** List endpoints use `PaginationParams` (`page`, `size`, `offset`) and always respond with `Page[T]` via `Page.create(...)`.
- **Entity CRUD organization:** Each entity has a dedicated module in `app/crud/` with async `get_*`, `create_*`, `update_*`, `delete_*` functions. `ProfileFollow` intentionally supports create/delete only (no PATCH route).
- **Schema pattern:** Pydantic v2 `Base/Create/Update/Read` variants per entity; `Read` schemas use `ConfigDict(from_attributes=True)` for ORM serialization.
- **ORM naming strategy:** Python attributes are snake_case while many DB column names are explicitly mapped to camelCase names (for example `"createdAt"`, `"updatedAt"`, `"googleId"`).
- **Primary key and relation style:** Models use UUID primary keys and SQLAlchemy relationships with cascade behavior to support dependent-row cleanup.
