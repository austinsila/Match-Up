# Match Up ER diagram (draft — matches `backend-api/sql/schema.sql`)

```mermaid
erDiagram
    USERS ||--o{ BOOKINGS : makes
    USERS ||--o{ PAYMENTS : pays
    BOOKINGS ||--o{ BOOKING_SLOTS : reserves
    BOOKINGS ||--o{ EQUIPMENT_RENTALS : includes
    BOOKINGS ||--o{ PAYMENTS : "settled by"
    SPORTS_COURTS ||--o{ BOOKING_SLOTS : hosts

    USERS {
        uuid user_id PK
        varchar full_name
        varchar email UK
        text password_hash
        text user_role "customer|admin"
        text tier_status "free|pro"
        timestamptz pro_expiry_date
        int accumulated_slots_count
        int free_slot_credits
    }
    SPORTS_COURTS {
        int court_id PK
        text sport_type
        varchar court_name UK
        numeric slot_rate "per 30 min"
    }
    BOOKINGS {
        uuid booking_id PK
        uuid user_id FK
        numeric total_amount
        numeric discount_amount
        int credits_used
        text status "holding|confirmed|cancelled|completed"
        numeric cancel_fee
    }
    BOOKING_SLOTS {
        uuid slot_id PK
        uuid booking_id FK
        int court_id FK
        date booking_date
        time start_time
        time end_time
        timestamptz hold_expires_at
        text status "held|booked"
    }
    EQUIPMENT_RENTALS {
        uuid rental_id PK
        uuid booking_id FK
        text equipment_type "racket|shuttlecock|shoes"
        int quantity
        numeric rental_fee
    }
    PAYMENTS {
        uuid payment_id PK
        uuid user_id FK
        uuid booking_id FK
        text type "booking|pro_subscription|cancellation_fee|refund"
        numeric amount
        text status
    }
```

Design notes
- `booking_slots` has `UNIQUE (court_id, booking_date, start_time)`: the database itself prevents double-booking. A row exists only while a slot is held/booked; expired holds are replaced.
- `payments` is the transaction/subscription log the course requires; admin KPIs and MRR are computed from it.
- Changes from the proposal: `courts.hourly_rate` → `slot_rate` (per 30 min), added `payments`, `credits_used`, `cancel_fee`, `quantity`.
