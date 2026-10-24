"""Turns a project config into an ordered list of pages + navigation targets."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from . import hijri as H
from .calendar import SHORT_PERIODS, WEEKDAYS_SHORT, CalendarEngine, is_dated, make_engine, year_key
from .catalog import MODULES, SURAHS, effective_modules, normalize

CAL_MODULES = [k for k, v in MODULES.items() if v.get("calendar")]


@dataclass
class Page:
    id: str
    kind: str
    title: str
    data: dict = field(default_factory=dict)
    year: int | None = None
    parent: str | None = None
    group: str = ""


@dataclass
class Plan:
    cfg: dict
    engine: CalendarEngine
    pages: list
    targets: dict              # year -> {"year": id, "q": {1..4: id}, "m": {1..12: id}}
    sections: list             # [(label, target_id)] for index + top chips
    day_target: dict           # day.id -> page id
    home: str | None
    ramadan: dict | None = None
    duas: list = field(default_factory=list)
    short: bool = False        # single month / quarter / week / custom range
    tabs: list = field(default_factory=list)  # short periods: [(label, target_id, ids of pages it covers)]
    quote_of: dict = field(default_factory=dict)  # page id -> quote dict

    @property
    def undated(self) -> bool:
        return self.engine.mode == "undated"

    def index_of(self) -> dict:
        return {p.id: i for i, p in enumerate(self.pages)}


def _chunks(seq, n):
    return [seq[i:i + n] for i in range(0, len(seq), n)] or [[]]


def find_ramadan(eng: CalendarEngine, cal: dict) -> dict:
    if eng.mode == "undated":
        days = [{"n": i + 1, "label": "Date: ____", "odd_last": i >= 20 and (i + 1) % 2 == 1, "last_ten": 20 <= i <= 28}
                for i in range(30)]
        return {"hijri_year": None, "days": days, "year_label": ""}
    off = eng.offset
    if cal.get("ramadan_year"):
        hy = int(cal["ramadan_year"])
    else:
        days = eng.all_days()
        first = days[0].g if days else date(2027, 1, 1)
        hy = H.to_hijri(first, off)[0]
        if H.month_start(hy, 9, off) < first:
            hy += 1
    hy = max(1447, min(hy, 1462))
    start = H.month_start(hy, 9, off)
    n = H.month_length(hy, 9)
    days = []
    for i in range(30):
        g = start + timedelta(days=i)
        exists = i < n
        if eng.mode == "hijri":
            lbl = f"{i + 1} Ramadan {hy} AH" if exists else f"Day 30 (if observed)"
        else:
            lbl = g.strftime("%a %d %b %Y") if exists else "Day 30 (if observed)"
        days.append({"n": i + 1, "label": lbl, "odd_last": i >= 20 and (i + 1) % 2 == 1, "last_ten": 20 <= i <= 28})
    year_lbl = f"{hy} AH" if eng.mode == "hijri" else str(start.year)
    return {"hijri_year": hy, "days": days, "year_label": year_lbl}


QUOTE_KINDS = ["cover", "month", "week", "day", "divider"]


def assign_quotes(cfg: dict, pages: list, quotes: list) -> dict:
    """page id -> quote.  'per_type': one quote for each page type; 'per_page': a new quote on every page
    (cycling through the library before any repeats)."""
    q = cfg.get("quotes") or {}
    mode = q.get("mode", "none")
    show = q.get("pages") or {}
    quotes = [x for x in quotes if (x.get("text") or "").strip()]
    if mode not in ("per_type", "per_page") or not quotes:
        return {}
    out, n = {}, 0
    for p in pages:
        if p.kind not in QUOTE_KINDS or show.get(p.kind, True) is False:
            continue
        if mode == "per_type":
            out[p.id] = quotes[QUOTE_KINDS.index(p.kind) % len(quotes)]
        else:
            out[p.id] = quotes[n % len(quotes)]
            n += 1
    return out


def build_plan(cfg: dict, duas: list | None = None, quotes: list | None = None) -> Plan:
    cfg = normalize(cfg)
    cfg["modules"] = effective_modules(cfg)
    M = cfg["modules"]
    lay = cfg["layout"]
    period = cfg["calendar"].get("period") or "year"
    short = period in SHORT_PERIODS
    undated = not is_dated(cfg["calendar"])
    eng = make_engine(cfg["calendar"])
    pages: list[Page] = []
    targets: dict = {}
    sections: list = []
    day_target: dict = {}
    tabs: list = []

    def add(p: Page):
        pages.append(p)
        return p

    def week_title(w, month_title: str, k: int) -> str:
        if not undated:
            return w.label
        return f"{month_title} · Week {k}" if month_title else "Week"

    def day_title(d, wt: str) -> str:
        return f"{wt} · {d.weekday_name}" if undated else d.label

    def add_week(w, wt: str, y, up: str) -> list[str]:
        """Week page + optional prayer week + daily pages; returns the ids added."""
        start = len(pages)
        if M["week"]:
            add(Page(w.id, "week", wt, {"week": w}, y, up, "calendar"))
        if M["namaz_week"]:
            add(Page("nw-" + w.id, "namaz_week", f"Prayers · {wt}", {"week": w}, y, w.id if M["week"] else up, "calendar"))
        if M["day"]:
            wup = w.id if M["week"] else up
            for d, ok in zip(w.days, w.in_range):
                if ok:
                    add(Page(d.id, "day", day_title(d, wt), {"day": d, "week": w}, y, wup, "calendar"))
        return [p.id for p in pages[start:]]

    if M["cover"]:
        add(Page("cover", "cover", "Start page" if short else "Cover"))
    if M["index"]:
        add(Page("index", "index", "Contents"))
    home = "index" if M["index"] else ("cover" if M["cover"] else None)

    # ---------------------------------------------------------- calendar
    has_cal = any(M[k] for k in CAL_MODULES)
    if has_cal:
        months = eng.months()
        weeks = eng.weeks()
        # each week belongs to the month of its first in-range day
        week_of_month: dict = {}
        for w in weeks:
            first = next(d for d, ok in zip(w.days, w.in_range) if ok)
            week_of_month.setdefault(first.month_key, []).append(w)
            for d, ok in zip(w.days, w.in_range):
                if not ok:
                    continue
                if M["day"]:
                    day_target[d.id] = d.id
                elif M["week"]:
                    day_target[d.id] = w.id
                elif M["namaz_week"]:
                    day_target[d.id] = "nw-" + w.id
                elif M["month"]:
                    day_target[d.id] = d.month_key

    def q_title(q: int, y: int) -> str:
        return f"Quarter {q}" if undated else f"Q{q} {eng.year_title(y)}"

    def add_month(m, y, up: str, review: bool) -> list[str]:
        """Month calendar + its monthly pages + its weeks/days; returns the ids added."""
        start = len(pages)
        if M["month"]:
            add(Page(m.key, "month", m.title, {"month": m}, y, up, "calendar"))
        mup = m.key if M["month"] else up
        if M["month_goals"]:
            add(Page("mg-" + m.key, "month_goals", f"Goals & notes · {m.title}", {"month": m}, y, mup, "calendar"))
        if M["month_habits"]:
            add(Page("hab-" + m.key, "month_habits", f"Habits · {m.title}", {"month": m}, y, mup, "calendar"))
        if M["namaz_month"]:
            add(Page("nm-" + m.key, "namaz_month", f"Prayers · {m.title}", {"month": m}, y, mup, "calendar"))
        for k, w in enumerate(week_of_month.get(m.key, []), 1):
            add_week(w, week_title(w, m.title, k), y, mup)
        if review and M["goal_review"]:
            add(Page("gr-" + m.key, "goal_review", f"Review · {m.title}", {"month": m}, y, mup, "calendar"))
        return [p.id for p in pages[start:]]

    if has_cal and short and period == "week":
        # ---- a single week: the week (and its days) only
        for w in weeks:
            y = next(d for d, ok in zip(w.days, w.in_range) if ok).year
            ids = add_week(w, "Week" if undated else w.label, y, home)
            if ids:
                tabs.append(("Week", ids[0], set(ids) - ({d.id for d in w.days} if M["day"] else set())))
                sections.append(("Week", ids[0]))
            if M["day"]:
                tabs.extend((WEEKDAYS_SHORT[d.weekday], d.id, {d.id}) for d, ok in zip(w.days, w.in_range) if ok)
    elif has_cal and short:
        # ---- single month / quarter / custom range: no year-level pages at all
        qid = None
        if M["quarter"]:
            m0 = months[0]
            qid = f"q-{year_key(eng.mode, m0.year)}-{m0.quarter}"
            add(Page(qid, "quarter", q_title(m0.quarter, m0.year),
                     {"q": m0.quarter, "year": m0.year, "months": months}, m0.year, home, "calendar"))
            targets.setdefault(m0.year, {"year": None, "q": {}, "m": {}})["q"][m0.quarter] = qid
            sections.append((q_title(m0.quarter, m0.year), qid))
            tabs.append(("Qtr" if undated else f"Q{m0.quarter}", qid, {qid}))
        for m in months:
            ids = add_month(m, m.year, qid or home, review=True)
            if not ids:
                continue
            targets.setdefault(m.year, {"year": None, "q": {}, "m": {}})["m"][m.month] = ids[0]
            sections.append((m.title, ids[0]))
            if period != "month":
                tabs.append((m.short, ids[0], set(ids)))
                continue
            # single month: finer tabs – month, goals, habits, prayers, each week, review
            wk_no = {w.id: k for k, w in enumerate(week_of_month.get(m.key, []), 1)}
            wk_tab: dict = {}
            for pg in pages[len(pages) - len(ids):]:
                if pg.kind in ("week", "namaz_week", "day"):
                    wid = pg.data["week"].id
                    if wid not in wk_tab:
                        wk_tab[wid] = (f"W{wk_no[wid]}", pg.id, set())
                        tabs.append(wk_tab[wid])
                    wk_tab[wid][2].add(pg.id)
                else:
                    label = {"month": m.short, "month_goals": "Goals", "month_habits": "Habits",
                             "namaz_month": "Prayer", "goal_review": "Review"}[pg.kind]
                    tabs.append((label, pg.id, {pg.id}))
        if M["quarter_review"] and qid:
            m0 = months[0]
            add(Page(f"qr-{year_key(eng.mode, m0.year)}-{m0.quarter}", "quarter_review",
                     f"{q_title(m0.quarter, m0.year)} review", {"q": m0.quarter, "year": m0.year}, m0.year, qid, "calendar"))
            tabs[0][2].add(pages[-1].id)
    elif has_cal:
        for y in eng.years():
            yk = year_key(eng.mode, y)
            tg = {"year": None, "q": {}, "m": {}}
            targets[y] = tg
            start_len = len(pages)
            if M["year_overview"]:
                add(Page(yk, "year_overview", "Year overview" if undated else eng.year_title(y),
                         {"year": y, "months": [eng.month(y, i) for i in range(1, 13)]}, y, home, "calendar"))
            for q in range(1, 5):
                mq = [m for m in months if m.year == y and m.quarter == q]
                if not mq:
                    continue
                q_start = len(pages)
                qid = f"q-{yk}-{q}"
                if M["quarter"]:
                    add(Page(qid, "quarter", q_title(q, y),
                             {"q": q, "year": y, "months": [eng.month(y, i) for i in range(q * 3 - 2, q * 3 + 1)]},
                             y, yk if M["year_overview"] else home, "calendar"))
                for m in mq:
                    ids = add_month(m, y, qid if M["quarter"] else (yk if M["year_overview"] else home), review=False)
                    if ids:
                        tg["m"][m.month] = ids[0]
                if M["quarter_review"]:
                    add(Page(f"qr-{yk}-{q}", "quarter_review", f"{q_title(q, y)} review", {"q": q, "year": y},
                             y, qid if M["quarter"] else home, "calendar"))
                if len(pages) > q_start:
                    tg["q"][q] = pages[q_start].id
            if len(pages) > start_len:
                if M["divider"]:
                    pages.insert(start_len, Page(f"div-{yk}", "divider", eng.year_title(y), {"label": eng.year_title(y)},
                                                 y, home, "calendar"))
                tg["year"] = pages[start_len].id
                sections.append((eng.year_title(y), tg["year"]))
            else:
                del targets[y]

    # ------------------------------------------------------- goal block
    def block(label: str, first_idx: int):
        if len(pages) > first_idx:
            if M["divider"]:
                pages.insert(first_idx, Page(f"div-{label.lower()}", "divider", label, {"label": label}, None, home))
            sections.append((label, pages[first_idx].id))
            for p in pages[first_idx:]:
                p.group = label
            if short:
                tabs.append((label, pages[first_idx].id, {p.id for p in pages[first_idx:]}))

    s = len(pages)
    if M["goal_vision"]:
        add(Page("goal-vision", "goal_vision", "Vision", {}, None, home))
    for i in range(1, int(lay.get("goals_count", 3)) + 1):
        if M["goal_smart"]:
            add(Page(f"goal-{i}-smart", "goal_smart", f"Goal {i} · SMART", {"n": i}, None, home))
        if M["goal_milestones"]:
            add(Page(f"goal-{i}-ms", "goal_milestones", f"Goal {i} · Milestones", {"n": i}, None, home))
        if M["goal_actions"]:
            add(Page(f"goal-{i}-act", "goal_actions", f"Goal {i} · Action steps", {"n": i}, None, home))
    if M["goal_progress"]:
        add(Page("goal-progress", "goal_progress", "Progress tracker", {"months": eng.months()[:12]}, None, home))
    if M["goal_review"] and not short:  # short periods place each review after its month
        for m in eng.months():
            add(Page("gr-" + m.key, "goal_review", f"Review · {m.title}", {"month": m}, None, home))
    block("Goals", s)

    s = len(pages)
    if M["affirmations"]:
        add(Page("affirmations", "affirmations", "Affirmations", {}, None, home))
    if M["vision_board"]:
        add(Page("vision-board", "vision_board", "Vision board", {}, None, home))
    for i in range(int(lay.get("gratitude_pages", 2)) if M["gratitude"] else 0):
        add(Page(f"gratitude-{i + 1}", "gratitude", f"Gratitude {i + 1}", {"n": i + 1}, None, home))
    for i in range(int(lay.get("scripting_pages", 2)) if M["scripting"] else 0):
        add(Page(f"scripting-{i + 1}", "scripting", f"Scripting {i + 1}", {"n": i + 1}, None, home))
    if M["method369"]:
        add(Page("method369", "method369", "369 method", {}, None, home))
    block("Manifest", s)

    # ------------------------------------------------------- Islamic
    duas = duas or []
    s = len(pages)
    if M["dua_list"]:
        for i, chunk in enumerate(_chunks(duas, 3)):
            add(Page(f"dua-list-{i + 1}", "dua_list", f"Dua collection {i + 1}", {"duas": chunk}, None, home))
    for i in range(int(lay.get("dua_journal_pages", 4)) if M["dua_journal"] else 0):
        add(Page(f"dua-journal-{i + 1}", "dua_journal", f"Dua journal {i + 1}", {"n": i + 1}, None, home))
    if M["duas_answered"]:
        add(Page("duas-answered", "duas_answered", "Duas answered", {}, None, home))
    block("Duas", s)

    ramadan = None
    s = len(pages)
    if any(M[k] for k in ("ramadan_tracker", "ramadan_day", "last_ten", "eid_prep", "meal_planner")):
        ramadan = find_ramadan(eng, cfg["calendar"])
        if M["ramadan_tracker"]:
            add(Page("ramadan-tracker", "ramadan_tracker", "Fasting tracker", {"r": ramadan}, None, home))
        if M["ramadan_day"]:
            for d in ramadan["days"]:
                add(Page(f"ramadan-{d['n']}", "ramadan_day", f"Ramadan day {d['n']}", {"r": ramadan, "d": d}, None,
                         "ramadan-tracker" if M["ramadan_tracker"] else home))
        if M["last_ten"]:
            add(Page("last-ten", "last_ten", "Last ten nights", {"r": ramadan}, None, home))
        if M["eid_prep"]:
            add(Page("eid-prep", "eid_prep", "Eid preparation", {}, None, home))
        if M["meal_planner"]:
            for i, chunk in enumerate(_chunks(ramadan["days"], 15)):
                add(Page(f"meals-{i + 1}", "meal_planner", f"Meal planner {i + 1}", {"r": ramadan, "days": chunk}, None, home))
    block("Ramadan", s)

    s = len(pages)
    if M["juz_tracker"]:
        add(Page("juz", "juz_tracker", "Juz tracker", {}, None, home))
    if M["surah_checklist"]:
        nums = list(enumerate(SURAHS, 1))
        add(Page("surahs-1", "surah_checklist", "Surahs 1–57", {"surahs": nums[:57]}, None, home))
        add(Page("surahs-2", "surah_checklist", "Surahs 58–114", {"surahs": nums[57:]}, None, home))
    if M["khatam"]:
        add(Page("khatam", "khatam", "Khatam progress", {}, None, home))
    for i in range(int(lay.get("reflection_pages", 4)) if M["reflection"] else 0):
        add(Page(f"reflection-{i + 1}", "reflection", f"Reflection {i + 1}", {"n": i + 1}, None, home))
    block("Quran", s)

    s = len(pages)
    for i in range(int(lay.get("notes_pages", 4)) if M["notes"] else 0):
        add(Page(f"notes-{i + 1}", "notes", f"Notes {i + 1}", {"n": i + 1}, None, home))
    block("Notes", s)

    if not pages:
        raise ValueError("No pages selected – turn on at least one page type in step 5.")
    return Plan(cfg, eng, pages, targets, sections, day_target, home, ramadan, duas, short, tabs,
                assign_quotes(cfg, pages, quotes or []))


def split_configs(cfg: dict, how: str) -> list[tuple[str, dict]]:
    """Split one config into several (per year / per half-year) for Etsy's 20 MB limit.

    Short periods and undated planners are always a single file."""
    import copy
    cfg = normalize(cfg)
    cal = cfg["calendar"]
    if how not in ("year", "half") or (cal.get("period") or "year") != "year" or not is_dated(cal):
        return [("", cfg)]
    out = []
    eng = CalendarEngine(cal)
    for y in eng.years():
        ranges = [(1, 12)] if how == "year" else [(1, 6), (7, 12)]
        for i, (a, b) in enumerate(ranges):
            sa, sb = max((y, a), eng.start), min((y, b), eng.end)
            if sa > sb:
                continue
            c = copy.deepcopy(cfg)
            c["calendar"].update(start_year=sa[0], start_month=sa[1], end_year=sb[0], end_month=sb[1])
            tag = f"{y}" if how == "year" else f"{y}-H{i + 1}"
            out.append((tag, c))
    return out or [("", cfg)]
