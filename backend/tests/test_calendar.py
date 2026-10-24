"""Calendar + Hijri engine tests.  Run:  backend\\.venv\\Scripts\\python -m pytest backend/tests"""
from datetime import date, timedelta

import pytest

from app.services import hijri as H
from app.services.calendar import CalendarEngine, is_leap


def greg(start_year=2026, end_year=2026, **kw):
    cfg = {"mode": "gregorian", "start_year": start_year, "start_month": 1, "end_year": end_year, "end_month": 12}
    cfg.update(kw)
    return CalendarEngine(cfg)


def hij(sy, sm, ey, em, offset=0, **kw):
    cfg = {"mode": "hijri", "start_year": sy, "start_month": sm, "end_year": ey, "end_month": em, "hijri_offset": offset}
    cfg.update(kw)
    return CalendarEngine(cfg)


# ------------------------------------------------------------ Gregorian
@pytest.mark.parametrize("year", range(2026, 2041))
def test_leap_years(year):
    eng = greg(year, year)
    feb = eng.month(year, 2)
    expected_leap = year in (2028, 2032, 2036, 2040)
    assert is_leap(year) == expected_leap
    assert len(feb.days) == (29 if expected_leap else 28)
    assert sum(len(m.days) for m in eng.months()) == (366 if expected_leap else 365)


@pytest.mark.parametrize("year", range(2026, 2041))
def test_monday_start_grid(year):
    eng = greg(year, year)
    for m in eng.months():
        grid = m.grid
        for row in grid:
            assert len(row) == 7
            for col, cell in enumerate(row):
                if cell is not None:
                    assert cell.weekday == col  # column 0 is always Monday
        flat = [c for r in grid for c in r if c is not None]
        assert [d.day for d in flat] == list(range(1, len(m.days) + 1))


def test_known_weekdays():
    eng = greg(2026, 2040)
    assert eng.month(2026, 1).days[0].weekday_name == "Thursday"
    assert eng.month(2026, 1).grid[0][3].day == 1
    assert eng.month(2040, 12).days[-1].weekday_name == "Monday"
    assert eng.month(2028, 2).days[28].g == date(2028, 2, 29)


def test_weeks_cover_range_and_start_monday():
    eng = greg(2026, 2040)
    weeks = eng.weeks()
    days = eng.all_days()
    assert len(days) == sum(366 if is_leap(y) else 365 for y in range(2026, 2041))
    covered = [d.g for w in weeks for d, ok in zip(w.days, w.in_range) if ok]
    assert covered == [d.g for d in days]
    for w in weeks:
        assert w.monday.weekday() == 0
        assert len(w.days) == 7


def test_iso_weeks_2026_has_53():
    eng = greg(2026, 2026)
    assert max(d.iso_week for d in eng.all_days() if d.g.isocalendar()[0] == 2026) == 53


def test_year_range_validation():
    with pytest.raises(ValueError):
        greg(2025, 2026)
    with pytest.raises(ValueError):
        greg(2026, 2041)


def test_custom_holiday():
    eng = greg(2026, 2027, gregorian_holidays=[{"month": 8, "day": 14, "name": "Independence Day"},
                                              {"month": 3, "day": 5, "year": 2027, "name": "Once"}])
    assert eng.month(2026, 8).days[13].events[0]["name"] == "Independence Day"
    assert not eng.month(2026, 3).days[4].events
    assert eng.month(2027, 3).days[4].events[0]["name"] == "Once"


# ---------------------------------------------------------------- Hijri
def test_known_hijri_anchors():
    # Umm al-Qura reference dates
    assert H.month_start(1447, 9) == date(2026, 2, 18)   # 1 Ramadan 1447
    assert H.month_start(1448, 1) == date(2026, 6, 16)   # 1 Muharram 1448
    assert H.to_hijri(date(2026, 1, 1)) == (1447, 7, 12)


def test_hijri_roundtrip_full_range():
    g = date(2026, 1, 1)
    prev = None
    while g <= date(2040, 12, 31):
        y, m, d = H.to_hijri(g)
        assert H.to_gregorian(y, m, d) == g
        if prev:
            py, pm, pd = prev
            if d == 1:  # new month starts after a 29 or 30 day month
                assert pd in (29, 30)
                assert (y, m) == ((py, pm + 1) if pm < 12 else (py + 1, 1))
            else:
                assert (y, m, d) == (py, pm, pd + 1)
        prev = (y, m, d)
        g += timedelta(days=1)


@pytest.mark.parametrize("offset", [-2, -1, 0, 1, 2])
def test_hijri_offset(offset):
    base = H.to_gregorian(1448, 9, 1, 0)
    assert H.to_gregorian(1448, 9, 1, offset) == base - timedelta(days=offset)
    assert H.to_hijri(base - timedelta(days=offset), offset) == (1448, 9, 1)


def test_invalid_offset():
    with pytest.raises(ValueError):
        H.to_hijri(date(2026, 1, 1), 3)


def test_hijri_months_contiguous_full_range():
    eng = hij(1447, 1, 1462, 12)
    assert eng.start == (1447, 7) and eng.end == (1462, 12)
    months = eng.months()
    assert len(months) == 6 + 15 * 12
    for a, b in zip(months, months[1:]):
        assert len(a.days) in (29, 30)
        assert b.days[0].g == a.days[-1].g + timedelta(days=1)
        assert b.days[0].day == 1
    for m in months:
        for row in m.grid:
            for col, c in enumerate(row):
                if c:
                    assert c.weekday == col
    assert months[0].days[0].g <= date(2026, 1, 1)
    assert months[-1].days[-1].g >= date(2040, 12, 31)


def test_hijri_mode_hides_gregorian():
    eng = hij(1448, 9, 1448, 9)
    d = eng.month(1448, 9).days[0]
    assert d.mode == "hijri" and d.day == 1 and d.month_name == "Ramadan"
    assert "AH" in d.label and str(d.g.year) not in d.label.replace("1448", "")


def test_islamic_events_and_toggles():
    eng = hij(1448, 1, 1448, 12)
    def names(m, d):
        return [e["name"] for e in eng.month(1448, m).days[d - 1].events]
    assert "Islamic New Year" in names(1, 1)
    assert "Ashura" in names(1, 10)
    assert "Ramadan begins" in names(9, 1)
    assert "Eid al-Fitr" in names(10, 1)
    assert "Day of Arafah" in names(12, 9)
    assert "Eid al-Adha" in names(12, 10)
    ten = [e for d in eng.month(1448, 9).days[20:29] for e in d.events]
    assert len(ten) == 9
    assert [e["highlight"] for e in ten] == [True, False] * 4 + [True]  # odd nights 21,23,25,27,29
    off = hij(1448, 1, 1448, 12, events={"ashura": False}, custom_hijri_events=[{"month": 3, "day": 12, "name": "Custom"}])
    assert not off.month(1448, 1).days[9].events
    assert off.month(1448, 3).days[11].events[0]["name"] == "Custom"


def test_offset_shifts_events():
    a = hij(1448, 9, 1448, 9, offset=0).month(1448, 9).days[0].g
    b = hij(1448, 9, 1448, 9, offset=-1).month(1448, 9).days[0].g
    assert b == a + timedelta(days=1)
