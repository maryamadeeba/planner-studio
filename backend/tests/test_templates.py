"""Template styles: data-driven definitions, the three featured looks, Islamic/Hijri support and listing images."""
import json
import re
import shutil
from pathlib import Path

import pytest

from app import models
from app.services import themes
from app.services.catalog import MODULES, normalize
from app.services.planner import build_plan
from app.services.render import LINK_PREFIX, Renderer

FEATURED = ["sky_classic", "blush_bloom", "ink_gold"]
NOV = {"period": "month", "period_year": 2026, "period_month": 11}
QUOTES = [{"text": t, "author": a} for t, a, _ in models.SEED_QUOTES]
DUAS = [{"title": "Dua before sleeping", "arabic": "بِاسْمِكَ اللَّهُمَّ أَمُوتُ وَأَحْيَا",
         "english": "In Your name O Allah, I die and I live.", "reference": "Bukhari", "verified": True}]


def test_featured_templates_in_order():
    assert themes.featured_templates() == FEATURED
    assert themes.DEFAULT_PRESET == "sky_classic"
    for k in FEATURED:
        p = themes.PRESETS[k]
        assert p["label"] and p["description"] and len(p["swatches"]) >= 3


def test_template_definitions_match_the_brief():
    sky, bloom, ink = (themes.resolve({"preset": k}) for k in FEATURED)
    assert (sky["title_font"], sky["cards"], sky["motif_kind"], sky["cover_layout"]) == ("Playfair Display", "soft", "bow", "panel")
    assert sky["accent"] == "#2A93B3" and sky["background"] == "#FFFCF8"
    assert bloom["title_font"] == "Caveat" and bloom["background"] == "#FFFFFF"
    assert (bloom["highlight"], bloom["motif_kind"], bloom["cover_layout"]) == ("#FFE59A", "flower", "bloom")
    assert bloom["radius"] > sky["radius"]
    assert (ink["ink"], ink["primary"], ink["accent"]) == ("#1D4E5F", "#1D4E5F", "#C9A24B")
    assert {ink["title_font"], ink["heading_font"], ink["body_font"], ink["script_font"]} == {"Poppins"}
    assert (ink["cards"], ink["cover_layout"], ink["motif"]) == ("lines", "editorial", False)
    assert ink["mark"] == "#1D4E5F"  # checkboxes in ink: the gold is decorative only


@pytest.mark.parametrize("key", list(themes.PRESETS))
def test_every_template_is_readable_by_default(key):
    assert themes.contrast_issues({"preset": key}) == []
    t = themes.resolve({"preset": key})
    assert themes.contrast(t["accent_text"], t["card"]) >= 4.5 and themes.contrast(t["muted"], t["card"]) >= 4.5


def test_old_brand_projects_map_to_sky_classic():
    assert normalize({"theme": {"preset": "brand"}})["theme"]["preset"] == "sky_classic"
    assert themes.template_key("nonsense") == "sky_classic"


def test_adding_a_fourth_template_is_just_a_json_file(tmp_path):
    for f in themes.STYLE_DIR.iterdir():
        shutil.copy(f, tmp_path / f.name)
    d = json.loads((tmp_path / "sky_classic.json").read_text(encoding="utf-8"))
    d.update(label="Sage Garden", description="Test", order=4, aliases=[], featured=True, cards="lines", motif="flower")
    d["colors"].update(primary="#2F4A3A", accent="#7A9A6B", background="#FBFBF6")
    (tmp_path / "sage_garden.json").write_text(json.dumps(d), encoding="utf-8")
    (tmp_path / "sage_garden.css").write_text(".mgrid .c .n { color: {{ t.accent }}; }", encoding="utf-8")
    presets, _ = themes.load_templates(tmp_path)
    assert [k for k, p in presets.items() if p["featured"]] == FEATURED + ["sage_garden"]
    assert presets["sage_garden"]["cards"] == "lines" and "{{ t.accent }}" in presets["sage_garden"]["css"]
    (tmp_path / "broken.json").write_text(json.dumps({"label": "x", "colors": {"primary": "#000000"}}), encoding="utf-8")
    with pytest.raises(ValueError, match="broken"):
        themes.load_templates(tmp_path)


@pytest.mark.parametrize("key", FEATURED)
def test_template_flags_and_css_reach_the_page(key):
    plan = build_plan({"planner_type": "daily", "calendar": NOV, "theme": {"preset": key}}, [], QUOTES)
    html = Renderer(plan, "A4", "digital").document(plan.pages[:3])
    t = themes.PRESETS[key]
    assert f"cards-{t['cards']} cover-{t['cover_layout']} motif-{t['motif_kind']}" in html
    assert ("/* template: " + key) in html if t["css"] else True
    if key == "blush_bloom":
        assert 'class="flower"' in html and "class=\"bow\"" not in html
    if key == "ink_gold":
        assert 'class="flower"' not in html and 'class="bow"' not in html
    if key == "sky_classic":
        assert 'class="bow"' in html


@pytest.mark.parametrize("key", FEATURED)
def test_islamic_hijri_and_arabic_in_every_template(key):
    cfg = {"planner_type": "namaz", "theme": {"preset": key},
           "modules": {"dua_list": True, "ramadan_tracker": True, "juz_tracker": True, "month": True},
           "calendar": {"mode": "hijri", "start_year": 1448, "start_month": 9, "end_year": 1448, "end_month": 10}}
    plan = build_plan(cfg, DUAS, QUOTES)
    month = next(p for p in plan.pages if p.kind == "month")
    assert month.data["month"].name == "Ramadan"
    r = Renderer(plan, "A4", "digital")
    html = r.document()
    assert 'dir="rtl"' in html and DUAS[0]["arabic"] in html and "رَمَضَان" in html
    assert "--ar-font: 'Amiri'" in html
    ids = {p.id for p in plan.pages}
    assert not set(re.findall(re.escape(LINK_PREFIX) + r'([^"]+)"', html)) - ids


@pytest.mark.parametrize("key", FEATURED)
def test_custom_colours_pictures_and_quotes_on_top_of_any_template(key):
    cfg = {"planner_type": "daily", "calendar": NOV, "quotes": {"mode": "per_page"},
           "theme": {"preset": key, "primary": "#3B2F63", "pages": {"week": {"background": "#EEF7EE"}}},
           "images": {"cover": {"asset": "c.jpg", "mode": "framed"}, "month_header": {"asset": "m.jpg", "position": "banner"}}}
    plan = build_plan(cfg, [], QUOTES)
    r = Renderer(plan, "A4", "digital", asset_base="/assets")
    assert r.theme["primary"] == "#3B2F63" and r.theme["preset"] == key
    week = next(p for p in plan.pages if p.kind == "week")
    assert r.page_theme(week)["background"] == "#EEF7EE"
    cover, month = (next(p for p in plan.pages if p.kind == k) for k in ("cover", "month"))
    html = r.document([cover, month, week])
    assert 'src="/assets/c.jpg"' in html and 'src="/assets/m.jpg"' in html
    assert html.count('class="quote-') >= 3 and "--bg:#EEF7EE" in html


@pytest.mark.parametrize("key", FEATURED)
@pytest.mark.parametrize("size", ["A4", "HalfLetter", "iPadLandscape"])
def test_every_module_renders_in_every_template(key, size):
    plan = build_plan({"planner_type": "daily", "modules": {k: True for k in MODULES}, "theme": {"preset": key},
                       "calendar": {"start_year": 2027, "start_month": 1, "end_year": 2027, "end_month": 1}}, DUAS, QUOTES)
    seen = list({p.kind: p for p in reversed(plan.pages)}.values())
    for variant in ("digital", "printable"):
        html = Renderer(plan, size, variant).document(seen)
        assert html.count('class="page ') == len(seen)


@pytest.mark.slow
def test_listing_images_use_template_and_compare_all(tmp_path):
    from app.services import mockups, pdf
    plan = build_plan({"planner_type": "compact", "calendar": NOV, "theme": {"preset": "blush_bloom"}}, [], QUOTES)
    try:
        with pdf.browser() as b:
            files = mockups.generate(b, plan, plan.cfg, "A4", ["digital"], ["A4"], tmp_path, themes.FONT_DIR.resolve().as_uri(), {},
                                     quotes=QUOTES)
    except pdf.EngineError as e:
        pytest.skip(str(e))
    names = [f.name for f in files]
    assert any("compare" in n for n in names) and all(f.stat().st_size > 20_000 for f in files)
