from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

import pricing
import settings

D = Decimal
BASE = settings.COURT_FEE_PER_SLOT
PRO_SLOT = BASE * (1 - settings.PRO_DISCOUNT)
P = settings.EQUIPMENT_PRICES
NOW = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)


# --- court fee ---
def test_free_court_fee_is_base_rate():
    assert pricing.court_fee_per_slot(False) == BASE


def test_pro_court_fee_has_discount():
    assert pricing.court_fee_per_slot(True) == PRO_SLOT
    assert pricing.court_fee_per_slot(True) < BASE


def test_court_fee_uses_court_rate_when_given():
    assert pricing.court_fee_per_slot(False, D("100")) == D("100.00")


def test_money_rounds_half_up():
    assert pricing.money(D("1.005")) == D("1.01")


def test_quote_returns_decimal_money():
    q = pricing.quote_booking(3, False)
    assert isinstance(q.total, Decimal)
    assert q.total == BASE * 3


# --- equipment ---
def test_free_pays_full_equipment():
    q = pricing.quote_booking(1, False, {"racket": 1, "shoes": 1, "shuttlecock": 2})
    assert q.equipment_paid == P["racket"] + P["shoes"] + P["shuttlecock"] * 2
    assert q.equipment_free_value == 0


def test_pro_first_racket_and_shoes_free():
    q = pricing.quote_booking(1, True, {"racket": 1, "shoes": 1})
    assert q.equipment_paid == 0
    assert q.equipment_free_value == P["racket"] + P["shoes"]
    assert q.total == PRO_SLOT


def test_pro_shuttlecocks_always_charged():
    q = pricing.quote_booking(1, True, {"racket": 1, "shoes": 1, "shuttlecock": 1})
    assert q.equipment_fees["shuttlecock"] == P["shuttlecock"]
    assert q.equipment_paid == P["shuttlecock"]


def test_pro_extras_beyond_first_set_charged():
    q = pricing.quote_booking(1, True, {"racket": 3, "shoes": 2})
    assert q.equipment_fees == {"racket": P["racket"] * 2, "shoes": P["shoes"]}


def test_equipment_is_per_booking_not_per_slot():
    one = pricing.quote_booking(1, False, {"racket": 1})
    four = pricing.quote_booking(4, False, {"racket": 1})
    assert one.equipment_paid == four.equipment_paid


def test_equipment_max_quantity():
    ok = {"racket": settings.EQUIPMENT_MAX_QTY}
    assert pricing.quote_booking(1, False, ok).equipment_paid == P["racket"] * settings.EQUIPMENT_MAX_QTY
    with pytest.raises(ValueError):
        pricing.quote_booking(1, False, {"racket": settings.EQUIPMENT_MAX_QTY + 1})


@pytest.mark.parametrize("bad", [{"towel": 1}, {"racket": -1}, {"racket": 1.5}, {"racket": True}])
def test_equipment_invalid_rejected(bad):
    with pytest.raises(ValueError):
        pricing.quote_booking(1, False, bad)


def test_zero_quantity_ignored():
    assert pricing.quote_booking(1, False, {"racket": 0}).equipment_fees == {}


# --- credits ---
def test_credits_zero_court_fee_for_those_slots():
    q = pricing.quote_booking(2, False, credits_to_use=2)
    assert q.court_paid == 0 and q.total == 0
    assert q.credit_discount == BASE * 2


def test_mixed_credit_and_paid_slots():
    q = pricing.quote_booking(4, False, credits_to_use=2)
    assert q.court_paid == BASE * 2
    assert q.total == BASE * 2


def test_mixed_credit_and_pro_discount():
    q = pricing.quote_booking(3, True, credits_to_use=1)
    assert q.court_paid == PRO_SLOT * 2
    assert q.discount_amount == BASE + (BASE * 2 - PRO_SLOT * 2)


def test_credits_capped_per_booking():
    with pytest.raises(ValueError):
        pricing.quote_booking(5, False, credits_to_use=settings.CREDIT_MAX_SLOTS_PER_BOOKING + 1)


def test_credits_cannot_exceed_slots_or_be_negative():
    with pytest.raises(ValueError):
        pricing.quote_booking(1, False, credits_to_use=2)
    with pytest.raises(ValueError):
        pricing.quote_booking(1, False, credits_to_use=-1)


def test_credits_do_not_discount_equipment():
    q = pricing.quote_booking(1, False, {"racket": 1}, credits_to_use=1)
    assert q.total == P["racket"]


def test_total_never_negative_and_bounds():
    q = pricing.quote_booking(1, True, {"racket": 1, "shoes": 1}, credits_to_use=1)
    assert q.total == 0
    with pytest.raises(ValueError):
        pricing.quote_booking(0, False)
    with pytest.raises(ValueError):
        pricing.quote_booking(settings.HOLD_MAX_SLOTS + 1, False)
    assert pricing.quote_booking(settings.HOLD_MAX_SLOTS, False).total == BASE * settings.HOLD_MAX_SLOTS


def test_total_matches_formula_for_pro():
    q = pricing.quote_booking(3, True, {"racket": 2, "shuttlecock": 1})
    assert q.total == PRO_SLOT * 3 + P["racket"] + P["shuttlecock"]


# --- tier expiry ---
def test_is_pro_active_checks_expiry():
    assert pricing.is_pro_active("pro", NOW + timedelta(seconds=1), NOW)
    assert not pricing.is_pro_active("pro", NOW, NOW)
    assert not pricing.is_pro_active("pro", None, NOW)
    assert not pricing.is_pro_active("free", NOW + timedelta(days=5), NOW)


# --- cancellation ---
def _cancel(hours, is_pro=False, court=BASE * 2, equip=D("100"), credits=0):
    return pricing.cancellation_terms(is_pro, NOW + timedelta(hours=hours), NOW, court, equip, credits)


def test_free_cancel_at_25h_is_free():
    r = _cancel(25)
    assert not r.late and r.fee == 0
    assert r.refund == BASE * 2 + 100


def test_free_cancel_at_23h_charges_half_court_fee():
    r = _cancel(23)
    assert r.late
    assert r.fee == BASE * 2 * settings.LATE_CANCEL_FEE_RATE
    assert r.refund == BASE * 2 + 100 - r.fee


def test_free_cancel_exactly_24h_is_late():
    assert _cancel(settings.FREE_CANCEL_HOURS).late
    assert not pricing.cancellation_terms(
        False, NOW + timedelta(hours=settings.FREE_CANCEL_HOURS, seconds=1), NOW, BASE
    ).late


def test_pro_cancel_always_free():
    for hours in (100, 23, 1, 0):
        r = _cancel(hours, is_pro=True)
        assert not r.late and r.fee == 0 and r.refund == BASE * 2 + 100


def test_equipment_fully_refunded_on_late_cancel():
    r = _cancel(1, court=D("0"), equip=D("160"))
    assert r.fee == 0 and r.refund == 160


def test_late_fee_based_on_court_fee_actually_paid():
    # 1 credit slot + 1 paid slot: the fee is 50% of the single paid slot
    q = pricing.quote_booking(2, False, credits_to_use=1)
    r = pricing.cancellation_terms(False, NOW + timedelta(hours=2), NOW, q.court_paid, q.equipment_paid, 1)
    assert r.fee == BASE * settings.LATE_CANCEL_FEE_RATE
    assert r.refund == q.total - r.fee


def test_credit_restored_on_free_cancel_forfeited_on_late():
    free = _cancel(48, court=D("0"), credits=2)
    assert (free.credits_restored, free.credits_forfeited) == (2, 0)
    late = _cancel(3, court=D("0"), credits=2)
    assert (late.credits_restored, late.credits_forfeited) == (0, 2)


def test_pro_cancel_restores_credits_even_when_close():
    r = _cancel(1, is_pro=True, court=D("0"), credits=1)
    assert r.credits_restored == 1 and r.credits_forfeited == 0


# --- loyalty ---
STEP = settings.LOYALTY_SLOTS_PER_REWARD
REWARD = settings.LOYALTY_CREDITS_PER_REWARD


def test_loyalty_no_crossing():
    assert pricing.loyalty_award(0, STEP - 1) == (STEP - 1, 0)


def test_loyalty_exact_threshold():
    assert pricing.loyalty_award(STEP - 2, 2) == (STEP, REWARD)


def test_loyalty_crossing_from_below():
    assert pricing.loyalty_award(STEP - 1, 3) == (STEP + 2, REWARD)


def test_loyalty_multiple_thresholds_in_one_jump():
    assert pricing.loyalty_award(STEP - 1, STEP * 2 + 1) == (STEP * 3, REWARD * 3)


def test_loyalty_already_past_threshold_no_regrant():
    assert pricing.loyalty_award(STEP, 1) == (STEP + 1, 0)


def test_loyalty_zero_and_invalid():
    assert pricing.loyalty_award(5, 0) == (5, 0)
    with pytest.raises(ValueError):
        pricing.loyalty_award(-1, 1)
    with pytest.raises(ValueError):
        pricing.loyalty_award(0, -1)


# --- settings ---
def test_peak_pro_only_courts():
    assert settings.PEAK_PRO_ONLY_COURTS == tuple(range(11, 17))
    assert settings.HOLD_MAX_SLOTS == 8 and settings.EQUIPMENT_MAX_QTY == 4
