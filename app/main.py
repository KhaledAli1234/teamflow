from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.common.exceptions import AppError
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME, debug=settings.DEBUG)


@app.exception_handler(AppError)
def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/health")
def health():
    return {"status": "ok"}