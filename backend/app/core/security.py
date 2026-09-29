"""Password hashing (Argon2id) and session-cookie helpers.

No JWTs, no localStorage. The cookie only ever carries an opaque random
session id; all session state lives server-side in the `sessions` table.
"""
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from fastapi import Response

from app.config import get_settings

settings = get_settings()

# Argon2id is the default variant for argon2-cffi's PasswordHasher.
_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=64 * 1024,  # 64 MiB
    parallelism=2,
    hash_len=32,
    salt_len=16,
)


def hash_password(plain_password: str) -> str:
    return _hasher.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        _hasher.verify(password_hash, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False
    return True


def needs_rehash(password_hash: str) -> bool:
    """Call after a successful verify; if True, re-hash with current params."""
    return _hasher.check_needs_rehash(password_hash)


def new_session_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=settings.session_ttl_minutes)


def set_session_cookie(response: Response, session_id: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_id,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        max_age=settings.session_ttl_minutes * 60,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
    )
