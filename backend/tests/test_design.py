"""Colour customisation + contrast guard, pictures (Pillow), quotes library and the redesigned pages."""
import asyncio
import io
import re
from markupsafe import escape  # same escaping as the Jinja templates
from pathlib import Path

import pytest
from PIL import Image

from app import models
from app.services import images, themes
from app.services.catalog import MODULES, SIZES, image_setting, normalize
from app.services.planner import assign_quotes, build_plan
from app.services.render import LINK_PREFIX, Renderer

QUOTES = [{"id": i, "text": t, "author": a, "category": c} for i, (t, a, c) in enumerate(models.SEED_QUOTES)]
NOV = {"period": "month", "period_year": 2026, "period_month": 11}


def page_of(plan, kind):
    return next(p for p in plan.pages if p.kind == kind)


# ------------------------------------------------------------- contrast
def test_contrast_ratio_matches_wcag():
    assert themes.contrast("#000000", "#FFFFFF") == 21.0
    assert themes.contrast("#FFFFFF", "#FFFFFF") == 1.0
    assert themes.contrast("#777777", "#FFFFFF") == pytest.approx(4.48, abs=0.01)
    assert themes.contrast("#2A93B3", "#FFFCF8") == pytest.approx(3.47, abs=0.01)


@pytest.mark.parametrize("fg, bg", [("#93E2F0", "#FFFCF8"), ("#F7C6D2", "#FFFFFF"), ("#1D4E5F", "#22343C"), ("#777777", "#808080")])
def test_fix_contrast_reaches_minimum(fg, bg):
    fixed = themes.fix_contrast(fg, bg, 4.5)
    assert themes.contrast(fixed, bg) >= 4.5
    assert themes.fix_contrast("#1D4E5F", "#FFFCF8") == "#1D4E5F"  # already fine: unchanged


def test_brand_defaults_are_readable():
    assert themes.contrast_issues(normalize({})["theme"]) == []
    for preset in themes.PRESETS:
        t = themes.resolve({"preset": preset})
        assert themes.contrast(t["primary"], t["background"]) >= 4.5
        assert themes.contrast(t["ink"], t["background"]) >= 4.5
        # small accent-coloured text is auto-darkened to stay readable
        assert themes.contrast(t["accent_text"], t["card"]) >= 4.5


def test_contrast_guard_flags_and_fixes_per_page_colours():
    theme = {"preset": "brand", "pages": {"week": {"background": "#FFE59A", "body": "#F7C6D2"},
                                          "cover": {"background": "#1D4E5F"}}}
    issues = themes.contrast_issues(theme)
    found = {(i["group"], i["role"]) for i in issues}
    assert ("week", "body") in found and ("cover", "heading") in found
    assert ("all", "heading") not in found
    for i in issues:
        assert i["ratio"] < i["minimum"] and themes.contrast(i["fix"], i["background"]) >= i["minimum"]
        key = {"heading": "heading", "body": "body", "accent": "accent"}[i["role"]]
        theme["pages"].setdefault(i["group"], {})[key] = i["fix"]
    assert themes.contrast_issues(theme) == []


# ---------------------------------------------------------- page colours
def test_global_and_per_page_colours():
    cfg = {"planner_type": "daily", "calendar": NOV,
           "theme": {"background": "#FFFFFF", "primary": "#223344", "ink": "#333333", "accent": "#AA3366",
                     "pages": {"week": {"background": "#FFF1F4", "heading": "#5A1F33"}, "cover": {"background": "#EAF8FC"}}}}
    plan = build_plan(cfg)
    r = Renderer(plan, "A4", "digital")
    assert r.theme["background"] == "#FFFFFF" and r.theme["ink"] == "#333333"
    week = r.page_theme(page_of(plan, "week"))
    assert (week["background"], week["primary"], week["ink"], week["accent"]) == ("#FFF1F4", "#5A1F33", "#333333", "#AA3366")
    html = r.document([page_of(plan, "week"), page_of(plan, "month"), page_of(plan, "cover")])
    sections = re.findall(r'<section class="page pg-(\w+)"[^>]*style="([^"]*)"', html)
    styles = dict(sections)
    assert "--bg:#FFF1F4" in styles["week"] and "--primary:#5A1F33" in styles["week"]
    assert "--bg:#EAF8FC" in styles["cover"]
    assert "--bg:" not in styles["month"]          # month uses the global colours from :root
    assert "--bg: #FFFFFF" in html                 # global background
    # derived soft tints follow the new background
    assert week["fill"] != r.theme["fill"]


def test_colour_settings_survive_normalize():
    theme = {"preset": "pastel", "ink": "#222222", "motif": False, "pages": {"day": {"accent": "#2A93B3"}}}
    cfg = normalize({"theme": theme})
    assert cfg["theme"]["pages"]["day"]["accent"] == "#2A93B3" and cfg["theme"]["ink"] == "#222222"
    assert cfg["theme"]["motif"] is False
    assert normalize(cfg) == cfg


def test_invalid_colours_are_ignored():
    t = themes.resolve({"preset": "brand", "background": "#GGGGGG", "primary": "red", "pages": {"day": {"background": "#12"}}},
                       group="day")
    assert t["background"] == themes.PRESETS["sky_classic"]["background"] and t["primary"] == themes.PRESETS["sky_classic"]["primary"]


# --------------------------------------------------------------- pictures
def _png(w, h, alpha=False):
    im = Image.new("RGBA" if alpha else "RGB", (w, h), (147, 226, 240, 120) if alpha else (247, 198, 210))
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


def _jpg(w, h, exif_orientation=None):
    im = Image.new("RGB", (w, h), (42, 147, 179))
    buf = io.BytesIO()
    if exif_orientation:
        exif = Image.Exif()
        exif[0x0112] = exif_orientation
        im.save(buf, "JPEG", quality=95, exif=exif)
    else:
        im.save(buf, "JPEG", quality=95)
    return buf.getvalue()


def test_upload_is_resized_and_compressed():
    data, ext, size = images.process_upload(_jpg(5000, 3000), "photo.JPG")
    assert ext == ".jpg" and max(size) == images.UPLOAD_MAX_PX
    assert Image.open(io.BytesIO(data)).size == (2400, 1440)


def test_upload_keeps_transparency_and_fixes_rotation():
    data, ext, _ = images.process_upload(_png(800, 400, alpha=True), "logo.png")
    assert ext == ".png" and Image.open(io.BytesIO(data)).mode == "RGBA"
    # a PNG without transparency is stored as a smaller JPG
    assert images.process_upload(_png(800, 400), "flat.png")[1] == ".jpg"
    # phone photo stored sideways (EXIF orientation 6) is turned upright
    _, _, size = images.process_upload(_jpg(600, 400, exif_orientation=6), "phone.jpg")
    assert size == (400, 600)


@pytest.mark.parametrize("name, data", [("x.gif", b"GIF89a"), ("x.webp", b"RIFF"), ("x.png", b"not an image")])
def test_upload_rejects_other_files(name, data):
    with pytest.raises(ValueError):
        images.process_upload(data, name)


def test_pdf_copy_downscales(tmp_path):
    src = tmp_path / "big.jpg"
    src.write_bytes(_jpg(2400, 1600))
    out = images.pdf_copy(src, tmp_path, 700)
    assert max(Image.open(out).size) == 700 and out.stat().st_size < src.stat().st_size


def test_image_settings_are_validated():
    cfg = normalize({"images": {"cover": {"asset": "a.jpg", "mode": "sideways", "fit": "stretch", "opacity": 7, "shape": "star"},
                                "month_header": {"asset": "b.jpg", "position": "middle", "opacity": "x"}}})
    c = image_setting(cfg, "cover")
    assert (c["mode"], c["fit"], c["opacity"], c["shape"], c["position"]) == ("framed", "cover", 1.0, "rounded", "center")
    m = image_setting(cfg, "month_header")
    assert (m["position"], m["opacity"]) == ("right", 1.0)
    assert image_setting(cfg, "divider") is None
    assert image_setting(normalize({"images": {"cover": {"asset": "a.jpg", "opacity": 0}}}), "cover")["opacity"] == 0.1


def test_old_cover_image_setting_is_migrated():
    cfg = normalize({"personalization": {"cover_image": "old.jpg"}})
    assert cfg["images"]["cover"]["asset"] == "old.jpg"


@pytest.mark.parametrize("mode", ["framed", "full"])
def test_cover_and_month_header_pictures_render(mode):
    cfg = {"planner_type": "daily", "calendar": NOV, "modules": {"divider": True, "notes": True},
           "images": {"cover": {"asset": "c.jpg", "mode": mode, "fit": "contain", "opacity": 0.6, "shape": "circle"},
                      "divider": {"asset": "c.jpg", "mode": "full"},
                      "month_header": {"asset": "m.jpg", "position": "banner", "shape": "rounded"}}}
    plan = build_plan(cfg)
    r = Renderer(plan, "A4", "digital", asset_base="/assets")
    cover = r.document([page_of(plan, "cover")])
    assert 'src="/assets/c.jpg"' in cover and "object-fit:contain" in cover and "opacity:0.6" in cover
    assert ('class="img-full' in cover) == (mode == "full") and ('class="cover-wrap has-full"' in cover) == (mode == "full")
    assert "shape-circle" in cover
    month = r.document([page_of(plan, "month")])
    assert 'class="ph-banner shape-rounded"' in month and 'src="/assets/m.jpg"' in month
    assert 'class="img-full shape-rounded"' in r.document([page_of(plan, "divider")])


# ---------------------------------------------------------------- quotes
def test_seed_library():
    assert len(models.SEED_QUOTES) >= 60
    cats = {c for _, _, c in models.SEED_QUOTES}
    assert cats == set(models.QUOTE_CATEGORIES)
    assert all(len(t) <= 240 for t, _, _ in models.SEED_QUOTES)
    assert len({t for t, _, _ in models.SEED_QUOTES}) == len(models.SEED_QUOTES)


def test_quote_modes():
    plan = build_plan({"planner_type": "daily", "calendar": NOV, "quotes": {"mode": "none"}}, [], QUOTES)
    assert plan.quote_of == {}
    plan = build_plan({"planner_type": "daily", "calendar": NOV, "quotes": {"mode": "per_type"}}, [], QUOTES)
    by_kind = {}
    for p in plan.pages:
        if p.id in plan.quote_of:
            by_kind.setdefault(p.kind, set()).add(plan.quote_of[p.id]["text"])
    assert set(by_kind) == {"cover", "month", "week", "day"}
    assert all(len(v) == 1 for v in by_kind.values())                     # one per page type …
    assert len({next(iter(v)) for v in by_kind.values()}) == 4            # … and different between types
    plan = build_plan({"planner_type": "daily", "calendar": NOV, "quotes": {"mode": "per_page"}}, [], QUOTES)
    texts = [plan.quote_of[p.id]["text"] for p in plan.pages if p.id in plan.quote_of]
    assert len(texts) == 1 + 1 + 6 + 30 and len(set(texts)) == len(texts)   # different on every page


def test_quote_page_toggles_and_empty_library():
    plan = build_plan({"planner_type": "daily", "calendar": NOV,
                       "quotes": {"mode": "per_page", "pages": {"day": False, "cover": False}}}, [], QUOTES)
    assert {p.kind for p in plan.pages if p.id in plan.quote_of} == {"month", "week"}
    assert assign_quotes({"quotes": {"mode": "per_page"}}, plan.pages, []) == {}


def test_quotes_are_printed():
    plan = build_plan({"planner_type": "daily", "calendar": NOV, "quotes": {"mode": "per_page"}}, [], QUOTES)
    r = Renderer(plan, "A4", "digital")
    for kind, cls in (("cover", "quote-card"), ("month", "quote-strip"), ("week", "quote-strip"), ("day", "day-quote")):
        p = page_of(plan, kind)
        html = r.document([p])
        assert f'class="{cls}"' in html and escape(plan.quote_of[p.id]["text"]) in html


def test_quote_api_crud():
    from fastapi import HTTPException
    from app.routers import library as L
    models.init_db()
    lib = L.list_quotes()
    assert len(lib) >= 60
    q = L.add_quote(L.QuoteIn(text="  My own little affirmation.  ", category="hope"))
    assert q["text"] == "My own little affirmation." and q["kind"] == "affirmation"
    q = L.update_quote(q["id"], L.QuoteIn(**{**q, "text": "Edited.", "author": "Me", "kind": "quote"}))
    assert (q["text"], q["author"], q["kind"]) == ("Edited.", "Me", "quote")
    for bad in ("   ", "x" * 241):
        with pytest.raises(HTTPException):
            L.add_quote(L.QuoteIn(text=bad))
    assert L.delete_quote(q["id"]) == {"ok": True}
    assert len(L.list_quotes()) == len(lib)


def test_asset_upload_api_compresses():
    from fastapi import HTTPException, UploadFile
    from app.routers import library as L
    big = _jpg(4000, 3000)
    r = asyncio.run(L.upload_asset(UploadFile(io.BytesIO(big), filename="big.jpg")))
    assert r["width"] == 2400 and r["bytes"] < r["original_bytes"]
    assert (models.ASSET_DIR / r["name"]).exists()
    with pytest.raises(HTTPException):
        asyncio.run(L.upload_asset(UploadFile(io.BytesIO(b"GIF89a"), filename="a.gif")))

# ------------------------------------------------------------- dividers
def test_divider_pages_open_each_section_and_links_resolve():
    plan = build_plan({"planner_type": "daily", "modules": {"divider": True, "goal_vision": True, "notes": True},
                       "calendar": {"start_year": 2027, "start_month": 1, "end_year": 2027, "end_month": 1}}, [], QUOTES)
    ids = {p.id for p in plan.pages}
    divs = [p for p in plan.pages if p.kind == "divider"]
    assert [d.data["label"] for d in divs] == ["2027", "Goals", "Notes"]
    for label, tid in plan.sections:
        assert tid.startswith("div-")
    html = Renderer(plan, "A4", "digital").document()
    assert not set(re.findall(re.escape(LINK_PREFIX) + r'([^"]+)"', html)) - ids


# ------------------------------------------------------ clipping (Chromium)
PHOTO = None


def _photo(tmp_path_factory):
    global PHOTO
    if not PHOTO:
        p = tmp_path_factory.mktemp("img") / "photo.jpg"
        Image.new("RGB", (1600, 1100), (234, 248, 252)).save(p, quality=85)
        PHOTO = p.resolve().as_uri()
    return PHOTO


@pytest.mark.slow
def test_clipping_check_catches_spills():
    """Cards don't clip their content, so the check must notice text or checkboxes spilling out of a card."""
    from app.services import pdf
    plan = build_plan({"planner_type": "daily", "calendar": NOV})
    day = page_of(plan, "day")

    class Squashed(Renderer):
        def css(self):
            return super().css() + ".box{flex:none!important;height:2.2rem!important}"
    try:
        with pdf.browser() as b:
            assert pdf.clipping_report(b, Renderer(plan, "A4", "digital"), [day]) == []
            found = pdf.clipping_report(b, Squashed(plan, "A4", "digital"), [day])
    except pdf.EngineError as e:
        pytest.skip(str(e))
    assert {i["what"] for i in found} & {"clipped", "spills"}


@pytest.mark.slow
@pytest.mark.parametrize("theme", list(themes.PRESETS))
def test_no_clipping_any_size(theme, tmp_path_factory):
    """Every page kind, every size, digital + printable, with quotes, pictures and per-page colours: nothing cut off."""
    from app.services import pdf
    photo = _photo(tmp_path_factory)
    longest = sorted(QUOTES, key=lambda q: -len(q["text"]))
    imgs = {"cover": {"asset": "p.jpg", "mode": "framed"}, "divider": {"asset": "p.jpg", "mode": "full"},
            "month_header": {"asset": "p.jpg", "position": "banner"}}
    cfgs = [{"planner_type": "daily", "modules": {k: True for k in MODULES}, "quotes": {"mode": "per_page"}, "images": imgs,
             "calendar": {"start_year": 2027, "start_month": 1, "end_year": 2027, "end_month": 2},
             "personalization": {"name": "Ayesha Bint Muhammad Al-Very-Long-Name", "mode": "throughout"}},
            {"planner_type": "daily", "modules": {"month_habits": True, "goal_review": True, "divider": True},
             "quotes": {"mode": "per_type"}, "calendar": NOV,
             "images": {**imgs, "cover": {"asset": "p.jpg", "mode": "full"}, "month_header": {"asset": "p.jpg", "position": "left"}}},
            # Islamic pages, Arabic (RTL) and the Hijri calendar
            {"planner_type": "namaz", "modules": {"dua_list": True, "month": True, "ramadan_tracker": True, "ramadan_day": True,
                                                  "last_ten": True, "juz_tracker": True, "khatam": True},
             "calendar": {"mode": "hijri", "period": "month", "period_year": 1448, "period_month": 9}, "quotes": {"mode": "per_page"}}]
    duas = [{"title": "Dua", "arabic": "بِاسْمِكَ اللَّهُمَّ أَمُوتُ وَأَحْيَا", "english": "In Your name O Allah, I die and I live.",
             "reference": "Bukhari", "verified": True}] * 3
    problems = []
    try:
        with pdf.browser() as b:
            for cfg in cfgs:
                plan = build_plan({**cfg, "theme": {"preset": theme, "pages": {"cover": {"background": "#1D4E5F", "heading": "#FFFCF8",
                                                                                         "body": "#EAF8FC"}}}}, duas, longest)
                sample = list({p.kind: p for p in reversed(plan.pages)}.values())
                for size in SIZES:
                    for variant in ("digital", "printable"):
                        r = Renderer(plan, size, variant, font_base=themes.FONT_DIR.resolve().as_uri(), asset_map={"p.jpg": photo})
                        problems += [(size, variant, i["page"], i["what"], i["text"]) for i in pdf.clipping_report(b, r, sample)]
    except pdf.EngineError as e:
        pytest.skip(str(e))
    assert not problems, problems[:10]
