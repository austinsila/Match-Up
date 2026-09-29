import logging
import os
from datetime import timedelta
from pathlib import Path

import bcrypt
from databases import Database

import clock
import settings

logger = logging.getLogger("matchup.db")

POSTGRES_USER = os.getenv("POSTGRES_USER", "temp")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "temp")
POSTGRES_DB = os.getenv("POSTGRES_DB", "advcompro")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "db")

DATABASE_URL = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}/{POSTGRES_DB}"
)

SCHEMA_PATH = Path(__file__).parent / "sql" / "schema.sql"

# Dev-only demo accounts. Never use these credentials in production.
DEMO_USERS = [
    # (full_name, email, password, role, tier)
    ("Demo Free", "free@matchup.test", "password", "customer", "free"),
    ("Demo Pro", "pro@matchup.test", "password", "customer", "pro"),
    ("Demo Coach", "coach@matchup.test", "password", "coach", "free"),
    ("Demo Admin", "admin@matchup.test", "admin1234", "admin", "free"),
]

database = Database(DATABASE_URL)


async def connect_db():
    await database.connect()


async def disconnect_db():
    await database.disconnect()


async def reset_legacy_users_table():
    """The class boilerplate had a `users` table keyed by email with no user_id.

    Detect it and, in dev only, drop it so the new schema can be created.
    """
    has_users = await database.fetch_val("SELECT to_regclass('public.users') IS NOT NULL")
    if not has_users:
        return
    has_user_id = await database.fetch_val(
        """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'user_id'
        )
        """
    )
    if has_user_id:
        return
    if settings.APP_ENV != "dev":
        raise RuntimeError("Legacy boilerplate users table found; migrate it manually.")
    logger.warning("Legacy boilerplate 'users' table detected (no user_id); dropping it (dev only).")
    await database.execute("DROP TABLE users CASCADE")


async def apply_schema():
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    sql = "\n".join(line for line in sql.splitlines() if not line.strip().startswith("--"))
    for statement in (s.strip() for s in sql.split(";")):
        if statement:
            await database.execute(statement)


async def seed_courts():
    for i in range(1, settings.COURT_COUNT + 1):
        await database.execute(
            """
            INSERT INTO sports_courts (court_id, sport_type, court_name, slot_rate)
            VALUES (:id, :sport, :name, :rate)
            ON CONFLICT DO NOTHING
            """,
            {
                "id": i,
                "sport": settings.SPORT,
                "name": f"Court {i}",
                "rate": settings.COURT_FEE_PER_SLOT,
            },
        )


async def seed_users():
    now = clock.now()
    for name, email, password, role, tier in DEMO_USERS:
        exists = await database.fetch_val(
            "SELECT 1 FROM users WHERE email = :e", {"e": email}
        )
        if exists:
            continue  # skip the slow bcrypt hash on every restart
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        expiry = now + timedelta(days=settings.PRO_DURATION_DAYS) if tier == "pro" else None
        await database.execute(
            """
            INSERT INTO users (full_name, email, password_hash, user_role, tier_status, pro_expiry_date)
            VALUES (:n, :e, :p, :r, :t, :x)
            ON CONFLICT (email) DO NOTHING
            """,
            {"n": name, "e": email, "p": hashed, "r": role, "t": tier, "x": expiry},
        )


async def setup_db():
    """Idempotent: safe on every startup."""
    await reset_legacy_users_table()
    await apply_schema()
    await seed_courts()
    if settings.APP_ENV == "dev":
        await seed_users()


async def get_user_by_email(email: str):
    return await database.fetch_one(
        "SELECT * FROM users WHERE email = :email", {"email": email.lower()}
    )


async def get_user_by_id(user_id: str):
    return await database.fetch_one(
        "SELECT * FROM users WHERE user_id = :user_id", {"user_id": user_id}
    )
