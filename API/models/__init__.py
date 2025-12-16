"""
Models Package - Pydantic Models for FirefighterAI API
======================================================
"""

from .auth_models import (
    RegisterRequest,
    LoginRequest,
    SSOLoginRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    ChangePasswordRequest,
    MFASetupResponse,
    MFAVerifyRequest,
    MFALoginRequest,
)

from .user_models import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
)

from .card_models import (
    MemoryCardCreate,
    MemoryCardUpdate,
    MemoryCardResponse,
    MemoryCardReview,
    BulkMemoryCardCreate,
    MemoryCardStats,
)

from .token_models import (
    AccessTokenCreate,
    AccessTokenUpdate,
    AccessTokenResponse,
    AccessTokenUse,
    AccessTokenStats,
)

__all__ = [
    # Auth
    "RegisterRequest",
    "LoginRequest",
    "SSOLoginRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "ChangePasswordRequest",
    "MFASetupResponse",
    "MFAVerifyRequest",
    "MFALoginRequest",
    # Users
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",
    # Cards
    "MemoryCardCreate",
    "MemoryCardUpdate",
    "MemoryCardResponse",
    "MemoryCardReview",
    "BulkMemoryCardCreate",
    "MemoryCardStats",
    # Tokens
    "AccessTokenCreate",
    "AccessTokenUpdate",
    "AccessTokenResponse",
    "AccessTokenUse",
    "AccessTokenStats",
]