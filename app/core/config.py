from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "TeamFlow"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    RATE_LIMIT_ENABLED: bool = True
    MAX_FAILED_LOGINS: int = 5
    LOCKOUT_MINUTES: int = 15

    PASSWORD_RESET_EXPIRE_MINUTES: int = 30
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    REDIS_URL: str = "redis://localhost:6379/0"

    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = False
    EMAIL_FROM: str = "TeamFlow <no-reply@teamflow.local>"

    @model_validator(mode="after")
    def check_secret_key(self):
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        if self.ENVIRONMENT == "production" and self.SECRET_KEY.startswith("change-me"):
            raise ValueError("Set a real SECRET_KEY in production")
        return self


settings = Settings()