from slowapi import Limiter
from starlette.requests import Request


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


# NOTE: SlowAPI uses in-memory storage by default. This works correctly for a
# single Uvicorn worker but will NOT enforce limits across multiple workers
# (e.g. `uvicorn --workers 4`). For multi-worker production, switch to a Redis
# backend: Limiter(key_func=get_client_ip, storage_uri="redis://localhost:6379")
# and add `redis` to requirements.txt.
limiter = Limiter(key_func=get_client_ip)