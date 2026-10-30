from pydantic import BaseModel, Field

from pydantic import EmailStr, field_validator

from app.modules.users.schemas import validate_password_strength


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=200)

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def strong(cls, value: str) -> str:
        return validate_password_strength(value)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def strong(cls, value: str) -> str:
        return validate_password_strength(value)


class MessageResponse(BaseModel):
    message: str