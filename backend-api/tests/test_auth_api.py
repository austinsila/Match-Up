"""API tests against a real Postgres. Skipped automatically when the DB is unreachable.

Run inside the container:  docker compose exec backend-api pytest
"""
import uuid
from datetime import timedelta

import httpx
import pytest
import pytest_asyncio

import security
from app import app
from database import connect_db, database, disconnect_db, setup_db

USER_KEYS = {
    "user_id", "full_name", "email", "role", "tier",
    "pro_expiry_date", "accumulated_slots_count", "free_slot_credits",
}


@pytest_asyncio.fixture
async def client():
    try:
        await connect_db()
        await setup_db()
    except Exception as exc:  # DB not reachable from this environment
        pytest.skip(f"database not reachable: {exc!r}")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    await disconnect_db()


def new_email():
    return f"t-{uuid.uuid4().hex[:10]}@example.com"


async def register(client, email=None, password="password123", **extra):
    body = {"full_name": "Test User", "email": email or new_email(), "password": password, **extra}
    return await client.post("/api/auth/register", json=body)


async def test_register_login_me(client):
    email = new_email().upper()
    r = await register(client, email=email)
    assert r.status_code == 201
    data = r.json()
    assert set(data["user"]) == USER_KEYS
    assert data["user"]["email"] == email.lower()
    assert data["user"]["role"] == "customer"
    assert data["user"]["tier"] == "free"
    assert data["user"]["accumulated_slots_count"] == 0

    r = await client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert r.status_code == 200
    token = r.json()["token"]

    r = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == email.lower()


async def test_register_ignores_client_role_and_tier(client):
    r = await register(client, role="admin", tier="pro", user_role="admin")
    assert r.status_code == 201
    assert r.json()["user"]["role"] == "customer"
    assert r.json()["user"]["tier"] == "free"


async def test_duplicate_email_409(client):
    email = new_email()
    assert (await register(client, email=email)).status_code == 201
    r = await register(client, email=email.upper())
    assert r.status_code == 409
    assert "already exists" in r.json()["detail"]


async def test_register_validation_422(client):
    assert (await register(client, password="short")).status_code == 422
    assert (await register(client, email="not-an-email")).status_code == 422
    assert (await register(client, password="x" * 80)).status_code == 422
    r = await client.post("/api/auth/register", json={"email": new_email()})
    assert r.status_code == 422


async def test_login_invalid_401(client):
    email = new_email()
    await register(client, email=email)
    r = await client.post("/api/auth/login", json={"email": email, "password": "wrongpassword"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid email or password"
    r = await client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "x"})
    assert r.status_code == 401


async def test_me_requires_valid_token(client):
    assert (await client.get("/api/auth/me")).status_code == 401
    r = await client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"})
    assert r.status_code == 401
    expired = security.create_token(str(uuid.uuid4()), "admin", "pro", expires_delta=timedelta(seconds=-1))
    r = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401
    # valid signature but user does not exist
    ghost = security.create_token(str(uuid.uuid4()), "admin", "pro")
    r = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {ghost}"})
    assert r.status_code == 401


async def test_old_login_route_removed(client):
    r = await client.post("/api/login", json={"email": "a@b.co", "password": "x"})
    assert r.status_code == 404


async def test_role_and_pro_dependencies(client):
    # Throwaway routes exercising the dependencies.
    if not any(getattr(r, "path", "") == "/_t/admin" for r in app.routes):
        from fastapi import Depends

        app.add_api_route("/_t/admin", lambda u=Depends(security.require_role("admin")): {"ok": True})
        app.add_api_route("/_t/pro", lambda u=Depends(security.require_pro): {"ok": True})

    async def token_for(email, password):
        r = await client.post("/api/auth/login", json={"email": email, "password": password})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['token']}"}

    free = await token_for("free@matchup.test", "password")
    admin = await token_for("admin@matchup.test", "admin1234")
    pro = await token_for("pro@matchup.test", "password")

    assert (await client.get("/_t/admin")).status_code == 401
    assert (await client.get("/_t/admin", headers=free)).status_code == 403
    assert (await client.get("/_t/admin", headers=admin)).status_code == 200
    assert (await client.get("/_t/pro", headers=free)).status_code == 403
    assert (await client.get("/_t/pro", headers=pro)).status_code == 200

    # A forged role claim in a token does not grant access: role is read from the DB.
    me = (await client.get("/api/auth/me", headers=free)).json()
    forged = security.create_token(me["user_id"], "admin", "pro")
    r = await client.get("/_t/admin", headers={"Authorization": f"Bearer {forged}"})
    assert r.status_code == 403
