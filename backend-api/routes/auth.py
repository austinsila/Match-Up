from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from database import database, get_user_by_email
from security import (
    BCRYPT_MAX_BYTES,
    get_current_user,
    hash_password,
    token_for_user,
    user_to_dict,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# Placeholder hash so unknown emails cost the same as wrong passwords.
_DUMMY_HASH = hash_password("not-a-real-password")


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    email: str = Field(max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8)

    @field_validator("full_name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Full name is required")
        return v

    @field_validator("email")
    @classmethod
    def lower_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def password_size(cls, v: str) -> str:
        if len(v.encode("utf-8")) > BCRYPT_MAX_BYTES:
            raise ValueError("Password must be at most 72 bytes")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    user_id: str
    full_name: str
    email: str
    role: str
    tier: str
    pro_expiry_date: Optional[datetime] = None
    accumulated_slots_count: int
    free_slot_credits: int


class AuthResponse(BaseModel):
    user: UserOut
    token: str


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest):
    # role/tier are never taken from the client: DB defaults are customer/free.
    row = await database.fetch_one(
        """
        INSERT INTO users (full_name, email, password_hash)
        VALUES (:full_name, :email, :password_hash)
        ON CONFLICT (email) DO NOTHING
        RETURNING *
        """,
        {
            "full_name": payload.full_name,
            "email": payload.email,
            "password_hash": hash_password(payload.password),
        },
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    user = user_to_dict(row)
    return {"user": user, "token": token_for_user(user)}


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest):
    row = await get_user_by_email(payload.email.strip())
    password_ok = verify_password(
        payload.password, row["password_hash"] if row else _DUMMY_HASH
    )
    if row is None or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    user = user_to_dict(row)
    return {"user": user, "token": token_for_user(user)}


@router.get("/me", response_model=UserOut)
async def me(user: dict = Depends(get_current_user)):
    return user
