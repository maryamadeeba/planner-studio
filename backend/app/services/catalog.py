"""Planner types, page modules, sections, editable labels and default config."""
from __future__ import annotations

import copy

# --------------------------------------------------------------- modules
# key: (group, label, calendar_based, sections[(key, label)])
MODULES: dict[str, dict] = {
    "cover": {"group": "General", "label": "Cover", "sections": [("subtitle", "Subtitle / quote"), ("year", "Year"), ("monogram", "Monogram initial"), ("image", "Cover image")]},
    "index": {"group": "General", "label": "Index / contents", "sections": []},
    "divider": {"group": "General", "label": "Section divider pages", "sections": [("image", "Divider image"), ("quote", "Quote")]},
    "year_overview": {"group": "Time-based", "label": "Yearly overview", "calendar": True, "sections": [("goals", "Year goals"), ("key_dates", "Key dates")]},
    "quarter": {"group": "Time-based", "label": "Quarterly view", "calendar": True, "sections": [("goals", "Quarter goals"), ("notes", "Notes")]},
    "quarter_review": {"group": "Time-based", "label": "Quarter review", "calendar": True, "sections": [("wins", "Wins"), ("challenges", "Challenges"), ("lessons", "Lessons"), ("next", "Next quarter focus")]},
    "month": {"group": "Time-based", "label": "Monthly calendar", "calendar": True, "sections": [("goals", "Monthly goals"), ("notes", "Notes"), ("events", "Event names in grid")]},
    "month_goals": {"group": "Time-based", "label": "Monthly goals & notes page", "calendar": True, "sections": [("focus", "Focus word"), ("priorities", "Top priorities"), ("dates", "Important dates")]},
    "month_habits": {"group": "Time-based", "label": "Monthly habit tracker", "calendar": True, "sections": []},
    "week": {"group": "Time-based", "label": "Weekly pages", "calendar": True, "sections": [("priorities", "Top 3 priorities"), ("todo", "To-do"), ("notes", "Notes")]},
    "day": {"group": "Time-based", "label": "Daily pages", "calendar": True, "sections": [("schedule", "Hourly schedule"), ("priorities", "Priorities"), ("todo", "To-do"), ("water", "Water tracker"), ("mood", "Mood tracker"), ("notes", "Notes")]},
    "goal_vision": {"group": "Goals", "label": "Vision & dream", "sections": [("vision", "Vision"), ("dream", "Dream life"), ("why", "My why")]},
    "goal_smart": {"group": "Goals", "label": "SMART goal breakdown", "sections": []},
    "goal_milestones": {"group": "Goals", "label": "Milestones", "sections": []},
    "goal_actions": {"group": "Goals", "label": "Action steps", "sections": []},
    "goal_progress": {"group": "Goals", "label": "Progress tracker", "sections": []},
    "goal_review": {"group": "Goals", "label": "Monthly review", "sections": []},
    "affirmations": {"group": "Manifestation", "label": "Affirmations", "sections": []},
    "vision_board": {"group": "Manifestation", "label": "Vision board", "sections": []},
    "gratitude": {"group": "Manifestation", "label": "Gratitude log", "sections": []},
    "scripting": {"group": "Manifestation", "label": "Scripting pages", "sections": []},
    "method369": {"group": "Manifestation", "label": "369 method", "sections": []},
    "namaz_month": {"group": "Islamic", "label": "Namaz – monthly grid", "calendar": True, "sections": [("sunnah", "Sunnah column"), ("tahajjud", "Tahajjud column"), ("witr", "Witr column")]},
    "namaz_week": {"group": "Islamic", "label": "Namaz – weekly view", "calendar": True, "sections": [("sunnah", "Sunnah column"), ("tahajjud", "Tahajjud column"), ("witr", "Witr column")]},
    "dua_list": {"group": "Islamic", "label": "Dua list (Arabic + English)", "sections": [("reference", "Show reference")]},
    "dua_journal": {"group": "Islamic", "label": "Dua journal", "sections": []},
    "duas_answered": {"group": "Islamic", "label": "Duas answered log", "sections": []},
    "ramadan_tracker": {"group": "Ramadan", "label": "30-day fasting tracker", "sections": []},
    "ramadan_day": {"group": "Ramadan", "label": "Daily Ramadan pages", "sections": [("meals", "Suhoor / iftar"), ("prayers", "Prayers"), ("quran", "Quran pages read"), ("deeds", "Good deeds"), ("dua", "Dua of the day")]},
    "last_ten": {"group": "Ramadan", "label": "Last ten nights", "sections": []},
    "eid_prep": {"group": "Ramadan", "label": "Eid prep checklist", "sections": []},
    "meal_planner": {"group": "Ramadan", "label": "Ramadan meal planner", "sections": []},
    "juz_tracker": {"group": "Quran", "label": "30-juz tracker", "sections": []},
    "surah_checklist": {"group": "Quran", "label": "114-surah checklist", "sections": []},
    "khatam": {"group": "Quran", "label": "Khatam progress", "sections": []},
    "reflection": {"group": "Quran", "label": "Reflection pages", "sections": []},
    "notes": {"group": "General", "label": "Notes pages", "sections": []},
}

PLANNER_TYPES = {
    "yearly": {"label": "Yearly planner", "group": "Time-based", "modules": ["cover", "index", "year_overview", "month", "notes"]},
    "quarterly": {"label": "Quarterly planner", "group": "Time-based", "modules": ["cover", "index", "year_overview", "quarter", "quarter_review", "month", "notes"]},
    "monthly": {"label": "Monthly planner", "group": "Time-based", "modules": ["cover", "index", "year_overview", "month", "month_habits", "notes"]},
    "weekly": {"label": "Weekly planner", "group": "Time-based", "modules": ["cover", "index", "year_overview", "month", "week", "notes"]},
    "daily": {"label": "Daily planner", "group": "Time-based", "modules": ["cover", "index", "year_overview", "quarter", "month", "week", "day", "notes"]},
    "compact": {"label": "Compact monthly set", "group": "Time-based", "modules": ["cover", "month", "month_goals"], "period": "month"},
    "goal": {"label": "Goal planner", "group": "Goal & manifestation", "modules": ["cover", "index", "goal_vision", "goal_smart", "goal_milestones", "goal_actions", "goal_progress", "goal_review", "notes"]},
    "manifestation": {"label": "Manifestation planner", "group": "Goal & manifestation", "modules": ["cover", "index", "affirmations", "vision_board", "gratitude", "scripting", "method369"]},
    "namaz": {"label": "Namaz planner", "group": "Islamic", "modules": ["cover", "index", "year_overview", "namaz_month", "namaz_week"]},
    "dua": {"label": "Dua planner", "group": "Islamic", "modules": ["cover", "index", "dua_list", "dua_journal", "duas_answered"]},
    "ramadan": {"label": "Ramadan planner", "group": "Islamic", "modules": ["cover", "index", "ramadan_tracker", "ramadan_day", "last_ten", "eid_prep", "meal_planner"]},
    "quran": {"label": "Quran tracker", "group": "Islamic", "modules": ["cover", "index", "juz_tracker", "surah_checklist", "khatam", "reflection"]},
}

# ---------------------------------------------------------------- labels
# Every printed title / label / prompt.  Users can override any of them.
LABELS: dict[str, str] = {
    "cover.title": "Planner",
    "cover.subtitle": "Plan with intention, live with purpose",
    "index.title": "Contents",
    "divider.subtitle": "a fresh chapter begins",
    "month.hand": "make it a lovely month",
    "week.hand": "one small step at a time",
    "day.hand": "today matters",
    "year.title": "Year at a Glance",
    "year.goals": "Year Goals",
    "year.key_dates": "Key Dates",
    "quarter.title": "Quarter",
    "quarter.goals": "Quarter Goals",
    "quarter.notes": "Notes",
    "quarter_review.title": "Quarter Review",
    "quarter_review.wins": "Wins & highlights",
    "quarter_review.challenges": "Challenges",
    "quarter_review.lessons": "Lessons learned",
    "quarter_review.next": "Focus for next quarter",
    "month.title": "Monthly Plan",
    "month.goals": "Monthly Goals",
    "month.notes": "Notes",
    "month_goals.title": "Goals & Notes",
    "month_goals.goals": "Goals this month",
    "month_goals.focus": "My focus word",
    "month_goals.priorities": "Top priorities",
    "month_goals.dates": "Important dates",
    "month_goals.notes": "Notes",
    "undated.month": "Month",
    "undated.week": "Week of",
    "undated.date": "Date",
    "undated.year": "Year",
    "undated.quarter": "Quarter",
    "habits.title": "Habit Tracker",
    "habits.habit": "Habit",
    "week.title": "Week",
    "week.priorities": "Top 3 Priorities",
    "week.todo": "To Do",
    "week.notes": "Notes",
    "day.schedule": "Schedule",
    "day.priorities": "Top Priorities",
    "day.todo": "To Do",
    "day.water": "Water",
    "day.mood": "Mood",
    "day.notes": "Notes",
    "notes.title": "Notes",
    "goal_vision.title": "Vision",
    "goal_vision.vision": "My vision for this year",
    "goal_vision.dream": "If anything were possible, my dream life looks like…",
    "goal_vision.why": "Why this matters to me",
    "goal_smart.title": "SMART Goal",
    "goal_smart.goal": "Goal",
    "goal_smart.s": "Specific – what exactly will I achieve?",
    "goal_smart.m": "Measurable – how will I measure progress?",
    "goal_smart.a": "Achievable – what resources do I need?",
    "goal_smart.r": "Relevant – why does it matter now?",
    "goal_smart.t": "Time-bound – deadline",
    "goal_milestones.title": "Milestones",
    "goal_actions.title": "Action Steps",
    "goal_progress.title": "Progress Tracker",
    "goal_review.title": "Monthly Review",
    "goal_review.went_well": "What went well",
    "goal_review.improve": "What to improve",
    "goal_review.next": "Next month I will",
    "affirmations.title": "Affirmations",
    "vision_board.title": "Vision Board",
    "gratitude.title": "Gratitude Log",
    "gratitude.prompt": "Today I am grateful for…",
    "scripting.title": "Scripting",
    "scripting.prompt": "Write as if it has already happened…",
    "method369.title": "369 Method",
    "method369.morning": "Morning – write 3 times",
    "method369.afternoon": "Afternoon – write 6 times",
    "method369.night": "Night – write 9 times",
    "namaz.title": "Prayer Tracker",
    "namaz_week.title": "Weekly Prayers",
    "dua_list.title": "Dua Collection",
    "dua_journal.title": "Dua Journal",
    "dua_journal.prompt": "My dua today",
    "duas_answered.title": "Duas Answered",
    "ramadan_tracker.title": "Ramadan Fasting Tracker",
    "ramadan_day.title": "Ramadan",
    "ramadan_day.suhoor": "Suhoor",
    "ramadan_day.iftar": "Iftar",
    "ramadan_day.prayers": "Prayers",
    "ramadan_day.quran": "Quran pages read",
    "ramadan_day.deeds": "Good deeds",
    "ramadan_day.dua": "Dua of the day",
    "last_ten.title": "The Last Ten Nights",
    "eid_prep.title": "Eid Preparation",
    "meal_planner.title": "Ramadan Meal Planner",
    "juz_tracker.title": "30 Juz Tracker",
    "surah_checklist.title": "Surah Checklist",
    "khatam.title": "Khatam Progress",
    "reflection.title": "Quran Reflection",
    "reflection.prompt": "Ayah / surah I read",
    "nav.home": "Home",
    "nav.back": "Back",
    "nav.year": "Year",
    "ar.dua": "دُعَاء",
    "ar.ramadan": "رَمَضَان",
    "ar.namaz": "صَلَاة",
    "ar.quran": "قُرْآن",
}

PRAYERS = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]

SURAHS = [
    "Al-Fatihah", "Al-Baqarah", "Al-Imran", "An-Nisa", "Al-Ma'idah", "Al-An'am", "Al-A'raf", "Al-Anfal", "At-Tawbah", "Yunus",
    "Hud", "Yusuf", "Ar-Ra'd", "Ibrahim", "Al-Hijr", "An-Nahl", "Al-Isra", "Al-Kahf", "Maryam", "Ta-Ha",
    "Al-Anbiya", "Al-Hajj", "Al-Mu'minun", "An-Nur", "Al-Furqan", "Ash-Shu'ara", "An-Naml", "Al-Qasas", "Al-Ankabut", "Ar-Rum",
    "Luqman", "As-Sajdah", "Al-Ahzab", "Saba", "Fatir", "Ya-Sin", "As-Saffat", "Sad", "Az-Zumar", "Ghafir",
    "Fussilat", "Ash-Shura", "Az-Zukhruf", "Ad-Dukhan", "Al-Jathiyah", "Al-Ahqaf", "Muhammad", "Al-Fath", "Al-Hujurat", "Qaf",
    "Adh-Dhariyat", "At-Tur", "An-Najm", "Al-Qamar", "Ar-Rahman", "Al-Waqi'ah", "Al-Hadid", "Al-Mujadilah", "Al-Hashr", "Al-Mumtahanah",
    "As-Saff", "Al-Jumu'ah", "Al-Munafiqun", "At-Taghabun", "At-Talaq", "At-Tahrim", "Al-Mulk", "Al-Qalam", "Al-Haqqah", "Al-Ma'arij",
    "Nuh", "Al-Jinn", "Al-Muzzammil", "Al-Muddaththir", "Al-Qiyamah", "Al-Insan", "Al-Mursalat", "An-Naba", "An-Nazi'at", "Abasa",
    "At-Takwir", "Al-Infitar", "Al-Mutaffifin", "Al-Inshiqaq", "Al-Buruj", "At-Tariq", "Al-A'la", "Al-Ghashiyah", "Al-Fajr", "Al-Balad",
    "Ash-Shams", "Al-Layl", "Ad-Duha", "Ash-Sharh", "At-Tin", "Al-Alaq", "Al-Qadr", "Al-Bayyinah", "Az-Zalzalah", "Al-Adiyat",
    "Al-Qari'ah", "At-Takathur", "Al-Asr", "Al-Humazah", "Al-Fil", "Quraysh", "Al-Ma'un", "Al-Kawthar", "Al-Kafirun", "An-Nasr",
    "Al-Masad", "Al-Ikhlas", "Al-Falaq", "An-Nas",
]
assert len(SURAHS) == 114

DEFAULT_CONFIG: dict = {
    "planner_type": "daily",
    "modules": {},  # filled from planner type when empty
    "calendar": {
        "mode": "gregorian", "start_year": 2027, "start_month": 1, "end_year": 2027, "end_month": 12,
        # period: year (the start/end month range above) | quarter | month | week | custom
        "period": "year", "period_year": 2026, "period_month": 11, "period_quarter": 4,
        "week_start": "2026-11-02", "range_start": "2026-11-01", "range_end": "2026-11-30",
        "dated": True,
        "hijri_offset": 0, "iso_weeks": False, "arabic_month_names": True,
        "events": {"new_year": True, "ashura": True, "ramadan_start": True, "last_ten": True, "eid_fitr": True, "arafah": True, "eid_adha": True},
        "custom_hijri_events": [], "gregorian_holidays": [], "ramadan_year": None,
    },
    "output": {
        "sizes": ["A4"], "variants": ["digital"], "binder_margin": False, "ink_saving": False,
        "compress_images": False, "split": "none", "listing_images": True, "listing_landscape": False,
        "buyer_guide": True,
    },
    # primary = heading colour, ink = body text colour.  pages: per page type overrides,
    # e.g. {"cover": {"background": "#EAF8FC", "heading": None, "body": None, "accent": None}}
    "theme": {"preset": "sky_classic", "primary": None, "accent": None, "background": None, "ink": None,
              "heading_font": None, "body_font": None, "corner": None, "line_style": "lined", "motif": True,
              "pages": {}},
    # mode: none | per_type (one quote per page type) | per_page (a different quote on every page)
    "quotes": {"mode": "per_type", "categories": [], "pages": {"cover": True, "month": True, "week": True, "day": True,
                                                               "divider": True}},
    # Uploaded pictures.  fit: cover | contain · shape: square | rounded | circle · opacity 0.1–1
    "images": {
        "cover": {"asset": None, "mode": "framed", "position": "center", "fit": "cover", "opacity": 1.0, "shape": "rounded"},
        "divider": {"asset": None, "mode": "framed", "position": "center", "fit": "cover", "opacity": 1.0, "shape": "rounded"},
        "month_header": {"asset": None, "position": "right", "fit": "cover", "opacity": 1.0, "shape": "circle"},
    },
    "sections": {},
    "labels": {},
    "layout": {"week_layout": "vertical", "day_start": 6, "day_end": 22, "half_hours": False,
               "habit_rows": 10, "goals_count": 3, "notes_pages": 4, "gratitude_pages": 2,
               "scripting_pages": 2, "dua_journal_pages": 4, "reflection_pages": 4, "water_glasses": 8},
    "personalization": {"name": "", "mode": "cover", "subtitle": "", "monogram": True, "cover_image": None, "show_year": True,
                        "cover_logo": True},
    "footer": {"enabled": True, "text": "Productivity Shop by M", "logo": None, "position": "center", "opacity": 0.55},
    "listing": {
        "headline": "", "subheadline": "Instant digital download",
        "inside_title": "What's inside", "sizes_title": "Available sizes",
        "links_title": "Fully hyperlinked", "links_text": "Tap any tab, month or date to jump straight to the page",
        "colors_title": "Colour palette", "shop_line": "Productivity Shop by M",
    },
    "affirmations": [
        "I am worthy of every blessing coming my way.",
        "I am calm, focused and in control of my day.",
        "I am growing a little more every single day.",
        "I am grateful for what I have and open to more.",
        "I am capable of achieving everything I set my mind to.",
        "I am surrounded by love and support.",
        "I am proud of how far I have come.",
        "I am creating a life that feels good on the inside.",
    ],
    "habits": ["Water", "Exercise", "Reading", "Quran", "Sleep by 11", "No sugar", "Journal", "Walk"],
    "eid_checklist": ["Eid outfits", "Eidi envelopes", "Gifts for family", "Home cleaning", "Decorations", "Sweet dishes", "Mehndi", "Zakat al-Fitr paid", "Eid prayer plan", "Guest list"],
    "dua_ids": [],
}

SIZES = {
    # key: (label, width CSS px, height CSS px)  (96 CSS px = 1 inch)
    "A4": ("A4 (210 × 297 mm)", 793.7, 1122.5),
    "Letter": ("US Letter (8.5 × 11 in)", 816, 1056),
    "A5": ("A5 (148 × 210 mm)", 559.4, 793.7),
    "HalfLetter": ("Half Letter (5.5 × 8.5 in)", 528, 816),
    "iPadPortrait": ("iPad Portrait (1668 × 2224 aspect)", 834, 1112),
    "iPadLandscape": ("iPad Landscape (2224 × 1668 aspect)", 1112, 834),
}


def deep_merge(base: dict, over: dict | None) -> dict:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def normalize(cfg: dict | None) -> dict:
    cfg = deep_merge(DEFAULT_CONFIG, cfg or {})
    ptype = cfg.get("planner_type") if cfg.get("planner_type") in PLANNER_TYPES else "daily"
    cfg["planner_type"] = ptype
    defaults = {m: (m in PLANNER_TYPES[ptype]["modules"]) for m in MODULES}
    mods = cfg.get("modules") or {}
    cfg["modules"] = {m: bool(mods.get(m, defaults[m])) for m in MODULES}
    from .themes import template_key
    cfg["theme"]["preset"] = template_key(cfg["theme"].get("preset"))
    # older projects kept the cover picture under personalization.cover_image
    if not cfg["images"]["cover"].get("asset") and cfg["personalization"].get("cover_image"):
        cfg["images"]["cover"]["asset"] = cfg["personalization"]["cover_image"]
    cfg["personalization"]["cover_image"] = cfg["images"]["cover"].get("asset")
    return cfg


IMAGE_ROLES = {"cover": ("full", "framed"), "divider": ("full", "framed"), "month_header": ("left", "right", "banner")}
IMAGE_FITS = ("cover", "contain")
IMAGE_SHAPES = ("square", "rounded", "circle")
IMAGE_POSITIONS = ("center", "top", "bottom", "left", "right")


def image_setting(cfg: dict, role: str) -> dict | None:
    """Validated picture settings for a role, or None when no picture is chosen."""
    s = dict((cfg.get("images") or {}).get(role) or {})
    if not s.get("asset"):
        return None
    modes = IMAGE_ROLES[role]
    key = "position" if role == "month_header" else "mode"
    if s.get(key) not in modes:
        s[key] = modes[-1] if role != "month_header" else "right"
    if role != "month_header" and s.get("position") not in IMAGE_POSITIONS:
        s["position"] = "center"
    s["fit"] = s.get("fit") if s.get("fit") in IMAGE_FITS else "cover"
    s["shape"] = s.get("shape") if s.get("shape") in IMAGE_SHAPES else "rounded"
    try:
        s["opacity"] = max(0.1, min(1.0, float(s.get("opacity", 1))))
    except (TypeError, ValueError):
        s["opacity"] = 1.0
    return s


def default_modules(ptype: str) -> dict:
    return {m: (m in PLANNER_TYPES[ptype]["modules"]) for m in MODULES}


# ----------------------------------------------------------- short periods
# Short-period exports never contain year-level pages; the cover doubles as the start page.
YEAR_LEVEL = ["index", "year_overview"]
MONTH_LEVEL = ["month", "month_goals", "month_habits", "namaz_month", "goal_review", "goal_progress"]
PERIOD_RULES: dict[str, dict] = {
    "year": {"label": "Full year", "on": [], "off": []},
    "month": {"label": "Single month", "on": ["cover", "month", "month_goals"],
              "off": YEAR_LEVEL + ["quarter", "quarter_review"]},
    "quarter": {"label": "Quarter", "on": ["cover", "quarter", "month", "month_goals"], "off": YEAR_LEVEL},
    "week": {"label": "Single week", "on": ["cover", "week"],
             "off": YEAR_LEVEL + ["quarter", "quarter_review"] + MONTH_LEVEL},
    "custom": {"label": "Custom date range", "on": ["cover", "month", "month_goals"],
               "off": YEAR_LEVEL + ["quarter", "quarter_review"]},
}

# Modules whose pages carry dates – the Dated / Undated toggle only matters when one of them is on.
UNDATED_MODULES = [k for k, v in MODULES.items() if v.get("calendar")] + [
    "goal_review", "goal_progress", "ramadan_tracker", "ramadan_day", "last_ten", "meal_planner"]


def effective_modules(cfg: dict) -> dict:
    """Modules actually used for this config's period (forced on / off for short periods)."""
    rules = PERIOD_RULES.get(cfg["calendar"].get("period") or "year", PERIOD_RULES["year"])
    mods = dict(cfg["modules"])
    mods.update({m: False for m in rules["off"]})
    mods.update({m: True for m in rules["on"]})
    return mods


def supports_undated(cfg: dict) -> bool:
    mods = effective_modules(cfg)
    return any(mods.get(m) for m in UNDATED_MODULES)


def catalog_payload() -> dict:
    return {
        "modules": {k: {**{kk: vv for kk, vv in v.items() if kk != "sections"},
                        "sections": [{"key": s, "label": l} for s, l in v["sections"]]} for k, v in MODULES.items()},
        "planner_types": PLANNER_TYPES,
        "labels": LABELS,
        "sizes": {k: {"label": v[0], "w": v[1], "h": v[2]} for k, v in SIZES.items()},
        "default_config": DEFAULT_CONFIG,
        "period_rules": PERIOD_RULES,
        "undated_modules": UNDATED_MODULES,
    }
