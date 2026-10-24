"""Etsy listing images (PNG) built from Playwright screenshots of real planner pages."""
from __future__ import annotations

from pathlib import Path

from . import pdf, themes
from .catalog import MODULES, SIZES
from .render import Renderer, env, fit
from markupsafe import Markup

SIZE_SHORT = {"A4": "A4", "Letter": "US Letter", "A5": "A5", "HalfLetter": "Half Letter",
              "iPadPortrait": "iPad", "iPadLandscape": "iPad Landscape"}


def inside_list(plan) -> list[str]:
    counts: dict = {}
    for p in plan.pages:
        counts[p.kind] = counts.get(p.kind, 0) + 1
    out = []
    for kind, n in counts.items():
        if kind in ("cover",):
            continue
        if plan.undated and kind in ("month", "week", "day"):
            out.append(f"Undated {MODULES[kind]['label'].lower()} ({n})" if n > 1 else f"Undated {MODULES[kind]['label'].lower()}")
            continue
        lbl = MODULES[kind]["label"]
        out.append(f"{lbl} ({n})" if n > 1 else lbl)
    return out


def _pick(plan, kinds):
    for k in kinds:
        for p in plan.pages:
            if p.kind == k:
                return p
    return None


def compare_shots(b, cfg: dict, plan, quotes: list, size_key: str, shot, font_base: str, asset_map: dict,
                  brand_logo: str | None) -> list[dict]:
    """Cover + month page of this planner in every featured template (their default colours)."""
    import copy
    from .planner import build_plan
    out = []
    for key in themes.featured_templates():
        c = copy.deepcopy(plan.cfg)
        c["theme"] = {"preset": key, "line_style": cfg["theme"].get("line_style", "lined")}
        p = build_plan(c, plan.duas, quotes)
        r = Renderer(p, size_key, "digital", font_base=font_base, asset_map=asset_map, brand_logo=brand_logo)
        cover = _pick(p, ["cover", "index"]) or p.pages[0]
        inner = _pick(p, ["month", "week", "day", "year_overview", "namaz_month", "goal_smart", "notes"]) or cover
        out.append({"key": key, "label": themes.PRESETS[key]["label"], "cover": shot(cover, f"cmp-{key}-cover", r),
                    "inner": shot(inner, f"cmp-{key}-inner", r), "swatches": themes.PRESETS[key]["swatches"][:5],
                    "current": key == themes.template_key(cfg["theme"].get("preset"))})
    return out


def generate(b, plan, cfg: dict, size_key: str, variants: list, sizes: list, out_dir: Path,
             font_base: str, asset_map: dict, progress=None, brand_logo: str | None = None,
             quotes: list | None = None) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    shot_dir = out_dir / "_shots"
    shot_dir.mkdir(exist_ok=True)
    has_digital = "digital" in variants
    r = Renderer(plan, size_key, "digital" if has_digital else "printable", font_base=font_base, asset_map=asset_map,
                 brand_logo=brand_logo)
    g = r.geom
    scale = 1.6

    def shot(page, name, renderer=None):
        rr = renderer or r
        f = shot_dir / f"{name}.png"
        pdf.screenshot_html(b, rr.document([page]), g["w"], g["h"], f, scale, ".page")
        return f.as_uri()

    cover = _pick(plan, ["cover", "index"]) or plan.pages[0]
    interesting = ["month", "week", "day", "year_overview", "namaz_month", "ramadan_day", "dua_list", "goal_smart",
                   "affirmations", "juz_tracker", "surah_checklist", "month_habits", "quarter", "gratitude",
                   "ramadan_tracker", "vision_board", "method369", "dua_journal", "reflection", "notes"]
    grid_pages, seen = [], set()
    for k in interesting:
        p = _pick(plan, [k])
        if p and p.kind not in seen:
            grid_pages.append(p)
            seen.add(p.kind)
        if len(grid_pages) >= 6:
            break
    while len(grid_pages) < 6 and len(grid_pages) < len(plan.pages):
        extra = [p for p in plan.pages if p not in grid_pages]
        if not extra:
            break
        grid_pages.append(extra[0])
    shots = {"cover": shot(cover, "cover"), "grid": []}
    for i, p in enumerate(grid_pages):
        shots["grid"].append(shot(p, f"g{i}"))
        if progress:
            progress(0.1 + 0.5 * (i + 1) / len(grid_pages))
    shots["second"] = shots["grid"][0] if shots["grid"] else shots["cover"]
    link_page = _pick(plan, ["month", "year_overview", "week", "index"]) or cover
    shots["links"] = shot(link_page, "links")

    t = r.theme  # the selected template (plus any custom colours)
    L = cfg["listing"]
    headline = L.get("headline") or (f"{r.year_label()} {r.cover_title()}".strip() if not plan.undated
                                      else f"Undated {r.cover_title()}")
    variants_text = " + ".join({"digital": "Digital hyperlinked", "printable": "Printable"}[v] for v in variants)
    size_items = [{"key": k, "w": SIZES[k][1], "h": SIZES[k][2], "short": SIZE_SHORT[k]} for k in sizes]
    pers = cfg["personalization"]
    kinds = ["cover", "collage", "inside", "sizes"]
    if has_digital:
        kinds.append("links")
    kinds.append("colors")
    if pers.get("name"):
        kinds.append("personal")
    compare = []
    if len(themes.featured_templates()) > 1:
        kinds.append("compare")
        compare = compare_shots(b, cfg, plan, quotes or list(plan.quote_of.values()), size_key, shot, font_base, asset_map, brand_logo)
    dims = [(2000, 2000, "")]
    if cfg["output"].get("listing_landscape"):
        dims.append((2700, 2025, "_2700x2025"))
    files = []
    tpl = env.get_template("listing/listing.html")
    total = len(kinds) * len(dims)
    n = 0
    for W, H, sfx in dims:
        for i, kind in enumerate(kinds, 1):
            html = tpl.render(kind=kind, W=W, H=H, t=t, L=L, headline=headline, shots=shots, fit=lambda s, b, m: f"{b * min(1, m / max(1, len(s))):.0f}px",
                              img_ratio=g["w"] / g["h"], page_count=len(plan.pages), inside=inside_list(plan),
                              sizes=size_items, variants_text=variants_text, has_digital=has_digital,
                              swatches=t.get("swatches", [])[:6] if not cfg["theme"].get("primary") else
                              [t["primary"], t["accent"], t["line"], t["fill"], t["background"]],
                              personal_throughout=pers.get("mode") == "throughout",
                              logo=r.asset_url(brand_logo) if brand_logo else None, short=plan.short, compare=compare,
                              undated=plan.undated, font_faces=Markup(themes.font_faces_css(font_base)))
            f = out_dir / f"{i:02d}-{kind}{sfx}.png"
            pdf.screenshot_html(b, html, W, H, f, 1.0)
            files.append(f)
            n += 1
            if progress:
                progress(0.6 + 0.4 * n / total)
    for f in shot_dir.iterdir():
        f.unlink()
    shot_dir.rmdir()
    return files


def thumbnail(b, plan, font_base: str, asset_map: dict, out: Path, size_key: str = "A4"):
    r = Renderer(plan, size_key, "printable", font_base=font_base, asset_map=asset_map)
    g = r.geom
    p = plan.pages[0]
    pdf.screenshot_html(b, r.document([p]), g["w"], g["h"], out, 0.5, ".page")
