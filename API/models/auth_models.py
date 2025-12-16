"""
Auth Models - Pydantic Models for Authentication, MFA & Password Management
===========================================================================
"""

from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    """
    Login normal con usuario/contraseña (y MFA opcional).
    """
    username: str
    password: str
    mfa_token: Optional[str] = None


class SSOLoginRequest(BaseModel):
    """
    Login SSO / login con token externo.
    """
    provider: str              # "google", "github", "custom", etc.
    external_token: str        # token OAuth/JWT externo
    email: Optional[EmailStr] = None
    name: Optional[str] = None


class RegisterRequest(BaseModel):  # ¡¡ESTA ES LA CLASE FALTANTE!!
    """
    Registro de usuario (usado por router Users y otros).
    """
    username: str
    password: str
    email: EmailStr
    name: str
    access_token: Optional[str] = None


class PasswordResetRequest(BaseModel):
    """
    Solicitar reset de contraseña por email.
    """
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """
    Confirmar reset de contraseña con token.
    """
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    """
    Cambiar contraseña estando autenticado.
    """
    old_password: str
    new_password: str


class MFASetupResponse(BaseModel):
    """
    Respuesta de la API al generar MFA (secreto + QR + clave manual).
    La usará el router de Auth/Users para devolver datos al backoffice.
    """
    ok: bool
    secret: Optional[str] = None
    qrcode: Optional[str] = None           # imagen en base64 o data URL
    manualentrykey: Optional[str] = None   # clave tipo "ABCD EFGH IJKL"
    detail: Optional[str] = None


class MFAVerifyRequest(BaseModel):
    """
    Modelo para verificar código MFA durante la configuración.
    """
    secret: str
    token: str


class MFALoginRequest(BaseModel):
    """
    Modelo para login con MFA (cuando el usuario ya tiene MFA habilitado).
    """
    username: str
    password: str
    mfa_token: str