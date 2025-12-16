"""
Models Package - Pydantic Models for FirefighterAI API
======================================================
"""

from .auth_models import (
    RegisterRequest,  # ¡¡ASEGÚRATE DE QUE ESTÁ!!
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
    UserStats,
)

from .card_models import (
    MemoryCardBase,
    MemoryCardCreate,
    MemoryCardUpdate,
    MemoryCardResponse,
    MemoryCardReview,
    MemoryCardReviewRequest,
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
    "RegisterRequest",  # ¡¡ASEGÚRATE DE QUE ESTÁ!!
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
    "UserStats",
    # Cards
    "MemoryCardBase",
    "MemoryCardCreate",
    "MemoryCardUpdate",
    "MemoryCardResponse",
    "MemoryCardReview",
    "MemoryCardReviewRequest",
    "BulkMemoryCardCreate",
    "MemoryCardStats",
    # Tokens
    "AccessTokenCreate",
    "AccessTokenUpdate",
    "AccessTokenResponse",
    "AccessTokenUse",
    "AccessTokenStats",
]