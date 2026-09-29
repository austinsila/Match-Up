# Match Up API contract (DRAFT — agree as a team, then treat as frozen)

Base path `/api`. JSON in/out. Auth = `Authorization: Bearer <JWT>` (claims: `sub` user_id, `role`, `tier`, `exp`).
Errors: `{ "detail": "message" }` with 401 (no/invalid token), 403 (wrong role/tier), 404, 409 (slot conflict), 422 (validation).
Money is THB, numbers with 2 decimals. Times are ISO 8601; slots are 30 minutes.

## Auth
| Method | Path | Auth | Body → Response |
| :-- | :-- | :-- | :-- |
| POST | `/auth/register` | none | `{full_name, email, password}` → `{user, token}` |
| POST | `/auth/login` | none | `{email, password}` → `{user, token}` |
| GET | `/auth/me` | any | → `{user_id, full_name, email, role, tier, pro_expiry_date, accumulated_slots_count, free_slot_credits}` |

(The boilerplate `POST /api/login` is replaced by `/auth/login`.)

## Courts and slots (badminton only for now)
| Method | Path | Auth | Notes |
| :-- | :-- | :-- | :-- |
| GET | `/courts` | any | 16 courts: `[{court_id, court_name, sport_type, slot_rate}]` |
| GET | `/slots?date=YYYY-MM-DD` | any | Grid: per court, per 30-min slot `status: available|held|booked` and `held_by_me`. 403 if date beyond tier window (Free 3 days, Pro 30) |
| POST | `/holds` | any | `{date, slots:[{court_id, start_time}]}` → `{booking_id, hold_expires_at}`; 8-min hold; 409 if any slot taken |
| DELETE | `/holds/{booking_id}` | owner | Release held slots |

## Checkout and bookings
| Method | Path | Auth | Notes |
| :-- | :-- | :-- | :-- |
| GET | `/checkout/{booking_id}/summary?use_credits=0..2&racket=0&shoes=0&shuttlecock=0` | owner | Price breakdown from `pricing`: court fees, Pro discount, equipment (Pro first racket+shoes free), credits, total |
| POST | `/checkout/{booking_id}/pay` | owner | Simulated PromptPay confirm. One transaction: booking→confirmed, slots held→booked, payment logged, credits deducted, loyalty applied. 409 if hold expired |
| GET | `/bookings/me` | any | Booking history with slots, equipment, status |
| POST | `/bookings/{booking_id}/cancel` | owner | Free >24h: free; <24h: 50% court fee; Pro: always free. Returns `{cancel_fee, refund}` |
| POST | `/bookings/{booking_id}/reschedule` | owner | Pro only (403 otherwise) |

## Membership
| Method | Path | Auth | Notes |
| :-- | :-- | :-- | :-- |
| GET | `/pricing` | none | Plans and prices for the pricing page |
| POST | `/membership/pro/pay` | any | Simulated pay 299 THB → `tier=pro`, `pro_expiry_date` +30 days (extends if already Pro); returns fresh token |

## Admin (role=admin)
| Method | Path | Notes |
| :-- | :-- | :-- |
| GET | `/admin/stats` | `{active_users, pro_users, pro_conversion_rate, monthly_transaction_volume, mrr, arr}` |
| GET | `/admin/revenue?days=30` | Daily revenue series for line chart |
| GET | `/admin/occupancy?days=14` | Court × hour heatmap data |
| GET | `/admin/users` | User list; `PATCH /admin/users/{id}` to change role/tier |
| GET | `/admin/transactions` | Payments log, paginated |
