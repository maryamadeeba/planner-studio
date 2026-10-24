"""Calendar engine: Gregorian and Hijri modes, Monday-start weeks.

The two modes are never mixed on a page: every Day carries the *display*
numbers for the active mode only (Gregorian day number in Gregorian mode,
Hijri day number in Hijri mode).  The underlying Gregorian date is kept
internally only for weekday maths and stable page ids.
"""
from __future__ import annotations

import calendar as _pycal
from dataclasses import dataclass, field
from datetime import date, timedelta

from . import hijri as H

MIN_YEAR, MAX_YEAR = 2026, 2040
GREG_MONTHS = list(_pycal.month_name)[1:]
GREG_MONTHS_SHORT = list(_pycal.month_abbr)[1:]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
WEEKDAYS_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
WEEKDAYS_LETTER = ["M", "T", "W", "T", "F", "S", "S"]


@dataclass
class Day:
    g: date                      # internal gregorian date (not printed in Hijri mode)
    mode: str
    year: int                    # display year (AD or AH)
    month: int
    day: int
    month_name: str
    events: list = field(default_factory=list)

    @property
    def id(self) -> str:
        return f"d-{self.g.isoformat()}"

    @property
    def weekday(self) -> int:
        return self.g.weekday()  # 0 = Monday

    @property
    def weekday_name(self) -> str:
        return WEEKDAYS[self.weekday]

    @property
    def iso_week(self) -> int:
        return self.g.isocalendar()[1]

    @property
    def month_key(self) -> str:
        return month_key(self.mode, self.year, self.month)

    @property
    def undated(self) -> bool:
        return self.mode == "undated"

    @property
    def label(self) -> str:
        if self.undated:
            return self.weekday_name
        suffix = " AH" if self.mode == "hijri" else ""
        return f"{self.weekday_name}, {self.day} {self.month_name} {self.year}{suffix}"

    @property
    def short_label(self) -> str:
        return f"{self.day} {self.month_name}"


@dataclass
class Month:
    mode: str
    year: int
    month: int
    name: str
    short: str
    name_ar: str
    days: list

    @property
    def key(self) -> str:
        return month_key(self.mode, self.year, self.month)

    @property
    def quarter(self) -> int:
        return (self.month - 1) // 3 + 1

    @property
    def undated(self) -> bool:
        return self.mode == "undated"

    @property
    def title(self) -> str:
        if self.undated:
            return f"Month {self.month}"
        return f"{self.name} {self.year}" + (" AH" if self.mode == "hijri" else "")

    @property
    def grid(self) -> list[list]:
        """Monday-start rows of 7; None for padding cells.  Undated months are 6 blank rows."""
        if self.undated:
            return [[None] * 7 for _ in range(6)]
        lead = self.days[0].weekday
        cells = [None] * lead + list(self.days)
        while len(cells) % 7:
            cells.append(None)
        return [cells[i:i + 7] for i in range(0, len(cells), 7)]


@dataclass
class Week:
    days: list            # 7 Day objects, Monday..Sunday
    in_range: list        # 7 bools

    @property
    def monday(self) -> date:
        return self.days[0].g

    @property
    def id(self) -> str:
        return f"w-{self.monday.isoformat()}"

    @property
    def iso_week(self) -> int:
        return self.monday.isocalendar()[1]

    @property
    def undated(self) -> bool:
        return self.days[0].undated

    @property
    def label(self) -> str:
        a, b = self.days[0], self.days[-1]
        if self.undated:
            return "Week of ____"
        sfx = " AH" if a.mode == "hijri" else ""
        if a.month == b.month:
            return f"{a.day} – {b.day} {a.month_name} {b.year}{sfx}"
        if a.year == b.year:
            return f"{a.day} {a.month_name} – {b.day} {b.month_name} {b.year}{sfx}"
        return f"{a.day} {a.month_name} {a.year} – {b.day} {b.month_name} {b.year}{sfx}"


def month_key(mode: str, year: int, month: int) -> str:
    if mode == "undated":
        return f"m-u{month:02d}"
    return f"m-{'h' if mode == 'hijri' else 'g'}{year}-{month:02d}"


def year_key(mode: str, year: int) -> str:
    if mode == "undated":
        return "y-u"
    return f"y-{'h' if mode == 'hijri' else 'g'}{year}"


# ------------------------------------------------------------------ periods
PERIODS = ("year", "quarter", "month", "week", "custom")
SHORT_PERIODS = ("quarter", "month", "week", "custom")
MAX_CUSTOM_DAYS = 366


def _parse_date(v, what: str) -> date:
    if isinstance(v, date):
        return v
    try:
        return date.fromisoformat(str(v)[:10])
    except (TypeError, ValueError):
        raise ValueError(f"Please pick a valid {what}.")


def period_of(cal_cfg: dict) -> str:
    p = cal_cfg.get("period") or "year"
    return p if p in PERIODS else "year"


def period_bounds(cal_cfg: dict, mode: str, offset: int):
    """(start month, end month, day clip or None) for a short period.

    Month / quarter periods use whole months of the active calendar; week and custom
    periods are clipped to exact days (dates are entered as Gregorian ISO dates)."""
    period = period_of(cal_cfg)
    if period in ("month", "quarter"):
        y = int(cal_cfg.get("period_year") or cal_cfg.get("start_year"))
        if period == "month":
            m = int(cal_cfg.get("period_month") or 1)
            return (y, m), (y, m), None
        q = max(1, min(4, int(cal_cfg.get("period_quarter") or 1)))
        return (y, q * 3 - 2), (y, q * 3), None
    if period == "week":
        d = _parse_date(cal_cfg.get("week_start"), "week")
        a = d - timedelta(days=d.weekday())
        b = a + timedelta(days=6)
    else:
        a = _parse_date(cal_cfg.get("range_start"), "start date")
        b = _parse_date(cal_cfg.get("range_end"), "end date")
        if a > b:
            raise ValueError("The custom range ends before it starts.")
        if (b - a).days >= MAX_CUSTOM_DAYS:
            raise ValueError("A custom date range can be at most one year – use 'Full year' for longer planners.")
    if mode == "hijri":
        sa, sb = H.to_hijri(a, offset)[:2], H.to_hijri(b, offset)[:2]
    else:
        sa, sb = (a.year, a.month), (b.year, b.month)
    return sa, sb, (a, b)


# ------------------------------------------------------------------ factory
class CalendarEngine:
    """Builds months/days/weeks for one planner configuration."""

    def __init__(self, cal_cfg: dict):
        self.mode = cal_cfg.get("mode", "gregorian")
        self.offset = int(cal_cfg.get("hijri_offset", 0) or 0)
        H._check_offset(self.offset)
        self.event_toggles = cal_cfg.get("events", {}) or {}
        self.custom_hijri = cal_cfg.get("custom_hijri_events", []) or []
        self.holidays = cal_cfg.get("gregorian_holidays", []) or []
        self.period = period_of(cal_cfg)
        self.clip = None  # (first, last) Gregorian dates for week / custom periods
        if self.period == "year":
            start = (int(cal_cfg["start_year"]), int(cal_cfg.get("start_month", 1)))
            end = (int(cal_cfg["end_year"]), int(cal_cfg.get("end_month", 12)))
        else:
            start, end, self.clip = period_bounds(cal_cfg, self.mode, self.offset)
        if self.mode == "hijri":
            self.start, self.end = H.clamp_range(start, end)
        else:
            if not (MIN_YEAR <= start[0] <= MAX_YEAR and MIN_YEAR <= end[0] <= MAX_YEAR):
                raise ValueError(f"Years must be between {MIN_YEAR} and {MAX_YEAR}")
            if start > end:
                raise ValueError("Start month must be before end month")
            self.start, self.end = start, end
        self._month_cache: dict = {}

    # ---------------------------------------------------------------- days
    def make_day(self, g: date) -> Day:
        if self.mode == "hijri":
            y, m, d = H.to_hijri(g, self.offset)
            ev = H.events_for(m, d, self.event_toggles, self.custom_hijri)
            return Day(g, "hijri", y, m, d, H.HIJRI_MONTHS_EN[m - 1], ev)
        ev = []
        for h in self.holidays:
            try:
                if int(h.get("month")) == g.month and int(h.get("day")) == g.day and h.get("name"):
                    if not h.get("year") or int(h["year"]) == g.year:
                        ev.append({"key": "holiday", "name": h["name"], "highlight": True, "kind": "holiday"})
            except (TypeError, ValueError):
                continue
        return Day(g, "gregorian", g.year, g.month, g.day, GREG_MONTHS[g.month - 1], ev)

    # -------------------------------------------------------------- months
    def month(self, year: int, mon: int) -> Month:
        key = (year, mon)
        if key in self._month_cache:
            return self._month_cache[key]
        if self.mode == "hijri":
            start = H.month_start(year, mon, self.offset)
            n = H.month_length(year, mon)
            days = [self.make_day(start + timedelta(days=i)) for i in range(n)]
            m = Month("hijri", year, mon, H.HIJRI_MONTHS_EN[mon - 1], H.HIJRI_MONTHS_SHORT[mon - 1],
                      H.HIJRI_MONTHS_AR[mon - 1], days)
        else:
            n = _pycal.monthrange(year, mon)[1]
            days = [self.make_day(date(year, mon, i + 1)) for i in range(n)]
            m = Month("gregorian", year, mon, GREG_MONTHS[mon - 1], GREG_MONTHS_SHORT[mon - 1], "", days)
        self._month_cache[key] = m
        return m

    def months(self) -> list[Month]:
        out = []
        y, m = self.start
        while (y, m) <= self.end:
            out.append(self.month(y, m))
            m += 1
            if m > 12:
                y, m = y + 1, 1
        return out

    def years(self) -> list[int]:
        return list(range(self.start[0], self.end[0] + 1))

    def in_range(self, year: int, mon: int) -> bool:
        return self.start <= (year, mon) <= self.end

    def day_in_range(self, d: Day) -> bool:
        return self.in_range(d.year, d.month) and (not self.clip or self.clip[0] <= d.g <= self.clip[1])

    def all_days(self) -> list[Day]:
        return [d for m in self.months() for d in m.days if not self.clip or self.clip[0] <= d.g <= self.clip[1]]

    # --------------------------------------------------------------- weeks
    def weeks(self) -> list[Week]:
        days = self.all_days()
        if not days:
            return []
        first, last = days[0].g, days[-1].g
        valid = {d.g for d in days}
        monday = first - timedelta(days=first.weekday())
        out = []
        while monday <= last:
            gs = [monday + timedelta(days=i) for i in range(7)]
            out.append(Week([self.make_day(g) for g in gs], [g in valid for g in gs]))
            monday += timedelta(days=7)
        return out

    def year_title(self, year: int) -> str:
        return f"{year} AH" if self.mode == "hijri" else str(year)

    def month_names_short(self) -> list[str]:
        return H.HIJRI_MONTHS_SHORT if self.mode == "hijri" else GREG_MONTHS_SHORT

    def weekday_header(self) -> list[str]:
        return WEEKDAYS_SHORT

    def period_label(self) -> str:
        """Human label for a short period ('November 2026', 'Q4 2026', '23 – 29 November 2026')."""
        months = self.months()
        if self.period == "month":
            return months[0].title
        if self.period == "quarter":
            return f"Q{months[0].quarter} {self.year_title(months[0].year)}"
        if self.period == "week":
            return self.weeks()[0].label
        if self.period == "custom":
            a, b = self.make_day(self.clip[0]), self.make_day(self.clip[1])
            sfx = " AH" if self.mode == "hijri" else ""
            if a.year == b.year:
                return f"{a.day} {a.month_name} – {b.day} {b.month_name} {b.year}{sfx}"
            return f"{a.day} {a.month_name} {a.year} – {b.day} {b.month_name} {b.year}{sfx}"
        ys = self.years()
        sfx = " AH" if self.mode == "hijri" else ""
        return f"{ys[0]}{sfx}" if len(ys) == 1 else f"{ys[0]} – {ys[-1]}{sfx}"


# ------------------------------------------------------------------ undated
UNDATED_BASE = date(1900, 1, 1)   # a Monday; synthetic dates only give undated pages stable, unique ids
UNDATED_WEEKS_PER_MONTH = 5
UNDATED_MONTH_DAYS = 31


class UndatedEngine:
    """Same interface as CalendarEngine, but every month / week / day is a blank, reusable slot.

    Months are numbered slots (Month 1, Month 2 …) with 31 day columns for trackers, each month
    owns five 'Week of ____' slots, and each week has seven weekday-headed day slots."""

    mode = "undated"
    offset = 0

    def __init__(self, cal_cfg: dict):
        self.period = period_of(cal_cfg)
        if self.period == "custom":
            n = len(CalendarEngine({**cal_cfg, "dated": True}).months())
        else:
            n = {"year": 12, "quarter": 3, "month": 1, "week": 1}[self.period]
        self.n_months = max(1, min(12, n))
        self.start, self.end = (1, 1), (1, self.n_months)
        self.clip = None
        self._months = [self._make_month(i) for i in range(1, self.n_months + 1)]
        n_weeks = 1 if self.period == "week" else self.n_months * UNDATED_WEEKS_PER_MONTH
        self._weeks = []
        for k in range(n_weeks):
            slot = 1 if self.period == "week" else k // UNDATED_WEEKS_PER_MONTH + 1
            monday = UNDATED_BASE + timedelta(days=7 * k)
            self._weeks.append(Week([Day(monday + timedelta(days=i), "undated", 1, slot, 0, "") for i in range(7)],
                                    [True] * 7))

    def _make_month(self, i: int) -> Month:
        first = UNDATED_BASE + timedelta(days=4000 + 40 * i)  # disjoint from the week slots
        days = [Day(first + timedelta(days=j), "undated", 1, i, j + 1, "") for j in range(UNDATED_MONTH_DAYS)]
        return Month("undated", 1, i, "", f"M{i}", "", days)

    def month(self, year: int, mon: int) -> Month:
        return self._months[mon - 1] if 1 <= mon <= self.n_months else self._make_month(mon)

    def months(self) -> list[Month]:
        return list(self._months)

    def weeks(self) -> list[Week]:
        return list(self._weeks)

    def years(self) -> list[int]:
        return [1]

    def in_range(self, year: int, mon: int) -> bool:
        return 1 <= mon <= self.n_months

    def day_in_range(self, d: Day) -> bool:
        return True

    def all_days(self) -> list[Day]:
        return [d for w in self._weeks for d in w.days]

    def year_title(self, year: int) -> str:
        return "Undated"

    def month_names_short(self) -> list[str]:
        return [f"M{i}" for i in range(1, 13)]

    def weekday_header(self) -> list[str]:
        return WEEKDAYS_SHORT

    def period_label(self) -> str:
        return ""


def is_dated(cal_cfg: dict) -> bool:
    return cal_cfg.get("dated", True) is not False


def make_engine(cal_cfg: dict):
    return CalendarEngine(cal_cfg) if is_dated(cal_cfg) else UndatedEngine(cal_cfg)


def is_leap(year: int) -> bool:
    return _pycal.isleap(year)
