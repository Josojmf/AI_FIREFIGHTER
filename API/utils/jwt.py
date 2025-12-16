"""JWT utilities for token generation and validation."""
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from config import JWT_SECRET, JWT_ALGORITHM

def make_jwt(payload: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = payload.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=1)
    to_encode.update({"iat": datetime.utcnow(), "exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")

def verify_jwt(token: str) -> bool:
    try:
        decode_jwt(token)
        return True
    except ValueError:
        return False

def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = decode_jwt(token)
        return {"user_id": payload.get("user_id"), "username": payload.get("username"), "role": payload.get("role")}
    except ValueError:
        return None
