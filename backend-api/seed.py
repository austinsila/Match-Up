"""Dev seed: applies sql/schema.sql, then inserts courts, demo users and sample history.

Run:  docker compose exec backend-api python seed.py
Idempotent. Dev-only credentials live in database.DEMO_USERS; never use them in production.
"""
import asyncio
import random
from datetime import datetime, time, timedelta, timezone

import settings
from database import (
    apply_schema,
    connect_db,
    database,
    disconnect_db,
    reset_legacy_users_table,
    seed_courts,
    seed_users,
)


async def seed_history():
    """About 40 past bookings plus Pro subscription payments so admin charts have data."""
    if await database.fetch_val("SELECT COUNT(*) FROM bookings") > 0:
        return
    rng = random.Random(42)
    users = await database.fetch_all(
        "SELECT user_id, tier_status FROM users WHERE user_role <> 'admin'"
    )
    today = datetime.now(timezone.utc).date()
    for _ in range(40):
        user = rng.choice(users)
        pro = user["tier_status"] == "pro"
        day = today - timedelta(days=rng.randint(1, 28))
        hour = rng.choice([9, 10, 17, 18, 19, 20, 21])
        court = rng.randint(1, settings.COURT_COUNT)
        n_slots = rng.randint(1, 3)
        fee = settings.COURT_FEE_PER_SLOT * n_slots
        discount = fee * settings.PRO_DISCOUNT if pro else 0
        total = fee - discount
        created = datetime.combine(day, time(8, 0), tzinfo=timezone.utc) - timedelta(days=1)
        booking_id = await database.fetch_val(
            """
            INSERT INTO bookings (user_id, total_amount, discount_amount, status, created_at, completed_at)
            VALUES (:u, :t, :d, 'confirmed', :c, :done) RETURNING booking_id
            """,
            {
                "u": user["user_id"], "t": total, "d": discount, "c": created,
                "done": datetime.combine(day, time(hour, 0), tzinfo=timezone.utc)
                + timedelta(minutes=30 * n_slots),
            },
        )
        for k in range(n_slots):
            start = datetime.combine(day, time(hour, 0)) + timedelta(minutes=30 * k)
            end = start + timedelta(minutes=settings.SLOT_MINUTES)
            try:
                await database.execute(
                    """
                    INSERT INTO booking_slots
                        (booking_id, court_id, booking_date, start_time, end_time, status)
                    VALUES (:b, :c, :d, :s, :e, 'booked')
                    """,
                    {"b": booking_id, "c": court, "d": day, "s": start.time(), "e": end.time()},
                )
            except Exception:  # unique clash with another random booking; skip this slot
                pass
        await database.execute(
            """
            INSERT INTO payments (user_id, booking_id, type, amount, created_at)
            VALUES (:u, :b, 'booking', :a, :c)
            """,
            {"u": user["user_id"], "b": booking_id, "a": total, "c": created},
        )
    pro_user = await database.fetch_val(
        "SELECT user_id FROM users WHERE email = 'pro@matchup.test'"
    )
    for months_ago in (2, 1, 0):
        await database.execute(
            """
            INSERT INTO payments (user_id, type, amount, created_at)
            VALUES (:u, 'pro_subscription', :a, :c)
            """,
            {
                "u": pro_user,
                "a": settings.PRO_PRICE_MONTHLY,
                "c": datetime.now(timezone.utc) - timedelta(days=30 * months_ago),
            },
        )


async def main():
    await connect_db()
    try:
        await reset_legacy_users_table()
        await apply_schema()
        await seed_courts()
        await seed_users()
        await seed_history()
        print("Seed complete: 16 courts, demo users (@matchup.test), sample history.")
    finally:
        await disconnect_db()


if __name__ == "__main__":
    asyncio.run(main())
