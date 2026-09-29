"""Injectable clock so hold expiry and the 24h cancellation rule are testable.

Always call clock.now() instead of datetime.now(). In dev, set CLOCK_OFFSET in
.env (e.g. "+2h", "-30m", "+1d") to shift time without waiting.
"""
import os
import re
from datetime import datetime, timedelta, timezone

_UNITS = {"m": "minutes", "h": "hours", "d": "days"}
_PATTERN = re.compile(r"^([+-])(\d+)([mhd])$")


def parse_offset(value: str) -> timedelta:
    value = (value or "").strip()
    if not value:
        return timedelta()
    match = _PATTERN.match(value)
    if not match:
        raise ValueError(f"Invalid CLOCK_OFFSET {value!r}; use e.g. +2h, -30m, +1d")
    sign, amount, unit = match.groups()
    delta = timedelta(**{_UNITS[unit]: int(amount)})
    return delta if sign == "+" else -delta


def now() -> datetime:
    return datetime.now(timezone.utc) + parse_offset(os.getenv("CLOCK_OFFSET", ""))
