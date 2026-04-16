"""
AUTH/jwt_handler.py
JWT token creation, validation, and role-based access control
"""
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "proofsar_super_secret_jwt_key_change_in_production_2026")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))

ROLES = {
    "admin": [
        "read", "write", "delete", "generate_sar", "edit_sar", 
        "approve_sar", "manage_users", "view_audit", "system_metrics"
    ],
    "analyst": [
        "read", "write", "generate_sar", "edit_sar", "view_audit"
    ],
    "manager": [
        "read", "generate_sar", "approve_sar", "view_audit"
    ]
}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(hours=JWT_EXPIRY_HOURS)
    )
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
        "jti": str(uuid.uuid4()) # token identifier for revocation if needed
    })
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a long-lived refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
        "jti": str(uuid.uuid4())
    })
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token. Returns payload or None."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            logger.warning("Token type mismatch")
            return None
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


def get_user_permissions(role: str) -> list:
    """Return list of permissions for a given role."""
    return ROLES.get(role.lower(), [])


def has_permission(role: str, permission: str) -> bool:
    """Check if a role has a specific permission."""
    return permission in get_user_permissions(role)


def create_token_for_user(username: str, role: str, user_id: str) -> dict:
    """Create a full auth response with token and metadata."""
    token_data = {
        "sub": username,
        "role": role,
        "user_id": user_id,
        "permissions": get_user_permissions(role)
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": username})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": JWT_EXPIRY_HOURS * 3600,
        "role": role,
        "username": username,
        "permissions": get_user_permissions(role)
    }
