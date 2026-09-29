-- Match Up schema (DRAFT for team review; freeze before feature work).
-- Idempotent: safe to run repeatedly. If an old boilerplate `users` table exists,
-- run `docker compose down -v` once to reset the dev database.

CREATE TABLE IF NOT EXISTS users (
    user_id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name               VARCHAR(120) NOT NULL,
    email                   VARCHAR(255) NOT NULL UNIQUE,
    password_hash           TEXT NOT NULL,
    user_role               TEXT NOT NULL DEFAULT 'customer'
                            CHECK (user_role IN ('customer', 'coach', 'admin')),
    tier_status             TEXT NOT NULL DEFAULT 'free'
                            CHECK (tier_status IN ('free', 'pro')),
    pro_expiry_date         TIMESTAMPTZ,
    accumulated_slots_count INT NOT NULL DEFAULT 0 CHECK (accumulated_slots_count >= 0),
    free_slot_credits       INT NOT NULL DEFAULT 0 CHECK (free_slot_credits >= 0),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sports_courts (
    court_id    INT PRIMARY KEY,
    sport_type  TEXT NOT NULL DEFAULT 'badminton'
                CHECK (sport_type IN ('badminton', 'football', 'basketball')),
    court_name  VARCHAR(50) NOT NULL UNIQUE,
    slot_rate   NUMERIC(10, 2) NOT NULL CHECK (slot_rate >= 0)
);

CREATE TABLE IF NOT EXISTS bookings (
    booking_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(user_id),
    total_amount    NUMERIC(10, 2) NOT NULL DEFAULT 0,
    discount_amount NUMERIC(10, 2) NOT NULL DEFAULT 0,
    credits_used    INT NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'holding'
                    CHECK (status IN ('holding', 'confirmed', 'cancelled', 'completed')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    cancelled_at    TIMESTAMPTZ,
    cancel_fee      NUMERIC(10, 2) NOT NULL DEFAULT 0
);

-- A row exists only while a slot is held or booked. Available means no live row.
-- Expired holds (hold_expires_at < now) must be treated as available and replaced.
CREATE TABLE IF NOT EXISTS booking_slots (
    slot_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id      UUID REFERENCES bookings(booking_id) ON DELETE CASCADE,
    court_id        INT NOT NULL REFERENCES sports_courts(court_id),
    booking_date    DATE NOT NULL,
    start_time      TIME NOT NULL,
    end_time        TIME NOT NULL,
    hold_expires_at TIMESTAMPTZ,
    status          TEXT NOT NULL DEFAULT 'held'
                    CHECK (status IN ('available', 'held', 'booked')),
    UNIQUE (court_id, booking_date, start_time)
);

CREATE TABLE IF NOT EXISTS equipment_rentals (
    rental_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id     UUID NOT NULL REFERENCES bookings(booking_id) ON DELETE CASCADE,
    equipment_type TEXT NOT NULL CHECK (equipment_type IN ('racket', 'shuttlecock', 'shoes')),
    quantity       INT NOT NULL DEFAULT 1 CHECK (quantity > 0),
    rental_fee     NUMERIC(10, 2) NOT NULL DEFAULT 0
);

-- Transaction / subscription log (required by course guidelines; feeds admin KPIs and MRR)
CREATE TABLE IF NOT EXISTS payments (
    payment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL REFERENCES users(user_id),
    booking_id UUID REFERENCES bookings(booking_id),
    type       TEXT NOT NULL CHECK (type IN ('booking', 'pro_subscription', 'cancellation_fee', 'refund')),
    amount     NUMERIC(10, 2) NOT NULL,
    status     TEXT NOT NULL DEFAULT 'paid' CHECK (status IN ('pending', 'paid', 'failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_slots_date ON booking_slots (booking_date, court_id);
CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_payments_created ON payments (created_at);
