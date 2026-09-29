from datetime import timedelta

import pytest

import clock


def test_parse_offset():
    assert clock.parse_offset("") == timedelta()
    assert clock.parse_offset("+2h") == timedelta(hours=2)
    assert clock.parse_offset("-30m") == timedelta(minutes=-30)
    assert clock.parse_offset("+1d") == timedelta(days=1)


def test_parse_offset_invalid():
    with pytest.raises(ValueError):
        clock.parse_offset("2 hours")


def test_now_respects_offset(monkeypatch):
    monkeypatch.setenv("CLOCK_OFFSET", "")
    base = clock.now()
    monkeypatch.setenv("CLOCK_OFFSET", "+1d")
    assert clock.now() - base >= timedelta(hours=23, minutes=59)
