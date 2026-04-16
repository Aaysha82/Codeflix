"""
AUTH/auth.py
User management with SQLAlchemy persistence
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from loguru import logger

from AUTH.password_utils import hash_password, verify_password
from AUTH.jwt_handler import create_token_for_user, decode_access_token
from BACKEND.database import User, SessionLocal

def _get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

def seed_default_users():
    """Seed default users if the table is empty."""
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            admin = User(
                user_id=str(uuid.uuid4()),
                username="admin",
                email="admin@proofsar.ai",
                hashed_password=hash_password("Admin@2026"),
                role="admin",
                is_active=True,
                created_at=datetime.now(timezone.utc)
            )
            analyst = User(
                user_id=str(uuid.uuid4()),
                username="analyst",
                email="analyst@proofsar.ai",
                hashed_password=hash_password("Analyst@2026"),
                role="analyst",
                is_active=True,
                created_at=datetime.now(timezone.utc)
            )
            db.add_all([admin, analyst])
            db.commit()
            logger.info("Database seeded with default users: admin, analyst")
    finally:
        db.close()

def register_user(username: str, password: str, email: str, role: str = "analyst") -> dict:
    """Register a new user in the database."""
    db = SessionLocal()
    try:
        db_user = db.query(User).filter(User.username == username).first()
        if db_user:
            raise ValueError(f"Username '{username}' already exists")
        
        if role not in ["admin", "analyst", "manager"]:
            raise ValueError("Invalid role specified")
            
        user = User(
            user_id=str(uuid.uuid4()),
            username=username,
            email=email,
            hashed_password=hash_password(password),
            role=role,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add(user)
        db.commit()
        logger.info(f"Registered new user: {username} ({role})")
        return {"username": username, "role": role, "status": "success"}
    finally:
        db.close()

def login_user(username: str, password: str) -> dict:
    """Authenticate user against database and return JWT."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user or not user.is_active:
            raise ValueError("Invalid username or deactivated account")
        
        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid password")
            
        token_response = create_token_for_user(username, user.role, user.user_id)
        return token_response
    finally:
        db.close()

def get_current_user(token: str) -> Optional[dict]:
    """Validate token and return user data from DB."""
    payload = decode_access_token(token)
    if not payload:
        return None
        
    db = SessionLocal()
    try:
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        if not user or not user.is_active:
            return None
            
        return {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "permissions": payload.get("permissions", [])
        }
    finally:
        db.close()

def list_users() -> List[dict]:
    """Return all users for admin dashboard."""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        return [
            {
                "username": u.username,
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat()
            } for u in users
        ]
    finally:
        db.close()
