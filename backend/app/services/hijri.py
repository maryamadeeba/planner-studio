"""Hijri (Umm al-Qura) helpers built on the `hijridate` package.

The *offset* setting (-2..+2) shifts every Hijri date to match local moon
sighting.  Definition used everywhere in the app:

    local_hijri(gregorian_day) == umm_al_qura(gregorian_day + offset days)

So in a country that usually starts months one day *after* Saudi Arabia
(e.g. Pakistan) you would use offset = -1.
"""
from __future__ import annotations

from datetime import date, timedelta

from hijridate import Gregorian, Hijri

HIJRI_MONTHS_EN = [
    "Muharram", "Safar", "Rabi al-Awwal", "Rabi al-Thani", "Jumada al-Awwal",
    "Jumada al-Thani", "Rajab", "Sha'ban", "Ramadan", "Shawwal",
    "Dhul Qa'dah", "Dhul Hijjah",
]
HIJRI_MONTHS_SHORT = ["Muh", "Saf", "R.Aw", "R.Th", "J.Aw", "J.Th", "Raj", "Sha", "Ram", "Shw", "DhQ", "DhH"]
# Standard Arabic month names (with tashkeel) – these are calendar names, not Quranic text.
HIJRI_MONTHS_AR = [
    "مُحَرَّم", "صَفَر", "رَبِيع الأَوَّل", "رَبِيع الآخِر", "جُمَادَى الأُولَى",
    "جُمَادَى الآخِرَة", "رَجَب", "شَعْبَان", "رَمَضَان", "شَوَّال",
    "ذُو القَعْدَة", "ذُو الحِجَّة",
]

# Hijri months that overlap the supported Gregorian range 2026-01-01 .. 2040-12-31
HIJRI_MIN = (1447, 7)   # Rajab 1447 contains 1 Jan 2026
HIJRI_MAX = (1462, 12)  # Dhul Hijjah 1462 contains 31 Dec 2040

VALID_OFFSETS = (-2, -1, 0, 1, 2)


def _check_offset(offset: int) -> int:
    offset = int(offset or 0)
    if offset not in VALID_OFFSETS:
        raise ValueError(f"Hijri offset must be one of {VALID_OFFSETS}, got {offset}")
    return offset


def to_hijri(g: date, offset: int = 0) -> tuple[int, int, int]:
    """Gregorian date -> local Hijri (year, month, day)."""
    offset = _check_offset(offset)
    h = Gregorian.fromdate(g + timedelta(days=offset)).to_hijri()
    return h.year, h.month, h.day


def month_start(hy: int, hm: int, offset: int = 0) -> date:
    """Gregorian date on which local Hijri month (hy, hm) begins."""
    offset = _check_offset(offset)
    return Hijri(hy, hm, 1).to_gregorian() - timedelta(days=offset)


def month_length(hy: int, hm: int) -> int:
    return Hijri(hy, hm, 1).month_length()


def to_gregorian(hy: int, hm: int, hd: int, offset: int = 0) -> date:
    return month_start(hy, hm, offset) + timedelta(days=hd - 1)


def iter_months(start: tuple[int, int], end: tuple[int, int]):
    y, m = start
    while (y, m) <= end:
        yield y, m
        m += 1
        if m > 12:
            y, m = y + 1, 1


def clamp_range(start: tuple[int, int], end: tuple[int, int]):
    start = max(tuple(start), HIJRI_MIN)
    end = min(tuple(end), HIJRI_MAX)
    if start > end:
        raise ValueError("Hijri start month must be before end month")
    return start, end


# ---------------------------------------------------------------- events
ISLAMIC_EVENTS = [
    # key, label, month, day(s)
    ("new_year", "Islamic New Year", 1, [1]),
    ("ashura", "Ashura", 1, [10]),
    ("ramadan_start", "Ramadan begins", 9, [1]),
    ("last_ten", "Last Ten Nights", 9, list(range(21, 30))),
    ("eid_fitr", "Eid al-Fitr", 10, [1]),
    ("arafah", "Day of Arafah", 12, [9]),
    ("eid_adha", "Eid al-Adha", 12, [10]),
]
EVENT_LABELS = {k: lbl for k, lbl, _, _ in ISLAMIC_EVENTS}


def events_for(hm: int, hd: int, enabled: dict | None, custom: list | None = None) -> list[dict]:
    """Islamic events falling on local Hijri month/day."""
    enabled = enabled or {}
    out = []
    for key, label, m, days in ISLAMIC_EVENTS:
        if not enabled.get(key, True) or m != hm or hd not in days:
            continue
        if key == "last_ten":
            odd = hd % 2 == 1
            out.append({"key": key, "name": f"Night {hd}" + (" ★" if odd else ""), "highlight": odd, "kind": "islamic"})
        else:
            out.append({"key": key, "name": label, "highlight": True, "kind": "islamic"})
    for ev in custom or []:
        try:
            if int(ev.get("month")) == hm and int(ev.get("day")) == hd and ev.get("name"):
                out.append({"key": "custom", "name": ev["name"], "highlight": False, "kind": "custom"})
        except (TypeError, ValueError):
            continue
    return out
