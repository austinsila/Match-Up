"""Pure pricing, cancellation and loyalty math. No DB, no I/O.

All numbers come from settings.py. Endpoints call these functions; never
duplicate the math elsewhere. Money is Decimal, rounded to satang (0.01).
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

import settings

_CENT = Decimal("0.01")
ZERO = Decimal("0.00")


def money(value) -> Decimal:
    return Decimal(value).quantize(_CENT, rounding=ROUND_HALF_UP)


def is_pro_active(tier_status: str, pro_expiry_date: datetime | None, now: datetime) -> bool:
    """Perks stop the instant pro_expiry_date passes; never trust tier_status alone."""
    return tier_status == "pro" and pro_expiry_date is not None and pro_expiry_date > now


# --- Court fee ---
def court_fee_per_slot(is_pro: bool, slot_rate: Decimal | None = None) -> Decimal:
    """Fee for one 30-min slot after the tier discount. slot_rate defaults to the settings rate."""
    rate = Decimal(settings.COURT_FEE_PER_SLOT if slot_rate is None else slot_rate)
    discount = settings.PRO_DISCOUNT if is_pro else Decimal(0)
    return money(rate * (1 - discount))


# --- Equipment ---
def validate_equipment(equipment: dict[str, int] | None) -> dict[str, int]:
    """Return a clean {type: qty} with qty > 0. Raises ValueError on bad input (map to 422)."""
    clean = {}
    for item, qty in (equipment or {}).items():
        if item not in settings.EQUIPMENT_PRICES:
            raise ValueError(f"Unknown equipment: {item}")
        if isinstance(qty, bool) or not isinstance(qty, int) or qty < 0:
            raise ValueError(f"Invalid quantity for {item}")
        if qty > settings.EQUIPMENT_MAX_QTY:
            raise ValueError(f"At most {settings.EQUIPMENT_MAX_QTY} of each item per booking")
        if qty:
            clean[item] = qty
    return clean


def equipment_fees(equipment: dict[str, int] | None, is_pro: bool) -> dict[str, Decimal]:
    """Charged fee per item (per booking). Pro: first racket and first pair of shoes are free."""
    fees = {}
    for item, qty in validate_equipment(equipment).items():
        chargeable = qty - 1 if is_pro and item in settings.PRO_FREE_EQUIPMENT else qty
        fees[item] = money(settings.EQUIPMENT_PRICES[item] * chargeable)
    return fees


# --- Booking quote ---
@dataclass(frozen=True)
class Quote:
    slot_count: int
    credits_used: int
    court_gross: Decimal  # slots x base rate, before any discount
    pro_discount: Decimal  # 10% off the non-credit slots
    credit_discount: Decimal  # base value of the credit-paid slots
    court_paid: Decimal  # what the customer actually pays for courts
    equipment_gross: Decimal
    equipment_free_value: Decimal  # Pro free set value
    equipment_paid: Decimal
    equipment_fees: dict = field(default_factory=dict)
    total: Decimal = ZERO

    @property
    def discount_amount(self) -> Decimal:
        """Value stored in bookings.discount_amount."""
        return self.pro_discount + self.credit_discount + self.equipment_free_value


def quote_booking(
    slot_count: int,
    is_pro: bool,
    equipment: dict[str, int] | None = None,
    credits_to_use: int = 0,
    slot_rate: Decimal | None = None,
) -> Quote:
    """Price a booking. Raises ValueError on invalid input (map to 422).

    Credits zero the court fee of up to CREDIT_MAX_SLOTS_PER_BOOKING slots; the remaining
    slots are paid (with the Pro discount if Pro). The caller checks the user's balance.
    """
    if slot_count < 1:
        raise ValueError("Select at least one slot")
    if slot_count > settings.HOLD_MAX_SLOTS:
        raise ValueError(f"At most {settings.HOLD_MAX_SLOTS} slots per booking")
    if credits_to_use < 0:
        raise ValueError("Credits cannot be negative")
    if credits_to_use > settings.CREDIT_MAX_SLOTS_PER_BOOKING:
        raise ValueError(f"At most {settings.CREDIT_MAX_SLOTS_PER_BOOKING} credits per booking")
    if credits_to_use > slot_count:
        raise ValueError("Cannot use more credits than slots")

    base = money(settings.COURT_FEE_PER_SLOT if slot_rate is None else slot_rate)
    paid_slots = slot_count - credits_to_use
    court_gross = base * slot_count
    court_paid = court_fee_per_slot(is_pro, base) * paid_slots
    credit_discount = base * credits_to_use
    pro_discount = base * paid_slots - court_paid

    fees = equipment_fees(equipment, is_pro)
    clean = validate_equipment(equipment)
    equipment_gross = money(sum((settings.EQUIPMENT_PRICES[i] * q for i, q in clean.items()), Decimal(0)))
    equipment_paid = money(sum(fees.values(), Decimal(0)))
    total = max(ZERO, court_paid + equipment_paid)
    return Quote(
        slot_count=slot_count,
        credits_used=credits_to_use,
        court_gross=money(court_gross),
        pro_discount=money(pro_discount),
        credit_discount=money(credit_discount),
        court_paid=money(court_paid),
        equipment_gross=equipment_gross,
        equipment_free_value=money(equipment_gross - equipment_paid),
        equipment_paid=equipment_paid,
        equipment_fees=fees,
        total=money(total),
    )


# --- Cancellation ---
@dataclass(frozen=True)
class CancellationResult:
    late: bool
    fee: Decimal  # retained by us (court fee only)
    refund: Decimal  # returned to the customer
    credits_restored: int
    credits_forfeited: int


def cancellation_terms(
    is_pro: bool,
    slot_start: datetime,
    now: datetime,
    court_paid: Decimal,
    equipment_paid: Decimal = ZERO,
    credits_used: int = 0,
) -> CancellationResult:
    """Cancellation outcome, using the tier at the moment of cancelling.

    slot_start is the earliest slot start of the booking. Pro: always free. Free: more than
    FREE_CANCEL_HOURS ahead is free; exactly that or less is late (fee = rate x court fee
    actually paid). Equipment is always fully refunded. Credits are restored on a free cancel
    and forfeited on a late cancel. Rejecting cancellations after the start is the caller's job.
    """
    court_paid = money(court_paid)
    equipment_paid = money(equipment_paid)
    late = (not is_pro) and (slot_start - now) <= timedelta(hours=settings.FREE_CANCEL_HOURS)
    fee = money(court_paid * settings.LATE_CANCEL_FEE_RATE) if late else ZERO
    return CancellationResult(
        late=late,
        fee=fee,
        refund=money(court_paid + equipment_paid - fee),
        credits_restored=0 if late else credits_used,
        credits_forfeited=credits_used if late else 0,
    )


# --- Loyalty ---
def loyalty_award(previous_count: int, slots_completed: int) -> tuple[int, int]:
    """Return (new_accumulated_count, credits_granted).

    Each crossing of a multiple of LOYALTY_SLOTS_PER_REWARD grants LOYALTY_CREDITS_PER_REWARD,
    including several crossings in one jump.
    """
    if previous_count < 0 or slots_completed < 0:
        raise ValueError("Counts cannot be negative")
    new_count = previous_count + slots_completed
    step = settings.LOYALTY_SLOTS_PER_REWARD
    crossings = new_count // step - previous_count // step
    return new_count, crossings * settings.LOYALTY_CREDITS_PER_REWARD
