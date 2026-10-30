from datetime import datetime
from pydantic import field_validator
from pydantic import BaseModel, ConfigDict, EmailStr, Field

COMMON_PASSWORDS = {
    "password", "password1", "12345678", "123456789", "1234567890",
    "qwertyuiop", "iloveyou", "admin123", "welcome1", "letmein123",
}

def validate_password_strength(value: str) -> str:
    if value.strip() != value:
        raise ValueError("Password cannot start or end with spaces")
    if value.lower() in COMMON_PASSWORDS:
        raise ValueError("Password is too common")
    if len(set(value)) < 4:
        raise ValueError("Password is too simple")
    return value

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Name cannot be empty")
        return value

    @field_validator("password")
    @classmethod
    def strong_enough(cls, value: str) -> str:
        return validate_password_strength(value)

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime