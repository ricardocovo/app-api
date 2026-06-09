from fastapi import FastAPI

from app.api.routes import channels, follows, profiles, users
from app.core.config import settings

app = FastAPI(
    title="CRUD API – FastAPI + SQL Server",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok"}


app.include_router(users.router, prefix=settings.API_V1_PREFIX)
app.include_router(profiles.router, prefix=settings.API_V1_PREFIX)
app.include_router(follows.router, prefix=settings.API_V1_PREFIX)
app.include_router(channels.router, prefix=settings.API_V1_PREFIX)
