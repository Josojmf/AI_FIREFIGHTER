"""
Access Token Models - Pydantic Models for Token Management
=========================================================
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class AccessTokenCreate(BaseModel):
    """Modelo para crear access token"""
    name: str = Field(..., min_length=3, max_length=100)
    max_uses: int = Field(default=1, ge=1, le=1000)
    expires_at: Optional[datetime] = None
    recipient_email: Optional[EmailStr] = None
    metadata: Optional[Dict[str, Any]] = Field(default={})
    send_email: bool = Field(default=False)


class AccessTokenUpdate(BaseModel):
    """Modelo para actualizar access token"""
    name: Optional[str] = None
    max_uses: Optional[int] = Field(default=None, ge=1, le=1000)
    expires_at: Optional[datetime] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            valid = ['active', 'inactive', 'expired', 'used']
            if v not in valid:
                raise ValueError(f'Status must be one of {valid}')
        return v


class AccessTokenResponse(BaseModel):
    """Respuesta con datos de access token"""
    id: str
    token: str
    name: str
    max_uses: int
    current_uses: int
    expires_at: Optional[datetime] = None
    status: str
    created_by: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    usage_history: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True


class AccessTokenUse(BaseModel):
    """Modelo para usar/consumir token"""
    username: Optional[str] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None


class AccessTokenStats(BaseModel):
    """Estadísticas de access tokens"""
    total_tokens: int
    active_tokens: int
    expired_tokens: int
    used_tokens: int
    total_uses: int