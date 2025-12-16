"""
User Models - Pydantic models for User Management
=================================================
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    name: Optional[str] = None
    role: str = Field(default="user")  # "user" o "admin"


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)
    access_token: Optional[str] = None  # por si usas tokens de invitación


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None  # "active" / "inactive"
    mfa_enabled: Optional[bool] = None

    class Config:
        extra = "ignore"


class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    name: Optional[str] = None
    role: str
    status: str
    created_at: datetime
    last_login: Optional[datetime] = None
    email_verified: bool = False
    mfa_enabled: bool = False

    # Campos opcionales para progreso / backoffice
    has_leitner_progress: Optional[bool] = False
    has_backoffice_cards: Optional[bool] = False
    metadata: Dict[str, Any] = {}

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    ok: bool = True
    users: List[UserResponse]


class UserStats(BaseModel):
    total: int
    active: int
    inactive: int
    with_mfa: int
    admins: int
    regular_users: int
    registered_today: int
    registered_this_week: int
