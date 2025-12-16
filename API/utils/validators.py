"""
Validators - Validation utilities for user data
==============================================
"""

import re
import bcrypt
from typing import Tuple, Dict, Any


# Regex patterns
USERNAME_RE = re.compile(r"^[a-zA-Z0-9]{3,24}$")
EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def hash_password(password: str) -> str:
    """
    Hash password usando bcrypt
    
    Args:
        password: Contraseña en texto plano
        
    Returns:
        str: Password hasheado
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, pwd_hash: str) -> bool:
    """
    Verificar contraseña contra hash
    
    Args:
        password: Contraseña en texto plano
        pwd_hash: Hash de la contraseña
        
    Returns:
        bool: True si la contraseña es correcta
    """
    try:
        return bcrypt.checkpw(password.encode("utf-8"), pwd_hash.encode("utf-8"))
    except Exception:
        return False


def validate_username(username: str) -> Tuple[bool, str]:
    """
    Validar formato de username
    
    Args:
        username: Username a validar
        
    Returns:
        Tuple[bool, str]: (es_valido, mensaje_error)
    """
    if not username or not isinstance(username, str):
        return False, "Username es requerido"
    
    username = username.strip()
    
    if len(username) < 3:
        return False, "Username debe tener al menos 3 caracteres"
    
    if len(username) > 24:
        return False, "Username no puede tener más de 24 caracteres"
    
    if not USERNAME_RE.match(username):
        return False, "Username solo puede contener letras y números"
    
    return True, ""


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validar formato de email
    
    Args:
        email: Email a validar
        
    Returns:
        Tuple[bool, str]: (es_valido, mensaje_error)
    """
    if not email or not isinstance(email, str):
        return False, "Email es requerido"
    
    email = email.strip()
    
    if not EMAIL_RE.match(email):
        return False, "Formato de email inválido"
    
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validar contraseña
    
    Args:
        password: Contraseña a validar
        
    Returns:
        Tuple[bool, str]: (es_valido, mensaje_error)
    """
    if not password or not isinstance(password, str):
        return False, "Password es requerido"
    
    if len(password) < 6:
        return False, "Password debe tener al menos 6 caracteres"
    
    return True, ""


def validate_register(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validar datos de registro completos
    
    Args:
        data: Diccionario con datos de registro
        
    Returns:
        Tuple[bool, str]: (es_valido, mensaje_error)
    """
    # Validar username
    username = data.get("username", "").strip()
    valid, msg = validate_username(username)
    if not valid:
        return False, msg
    
    # Validar password
    password = data.get("password", "")
    valid, msg = validate_password(password)
    if not valid:
        return False, msg
    
    # Validar email
    email = data.get("email", "").strip()
    valid, msg = validate_email(email)
    if not valid:
        return False, msg
    
    # Validar name
    name = data.get("name", "").strip()
    if not name:
        return False, "Name es requerido"
    
    return True, ""


def validate_role(role: str) -> bool:
    """
    Validar que el rol sea válido
    
    Args:
        role: Rol a validar
        
    Returns:
        bool: True si el rol es válido
    """
    valid_roles = ["user", "admin", "moderator"]
    return role in valid_roles