from datetime import datetime, timedelta, timezone

import jwt
import pytest

import security
import settings

USER_ID = "3f2b8c1e-5d4a-4e6b-9a7c-1234567890ab"


def test_hash_and_verify_password():
    hashed = security.hash_password("hunter2hunter2")
    assert hashed != "hunter2hunter2"
    assert security.verify_password("hunter2hunter2", hashed)
    assert not security.verify_password("wrong-password", hashed)


def test_hashes_are_salted():
    assert security.hash_password("samepassword") != security.hash_password("samepassword")


def test_verify_password_bad_hash_is_false():
    assert security.verify_password("x", "not-a-bcrypt-hash") is False


def test_token_roundtrip():
    token = security.create_token(USER_ID, "customer", "free")
    payload = security.decode_token(token)
    assert payload["sub"] == USER_ID
    assert payload["role"] == "customer"
    assert payload["tier"] == "free"
    assert payload["exp"] > payload["iat"]


def test_expired_token_rejected():
    token = security.create_token(USER_ID, "customer", "free", expires_delta=timedelta(seconds=-5))
    with pytest.raises(jwt.ExpiredSignatureError):
        security.decode_token(token)


def test_expiry_follows_clock_offset(monkeypatch):
    token = security.create_token(USER_ID, "customer", "free")
    monkeypatch.setenv("CLOCK_OFFSET", "+2h")
    with pytest.raises(jwt.ExpiredSignatureError):
        security.decode_token(token)


def test_wrong_secret_rejected():
    token = security.create_token(USER_ID, "admin", "pro", secret="some-other-secret-value")
    with pytest.raises(jwt.InvalidSignatureError):
        security.decode_token(token)


def test_tampered_token_rejected():
    token = security.create_token(USER_ID, "customer", "free")
    header, payload, sig = token.split(".")
    forged = jwt.encode(
        {**jwt.decode(token, options={"verify_signature": False}), "role": "admin"},
        "attacker-secret",
        algorithm="HS256",
    ).split(".")[1]
    with pytest.raises(jwt.InvalidTokenError):
        security.decode_token(f"{header}.{forged}.{sig}")


def test_alg_none_rejected():
    forged = jwt.encode({"sub": USER_ID, "exp": 9999999999}, key=None, algorithm="none")
    with pytest.raises(jwt.InvalidTokenError):
        security.decode_token(forged)


def test_effective_tier_expiry():
    now = datetime.now(timezone.utc)
    active = {"tier_status": "pro", "pro_expiry_date": now + timedelta(days=5)}
    lapsed = {"tier_status": "pro", "pro_expiry_date": now - timedelta(days=1)}
    no_expiry = {"tier_status": "pro", "pro_expiry_date": None}
    free = {"tier_status": "free", "pro_expiry_date": now + timedelta(days=5)}
    assert security.effective_tier(active) == "pro"
    assert security.effective_tier(lapsed) == "free"
    assert security.effective_tier(no_expiry) == "free"
    assert security.effective_tier(free) == "free"


def test_require_jwt_secret_fails_when_empty(monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", "")
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        security.require_jwt_secret()
