from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings


def get_ip_address(request) -> str:
    """Return the client IP address.

    Thin wrapper around ``get_remote_address`` so that tests can override IP
    resolution by patching ``app.core.limiter.get_remote_address``.
    """
    return get_remote_address(request)


limiter = Limiter(
    key_func=get_ip_address,
    default_limits=[settings.RATE_LIMIT],
    storage_uri=settings.REDIS_URL,
    headers_enabled=True,
)
