"""Short-period (month / quarter / week / custom) and undated planners, plus brand defaults."""
import re
from datetime import date, timedelta
from pathlib import Path

import pytest

from app.services import themes
from app.services.catalog import MODULES, PLANNER_TYPES, normalize, supports_undated
from app.services.planner import build_plan, split_configs
from app.services.render import LINK_PREFIX, Renderer

DUAS = [{"title": "Test", "arabic": "مُحَرَّم", "english": "Test", "reference": "", "verified": False}]
NOV = {"period": "month", "period_year": 2026, "period_month": 11}
YEAR_LEVEL = {"year_overview", "index"}
EXTRAS = {"week": True, "day": True, "month_habits": True, "goal_review": True, "notes": True}


def kinds(plan):
    return [p.kind for p in plan.pages]


def links_in(plan, variant="digital", size="A4"):
    """Every internal link target in the rendered digital HTML of the whole plan."""
    html = Renderer(plan, size, variant, font_base="/fonts").document()
    return html, re.findall(re.escape(LINK_PREFIX) + r'([^"]+)"', html)


def assert_no_dangling(plan):
    ids = {p.id for p in plan.pages}
    html, targets = links_in(plan)
    assert targets, "digital planner should contain links"
    dangling = sorted(set(targets) - ids)
    assert not dangling, f"links to missing pages: {dangling[:10]}"
    assert all(t in ids for _, t, _ in plan.tabs)
    assert all(t in ids for _, t in plan.sections)
    assert all(p.parent in ids or p.parent is None for p in plan.pages)
    assert all(t in ids for t in plan.day_target.values())
    return html


# ------------------------------------------------------------- single month
def test_compact_preset_is_three_pages():
    plan = build_plan({"planner_type": "compact", "calendar": NOV}, DUAS)
    assert kinds(plan) == ["cover", "month", "month_goals"]
    assert plan.pages[1].title == "November 2026"
    assert PLANNER_TYPES["compact"]["period"] == "month"
    assert_no_dangling(plan)


def test_single_month_only_contains_that_month():
    plan = build_plan({"planner_type": "daily", "calendar": NOV, "modules": EXTRAS}, DUAS)
    k = kinds(plan)
    assert not YEAR_LEVEL & set(k) and "quarter" not in k
    assert k[:3] == ["cover", "month", "month_goals"]
    days = [p for p in plan.pages if p.kind == "day"]
    assert [p.data["day"].g for p in days] == [date(2026, 11, 1) + timedelta(days=i) for i in range(30)]
    # Nov 2026 starts on a Sunday and ends on a Monday -> 6 Monday-start weeks
    assert k.count("week") == 6
    assert k.count("month_habits") == 1 and k.count("goal_review") == 1 and k.count("notes") == 4
    assert len(plan.pages) == 3 + 1 + 6 + 30 + 1 + 4
    assert plan.home == "cover"
    html = assert_no_dangling(plan)
    assert "Year at a Glance" not in html


def test_single_month_tabs_point_at_existing_pages():
    plan = build_plan({"planner_type": "weekly", "calendar": NOV}, DUAS)
    labels = [l for l, _, _ in plan.tabs]
    assert labels[:2] == ["Nov", "Goals"] and "W1" in labels and "Notes" in labels
    r = Renderer(plan, "A4", "digital")
    week_page = next(p for p in plan.pages if p.kind == "week")
    on = [l for l, _, cls in r.short_tabs(week_page) if cls == "on"]
    assert on == ["W1"]
    # no full-year tabs (Q1..Q4, Jan..Dec) on short periods
    html = r.document([week_page])
    assert ">Q1<" not in html and ">Jan<" not in html


def test_month_hijri():
    plan = build_plan({"planner_type": "monthly", "calendar": {"mode": "hijri", "period": "month", "period_year": 1448,
                                                               "period_month": 9}}, DUAS)
    m = next(p for p in plan.pages if p.kind == "month")
    assert m.data["month"].name == "Ramadan" and m.title == "Ramadan 1448 AH"
    assert_no_dangling(plan)


# -------------------------------------------------------------- quarter
def test_quarter_has_overview_plus_its_months():
    plan = build_plan({"planner_type": "monthly", "calendar": {"period": "quarter", "period_year": 2027, "period_quarter": 2},
                       "modules": {"quarter_review": True}}, DUAS)
    k = kinds(plan)
    assert not YEAR_LEVEL & set(k)
    assert k[:2] == ["cover", "quarter"]
    assert [p.data["month"].month for p in plan.pages if p.kind == "month"] == [4, 5, 6]
    assert k.count("month_goals") == 3 and k.count("quarter_review") == 1
    assert [l for l, _, _ in plan.tabs][:4] == ["Q2", "Apr", "May", "Jun"]
    assert_no_dangling(plan)


# ----------------------------------------------------------------- week
def test_single_week_outputs_only_that_week():
    plan = build_plan({"planner_type": "daily", "calendar": {"period": "week", "week_start": "2026-11-26"}}, DUAS)
    k = kinds(plan)
    assert set(k) == {"cover", "week", "day", "notes"}
    assert k.count("week") == 1 and k.count("day") == 7
    week = next(p for p in plan.pages if p.kind == "week")
    assert week.id == "w-2026-11-23"  # snapped to Monday
    assert [l for l, _, _ in plan.tabs][:8] == ["Week", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    assert_no_dangling(plan)


def test_week_spanning_two_months():
    plan = build_plan({"planner_type": "weekly", "calendar": {"period": "week", "week_start": "2026-11-30"}}, DUAS)
    week = next(p for p in plan.pages if p.kind == "week").data["week"]
    assert all(week.in_range) and week.label == "30 November – 6 December 2026"
    assert "month" not in kinds(plan)


# --------------------------------------------------------------- custom
def test_custom_range_is_clipped_to_the_day():
    plan = build_plan({"planner_type": "daily", "calendar": {"period": "custom", "range_start": "2026-11-15",
                                                             "range_end": "2027-01-10"}}, DUAS)
    days = [p.data["day"].g for p in plan.pages if p.kind == "day"]
    assert days[0] == date(2026, 11, 15) and days[-1] == date(2027, 1, 10) and len(days) == 57
    assert [p.title for p in plan.pages if p.kind == "month"] == ["November 2026", "December 2026", "January 2027"]
    html = assert_no_dangling(plan)
    # days before the 15th are printed dimmed and never linked
    assert 'class="c out"' in html


@pytest.mark.parametrize("cal, msg", [
    ({"period": "custom", "range_start": "2026-12-01", "range_end": "2026-11-01"}, "ends before"),
    ({"period": "custom", "range_start": "2026-01-01", "range_end": "2027-06-01"}, "at most one year"),
    ({"period": "week", "week_start": "not a date"}, "valid week"),
])
def test_period_validation(cal, msg):
    with pytest.raises(ValueError, match=msg):
        build_plan({"planner_type": "weekly", "calendar": cal}, DUAS)


def test_short_periods_never_split():
    cfg = {"calendar": NOV, "output": {"split": "year"}}
    assert [t for t, _ in split_configs(cfg, "year")] == [""]


def test_full_year_unchanged():
    plan = build_plan({"planner_type": "daily", "calendar": {"start_year": 2027, "end_year": 2027}}, DUAS)
    k = kinds(plan)
    assert k[:3] == ["cover", "index", "year_overview"] and k.count("quarter") == 4 and k.count("day") == 365
    assert not plan.short and not plan.tabs


# --------------------------------------------------------------- undated
@pytest.mark.parametrize("period, months, weeks", [("year", 12, 60), ("quarter", 3, 15), ("month", 1, 5), ("week", 0, 1)])
def test_undated_structure(period, months, weeks):
    plan = build_plan({"planner_type": "daily", "calendar": {"dated": False, "period": period}}, DUAS)
    k = kinds(plan)
    assert k.count("month") == months and k.count("week") == weeks and k.count("day") == weeks * 7
    assert plan.undated
    assert_no_dangling(plan)


def test_undated_pages_have_blank_dates():
    plan = build_plan({"planner_type": "daily", "calendar": {**NOV, "dated": False},
                       "modules": {"month_habits": True, "namaz_month": True, "namaz_week": True}}, DUAS)
    r = Renderer(plan, "A4", "digital")
    html = r.document()
    for field in ("Month:", "Week of:", "Date:"):
        assert field in html
    text = re.sub(r"<[^>]+>|@font-face[^}]+}|https?://\S+", " ", html)
    assert not re.search(r"\b(19|20)\d\d\b", text), "undated pages must not print a year"
    assert "November" not in text
    day = next(p for p in plan.pages if p.kind == "day")
    assert day.data["day"].weekday_name == "Monday" and ">Monday<" in r.document([day])
    assert r.year_label() == ""


@pytest.mark.parametrize("ptype", ["yearly", "quarterly", "monthly", "weekly", "daily", "compact", "namaz", "goal", "ramadan"])
def test_undated_builds_for_dated_types(ptype):
    cfg = {"planner_type": ptype, "calendar": {"dated": False}}
    assert supports_undated(normalize(cfg))
    plan = build_plan(cfg, DUAS)
    assert_no_dangling(plan)


@pytest.mark.parametrize("ptype", ["manifestation", "dua", "quran"])
def test_undated_toggle_hidden_for_undated_types(ptype):
    assert not supports_undated(normalize({"planner_type": ptype}))


@pytest.mark.parametrize("cal", [NOV, {"period": "week", "week_start": "2026-11-23"},
                                 {"period": "quarter", "period_year": 2026, "period_quarter": 4},
                                 {**NOV, "dated": False}, {"dated": False}])
@pytest.mark.parametrize("size", ["A4", "iPadLandscape", "HalfLetter"])
def test_every_module_renders_in_short_and_undated(cal, size):
    cfg = {"planner_type": "daily", "modules": {k: True for k in MODULES}, "calendar": cal,
           "personalization": {"name": "Ayesha", "mode": "throughout"}}
    plan = build_plan(cfg, DUAS)
    seen = {}
    for p in plan.pages:
        seen.setdefault(p.kind, p)
    for variant in ("digital", "printable"):
        html = Renderer(plan, size, variant, font_base="/fonts").document(list(seen.values()))
        assert html.count('class="page ') == len(seen)


# ---------------------------------------------------------------- brand
def test_brand_theme_is_default_and_fonts_are_bundled():
    cfg = normalize({})
    t = themes.resolve(cfg["theme"])
    assert cfg["theme"]["preset"] == "sky_classic" and t["preset"] == "sky_classic"
    assert themes.resolve({"preset": "brand"})["preset"] == "sky_classic"  # old projects
    assert (t["primary"], t["accent"], t["background"], t["ink"]) == ("#1D4E5F", "#2A93B3", "#FFFCF8", "#35535E")
    assert (t["title_font"], t["body_font"], t["script_font"]) == ("Playfair Display", "Poppins", "Caveat")
    assert cfg["footer"]["text"] == cfg["listing"]["shop_line"] == "Productivity Shop by M"
    for files in themes.FONTS.values():
        for fname, _ in files:
            assert (themes.FONT_DIR / fname).stat().st_size > 50_000, fname
    for fam in ("Playfair Display", "Poppins", "Caveat"):
        assert fam in themes.font_faces_css("/fonts")


def test_cover_shows_shop_logo():
    plan = build_plan({"planner_type": "compact", "calendar": NOV}, DUAS)
    html = Renderer(plan, "A4", "digital", brand_logo="logo.png").document([plan.pages[0]])
    assert 'class="cover-logo" src="/assets/logo.png"' in html
    off = build_plan({"planner_type": "compact", "calendar": NOV, "personalization": {"cover_logo": False}}, DUAS)
    assert 'class="cover-logo"' not in Renderer(off, "A4", "digital", brand_logo="logo.png").document([off.pages[0]])


# ------------------------------------------------------------ real PDF
@pytest.mark.slow
@pytest.mark.parametrize("cfg", [
    {"planner_type": "daily", "calendar": NOV, "modules": EXTRAS},
    {"planner_type": "compact", "calendar": NOV},
    {"planner_type": "weekly", "calendar": {**NOV, "dated": False}},
], ids=["month-full", "compact", "undated"])
def test_short_period_pdf_links(tmp_path: Path, cfg):
    """Needs Chromium (python -m playwright install chromium)."""
    from app.services import pdf
    plan = build_plan(cfg, DUAS)
    try:
        with pdf.browser() as b:
            r = Renderer(plan, "A4", "digital", font_base=themes.FONT_DIR.resolve().as_uri())
            res = pdf.render_pdf(r, tmp_path / "t.pdf", b=b, batch_size=20)
    except pdf.EngineError as e:
        pytest.skip(str(e))
    v = res["verify"]
    assert v["pages"] == v["expected_pages"] == len(plan.pages)
    assert res["broken"] == 0 and v["unresolved"] == 0 and v["resolved"] == v["links"] > 0
