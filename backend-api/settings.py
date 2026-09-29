"""Single source of truth for prices, limits and environment config.

Never hard-code these numbers elsewhere; import them from here.
"""
import os
from decimal import Decimal

# --- Environment (see ../.env.example) ---
APP_ENV = os.getenv("APP_ENV", "dev")  # "dev" enables demo seeding and legacy-table reset
JWT_SECRET =os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

# --- Scope: badminton only for now ---
SPORT = "badminton"
COURT_COUNT = 16  # Court 1 .. Court 16

# --- Pricing (THB) ---
SLOT_MINUTES = 30
COURT_FEE_PER_SLOT = Decimal("90")
PRO_DISCOUNT = Decimal("0.10")
PRO_PRICE_MONTHLY = Decimal("299")
PRO_DURATION_DAYS = 30

EQUIPMENT_PRICES = {
    "racket": Decimal("50"),
    "shuttlecock": Decimal("60"),  # per tube (3 pcs)
    "shoes": Decimal("50"),  # per pair
}
# Pro perk: first set per booking is free = one racket + one pair of shoes
PRO_FREE_EQUIPMENT = ("racket", "shoes")

# --- Booking rules ---
HOLD_MINUTES = 8
FREE_ADVANCE_DAYS = 3
PRO_ADVANCE_DAYS = 30
PEAK_START_HOUR = 18
PEAK_END_HOUR = 22

# --- Cancellation ---
FREE_CANCEL_HOURS = 24
LATE_CANCEL_FEE_RATE = Decimal("0.5")  # of the court fee, Free tier < 24h

# --- Loyalty: book 20 slots, get 2 free slots ---
LOYALTY_SLOTS_PER_REWARD = 20
LOYALTY_CREDITS_PER_REWARD = 2
