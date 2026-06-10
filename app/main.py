from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.routes import channels, follows, profiles, users
from app.core.config import settings
from app.core.limiter import limiter

app = FastAPI(
    title="CRUD API – FastAPI + SQL Server",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.get("/health", tags=["health"])
@limiter.exempt
async def health_check() -> dict:
    return {"status": "ok"}


app.include_router(users.router, prefix=settings.API_V1_PREFIX)
app.include_router(profiles.router, prefix=settings.API_V1_PREFIX)
app.include_router(follows.router, prefix=settings.API_V1_PREFIX)
app.include_router(channels.router, prefix=settings.API_V1_PREFIX)
