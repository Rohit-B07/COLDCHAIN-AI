"""Security primitives: password hashing, JWT issuing/validation.

Passwords are hashed with bcrypt; access tokens are signed JWTs; refresh
tokens are opaque and stored hashed server-side so a leak cannot be replayed.
"""

import datetime as dt
import hashlib
import secrets
from typing import Any
from uuid import UUID

import bcrypt
import jwt

from app.core.config import get_settings


def generate_api_key() -> str:
    """Generate a URL-safe random API key."""
    return secrets.token_urlsafe(48)


def sha256_hex(value: str) -> str:
    """Return the SHA-256 hex digest of a string (e.g. for masking secrets)."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


# ---- Password hashing -----------------------------------------------------


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt (returns bytes encoded salt)."""
    if not password:
        raise ValueError("password must not be empty")
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


# --------------------------------------------------------------------------
# JWT access tokens
# --------------------------------------------------------------------------


def _now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def create_access_token(subject: str, role: str, expires_minutes: int | None = None) -> str:
    """Issue a signed JWT access token for the given user subject."""
    settings = get_settings()
    lifetime = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    now = _now()
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + dt.timedelta(minutes=lifetime)).timestamp()),
        "iss": settings.JWT_ISSUER,
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT, raising on expiry or signature failure."""
    settings = get_settings()
    return dict(
        jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            issuer=settings.JWT_ISSUER,
        )
    )


# ---- Refresh tokens --------------------------------------------------------


def generate_refresh_token() -> str:
    """Return a fresh random opaque refresh token."""
    return secrets.token_urlsafe(64)


def hash_refresh_token(token: str) -> str:
    """Deterministically hash a refresh token so plaintext is never stored."""
    return sha256_hex(token)


def refresh_token_expiry(days: int | None = None) -> dt.datetime:
    """Return the expiry timestamp for a new refresh token."""
    settings = get_settings()
    return _now() + dt.timedelta(days=days or settings.REFRESH_TOKEN_EXPIRE_DAYS)


def subject_to_uuid(token: str) -> UUID:
    """Extract the user UUID subject from a validated access token."""
    return UUID(decode_token(token)["sub"])
