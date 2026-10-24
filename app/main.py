from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME, debug=settings.DEBUG)


@app.get("/health")
def health():
    return {"status": "ok"}