"""Password hashing, JWT helpers and FastAPI auth dependencies.

Role and tier are always re-read from the database; token claims are only
informational for the frontend and never trusted for authorization.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import clock
import settings
from database import get_user_by_id

bearer_scheme = HTTPBearer(auto_error=False)

BCRYPT_MAX_BYTES = 72


def require_jwt_secret() -> None:
    """Called at startup: refuse to run with an empty signing secret."""
    if not settings.JWT_SECRET:
        raise RuntimeError(
            "JWT_SECRET is empty. Set JWT_SECRET in .env (see .env.example) and restart."
        )


# --- Passwords ---
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:  # malformed hash or over-long password
        return False


# --- Tokens ---
def create_token(
    user_id: str,
    role: str,
    tier: str,
    secret: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    now = clock.now()
    delta = expires_delta if expires_delta is not None else timedelta(
        minutes=settings.JWT_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),
        "role": role,
        "tier": tier,
        "iat": int(now.timestamp()),
        "exp": int((now + delta).timestamp()),
    }
    return jwt.encode(payload, secret or settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str, secret: Optional[str] = None) -> dict:
    """Raises jwt.InvalidTokenError (incl. ExpiredSignatureError) when invalid.

    Expiry is checked against clock.now() so CLOCK_OFFSET affects it in dev.
    """
    payload = jwt.decode(
        token,
        secret or settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["sub", "exp"], "verify_exp": False, "verify_iat": False},
    )
    if payload["exp"] <= clock.now().timestamp():
        raise jwt.ExpiredSignatureError("Signature has expired")
    return payload


# --- Users ---
def effective_tier(row) -> str:
    """A Pro whose pro_expiry_date has passed is treated as free."""
    if row["tier_status"] != "pro":
        return "free"
    expiry = row["pro_expiry_date"]
    if expiry is None:
        return "free"
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    return "pro" if expiry > clock.now() else "free"


def user_to_dict(row) -> dict:
    return {
        "user_id": str(row["user_id"]),
        "full_name": row["full_name"],
        "email": row["email"],
        "role": row["user_role"],
        "tier": effective_tier(row),
        "pro_expiry_date": row["pro_expiry_date"],
        "accumulated_slots_count": row["accumulated_slots_count"],
        "free_slot_credits": row["free_slot_credits"],
    }


def token_for_user(user: dict) -> str:
    return create_token(user["user_id"], user["role"], user["tier"])


# --- Dependencies ---
def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    if credentials is None:
        raise _unauthorized("Not authenticated")
    try:
        payload = decode_token(credentials.credentials)
        user_id = str(uuid.UUID(payload["sub"]))
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Session expired, please log in again")
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise _unauthorized("Invalid token")
    row = await get_user_by_id(user_id)
    if row is None:
        raise _unauthorized("User no longer exists")
    return user_to_dict(row)


def require_role(*roles: str):
    async def checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to do this",
            )
        return user

    return checker


async def require_pro(user: dict = Depends(get_current_user)) -> dict:
    if user["tier"] != "pro":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This feature is for Pro members only",
        )
    return user
