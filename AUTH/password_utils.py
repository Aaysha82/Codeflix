"""
AUTH/password_utils.py
Secure password hashing and verification using bcrypt
"""
import bcrypt
import secrets
import string
from loguru import logger


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt with salt."""
    if not plain_password or len(plain_password) < 6:
        raise ValueError("Password must be at least 6 characters long")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def generate_temp_password(length: int = 12) -> str:
    """Generate a cryptographically secure temporary password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def validate_password_strength(password: str) -> dict:
    """Validate password meets security requirements."""
    issues = []
    if len(password) < 8:
        issues.append("Minimum 8 characters required")
    if not any(c.isupper() for c in password):
        issues.append("At least one uppercase letter required")
    if not any(c.islower() for c in password):
        issues.append("At least one lowercase letter required")
    if not any(c.isdigit() for c in password):
        issues.append("At least one digit required")
    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "strength": "strong" if len(issues) == 0 else "weak"
    }
