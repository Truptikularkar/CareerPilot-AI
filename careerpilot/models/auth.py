from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class User(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login_at: Optional[datetime] = None
    candidate_id: Optional[str] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long.")
    full_name: str = Field(..., min_length=2, description="Full name is required.")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        has_alpha = any(c.isalpha() for c in v)
        has_num = any(c.isdigit() for c in v)
        if not (has_alpha and has_num):
            raise ValueError("Password must contain at least one letter and one number.")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    device_info: Optional[str] = "Desktop/Laptop"


class UserSession(BaseModel):
    id: str
    user_id: str
    token: str
    device_info: str = "Desktop/Laptop"
    ip_address: Optional[str] = None
    expires_at: datetime
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("New password must be at least 8 characters long.")
        has_alpha = any(c.isalpha() for c in v)
        has_num = any(c.isdigit() for c in v)
        if not (has_alpha and has_num):
            raise ValueError("New password must contain at least one letter and one number.")
        return v
