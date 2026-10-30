import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.common.exceptions import AppError
from app.core.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.teams.router import router as teams_router
from app.modules.projects.router import router as projects_router
from app.modules.tasks.router import router as tasks_router
from app.modules.comments.router import router as comments_router
from app.modules.activity.router import router as activity_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.notifications.router import router as notifications_router

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.rate_limit import limiter

from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.db.session import SessionLocal

from app.core.logging import setup_logging
from app.core.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware

logger = logging.getLogger("app.error")

setup_logging(settings.DEBUG)
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "TeamFlow is a project & task management API inspired by Trello/Jira. "
        "Features: JWT auth with refresh-token rotation, team/project/task hierarchy, "
        "real-time activity log, in-app notifications, and a live dashboard."
    ),
    version="1.0.0",
    debug=settings.DEBUG,
)

app.state.limiter = limiter
limiter.enabled = settings.RATE_LIMIT_ENABLED
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(users_router, prefix=settings.API_V1_PREFIX)
app.include_router(teams_router, prefix=settings.API_V1_PREFIX)
app.include_router(projects_router, prefix=settings.API_V1_PREFIX)
app.include_router(tasks_router, prefix=settings.API_V1_PREFIX)
app.include_router(comments_router, prefix=settings.API_V1_PREFIX)
app.include_router(activity_router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard_router, prefix=settings.API_V1_PREFIX)
app.include_router(notifications_router, prefix=settings.API_V1_PREFIX)


@app.exception_handler(AppError)
def app_error_handler(request: Request, exc: AppError):
    headers = {}
    if exc.status_code == 401:
        headers["WWW-Authenticate"] = "Bearer"
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=headers)


@app.exception_handler(IntegrityError)
def integrity_error_handler(request: Request, exc: IntegrityError):
    return JSONResponse(status_code=409, content={"detail": "Conflict: duplicate or invalid reference"})


@app.exception_handler(Exception)
def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all handler — prevents stack traces from leaking in responses."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health", tags=["health"], summary="Health check")
def health():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content={"status": "error", "detail": "database unavailable"})
    return {"status": "ok"}