"""
AUTH/auth.py
User management, registration, login with SQLite persistence
"""
import os
import json
import uuid
from datetime import datetime, timezone
from typing import Optional
from loguru import logger
from AUTH.password_utils import hash_password, verify_password
from AUTH.jwt_handler import create_token_for_user, decode_access_token

USERS_FILE = "AUTH/users.json"


def _load_users() -> dict:
    """Load users from JSON store."""
    if not os.path.exists(USERS_FILE):
        # Seed default admin
        default_users = {
            "admin": {
                "user_id": str(uuid.uuid4()),
                "username": "admin",
                "email": "admin@proofsar.ai",
                "hashed_password": hash_password("Admin@2026"),
                "role": "admin",
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            "analyst": {
                "user_id": str(uuid.uuid4()),
                "username": "analyst",
                "email": "analyst@proofsar.ai",
                "hashed_password": hash_password("Analyst@2026"),
                "role": "analyst",
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        }
        os.makedirs("AUTH", exist_ok=True)
        with open(USERS_FILE, "w") as f:
            json.dump(default_users, f, indent=2)
        logger.info("Created default users: admin / analyst")
        return default_users
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def _save_users(users: dict):
    """Persist users to JSON store."""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def register_user(username: str, password: str, email: str, role: str = "analyst") -> dict:
    """Register a new user. Role must be admin or analyst."""
    users = _load_users()
    if username in users:
        raise ValueError(f"Username '{username}' already exists")
    if role not in ["admin", "analyst"]:
        raise ValueError("Role must be 'admin' or 'analyst'")
    user = {
        "user_id": str(uuid.uuid4()),
        "username": username,
        "email": email,
        "hashed_password": hash_password(password),
        "role": role,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    users[username] = user
    _save_users(users)
    logger.info(f"Registered new user: {username} ({role})")
    return {"message": "User registered successfully", "username": username, "role": role}


def login_user(username: str, password: str) -> dict:
    """Authenticate user and return JWT token."""
    users = _load_users()
    user = users.get(username)
    if not user:
        raise ValueError("Invalid username or password")
    if not user.get("is_active", True):
        raise ValueError("Account is disabled")
    if not verify_password(password, user["hashed_password"]):
        raise ValueError("Invalid username or password")
    token_response = create_token_for_user(username, user["role"], user["user_id"])
    logger.info(f"User logged in: {username} ({user['role']})")
    return token_response


def get_current_user(token: str) -> Optional[dict]:
    """Decode token and return current user info."""
    payload = decode_access_token(token)
    if not payload:
        return None
    users = _load_users()
    username = payload.get("sub")
    user = users.get(username)
    if not user or not user.get("is_active", True):
        return None
    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "permissions": payload.get("permissions", [])
    }


def list_users() -> list:
    """List all users (admin only)."""
    users = _load_users()
    return [
        {k: v for k, v in u.items() if k != "hashed_password"}
        for u in users.values()
    ]
