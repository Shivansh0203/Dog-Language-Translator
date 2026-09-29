import re
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.-]{3,50}$")


class PetCreate(BaseModel):
    """Optional pet profile submitted alongside registration."""

    name: str = Field(min_length=1, max_length=100)
    breed: str | None = Field(default=None, max_length=100)
    age: str | None = Field(default=None, max_length=50)
    gender: str | None = Field(default=None, max_length=20)
    species: str = Field(default="dog", pattern="^dog$")

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        allowed = {"male", "female", "other"}
        if value.lower() not in allowed:
            raise ValueError(f"gender must be one of {sorted(allowed)}")
        return value.lower()


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str = Field(min_length=8, max_length=128)
    pet: PetCreate | None = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if not USERNAME_RE.match(value):
            raise ValueError(
                "username must be 3-50 characters: letters, numbers, underscore, dot, or hyphen"
            )
        return value

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if value.isdigit() or value.isalpha():
            raise ValueError("password must contain a mix of letters and numbers")
        return value


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=1, description="Username or email")
    password: str = Field(min_length=1)


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PetOut(BaseModel):
    id: uuid.UUID
    name: str
    breed: str | None
    age: str | None
    gender: str | None
    avatar_url: str | None
    species: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RegisterResponse(BaseModel):
    user: UserOut
    pet: PetOut | None = None


class MessageResponse(BaseModel):
    message: str
