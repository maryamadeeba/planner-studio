"""Planner structure + rendering tests (no Chromium needed, except the marked PDF test)."""
from pathlib import Path

import pytest

from app.services.catalog import MODULES, PLANNER_TYPES, SIZES
from app.services.planner import build_plan, split_configs
from app.services.render import LINK_PREFIX, Renderer

ALL = {k: True for k in MODULES}
DUAS = [{"title": "Test", "arabic": "مُحَرَّم", "english": "Test", "reference": "", "verified": False}]


@pytest.mark.parametrize("ptype", list(PLANNER_TYPES))
def test_each_planner_type_builds(ptype):
    plan = build_plan({"planner_type": ptype}, DUAS)
    ids = [p.id for p in plan.pages]
    assert len(ids) == len(set(ids)), "page ids must be unique"
    assert plan.pages


def test_daily_planner_targets_resolve():
    plan = build_plan({"planner_type": "daily", "calendar": {"start_year": 2028, "end_year": 2028}}, DUAS)
    ids = {p.id for p in plan.pages}
    assert len([p for p in plan.pages if p.kind == "day"]) == 366  # leap year
    assert all(t in ids for t in plan.day_target.values())
    for tg in plan.targets.values():
        assert tg["year"] in ids
        assert all(v in ids for v in tg["q"].values())
        assert sorted(tg["m"]) == list(range(1, 13))
    assert all(p.parent in ids or p.parent is None for p in plan.pages)


def test_hijri_daily_plan():
    plan = build_plan({"planner_type": "daily", "calendar": {"mode": "hijri", "start_year": 1448, "start_month": 1,
                                                             "end_year": 1448, "end_month": 12, "hijri_offset": -1}}, DUAS)
    days = [p for p in plan.pages if p.kind == "day"]
    assert len(days) in (354, 355)
    assert days[0].data["day"].day == 1 and days[0].data["day"].month_name == "Muharram"


def test_split_per_half_year():
    parts = split_configs({"calendar": {"start_year": 2026, "end_year": 2027}, "output": {"split": "half"}}, "half")
    assert [t for t, _ in parts] == ["2026-H1", "2026-H2", "2027-H1", "2027-H2"]


@pytest.mark.parametrize("size", list(SIZES))
@pytest.mark.parametrize("theme", ["minimal", "pastel", "islamic", "colorful"])
def test_every_module_renders(size, theme):
    cfg = {"planner_type": "daily", "modules": ALL, "theme": {"preset": theme},
           "calendar": {"start_year": 2027, "start_month": 1, "end_year": 2027, "end_month": 2},
           "personalization": {"name": "Ayesha Bint Muhammad Al-Very-Long-Name", "mode": "throughout"}}
    plan = build_plan(cfg, DUAS)
    seen = {}
    for p in plan.pages:
        seen.setdefault(p.kind, p)
    for variant in ("digital", "printable"):
        r = Renderer(plan, size, variant, font_base="/fonts")
        html = r.document(list(seen.values()))
        assert html.count('class="page ') == len(seen)
        assert (LINK_PREFIX in html) == (variant == "digital")
    assert set(seen) == set(MODULES)


@pytest.mark.slow
def test_pdf_links_and_page_count(tmp_path: Path):
    """Needs Chromium (python -m playwright install chromium)."""
    from app.services import pdf
    try:
        with pdf.browser() as b:
            plan = build_plan({"planner_type": "weekly", "calendar": {"start_year": 2027, "start_month": 1,
                                                                      "end_year": 2027, "end_month": 3}}, DUAS)
            r = Renderer(plan, "A4", "digital", font_base=Path("app/fonts").resolve().as_uri())
            res = pdf.render_pdf(r, tmp_path / "t.pdf", b=b, batch_size=10)
    except pdf.EngineError as e:
        pytest.skip(str(e))
    assert res["verify"]["pages"] == len(plan.pages)
    assert res["verify"]["unresolved"] == 0 and res["links"] > 100
