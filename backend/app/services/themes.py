"""Template styles (theme presets), bundled fonts and the resolved style for a project."""
from __future__ import annotations

import json
from pathlib import Path

FONT_DIR = Path(__file__).resolve().parent.parent / "fonts"

# family -> list of (file, weight-range, style)
FONTS = {
    "Inter": [("Inter.ttf", "100 900")],
    "Poppins": [("Poppins-Regular.ttf", "400"), ("Poppins-SemiBold.ttf", "600 700")],
    "Playfair Display": [("PlayfairDisplay.ttf", "400 900")],
    "Lora": [("Lora.ttf", "400 700")],
    "Dancing Script": [("DancingScript.ttf", "400 700")],
    "Great Vibes": [("GreatVibes-Regular.ttf", "400")],
    "Caveat": [("Caveat.ttf", "400 700")],
    "Amiri": [("Amiri-Regular.ttf", "400"), ("Amiri-Bold.ttf", "700")],
    "Noto Naskh Arabic": [("NotoNaskhArabic.ttf", "400 700")],
    "Scheherazade New": [("ScheherazadeNew-Regular.ttf", "400"), ("ScheherazadeNew-Bold.ttf", "700")],
}
ENGLISH_FONTS = ["Inter", "Poppins", "Playfair Display", "Lora", "Dancing Script", "Great Vibes", "Caveat"]
ARABIC_FONTS = ["Amiri", "Noto Naskh Arabic", "Scheherazade New"]
SCRIPT_FONTS = {"Dancing Script", "Great Vibes", "Caveat"}

# Productivity Shop by M brand palette
BRAND = {
    "sky": "#93E2F0", "deep_sky": "#2A93B3", "ink": "#1D4E5F", "text": "#35535E", "cream": "#FFFCF8",
    "soft_sky": "#EAF8FC", "blush": "#F7C6D2", "blush_soft": "#FFF1F4", "butter": "#FFE59A", "butter_soft": "#FFF8E0",
}


def extra_fonts() -> dict:
    """Fonts dropped into backend/app/fonts/extra/ (see README: 'Adding fonts')."""
    out = {}
    d = FONT_DIR / "extra"
    if d.exists():
        for f in sorted(d.iterdir()):
            if f.suffix.lower() in (".ttf", ".otf", ".woff2", ".woff"):
                fam = f.stem.split("-")[0].replace("_", " ")
                out.setdefault(fam, []).append((f"extra/{f.name}", "100 900"))
    return out


def all_fonts() -> dict:
    return {**FONTS, **extra_fonts()}


def font_faces_css(base_url: str) -> str:
    css = []
    for fam, files in all_fonts().items():
        for fname, weight in files:
            css.append(
                f"@font-face{{font-family:'{fam}';src:url('{base_url}/{fname}');font-weight:{weight};font-style:normal;font-display:block}}"
            )
    return "\n".join(css)


# ---------------------------------------------------------------- templates
# Each template style is data: backend/app/styles/<key>.json (+ optional <key>.css with small extra rules).
# To add a template, drop in a new JSON file – see README "Adding a template style".
STYLE_DIR = Path(__file__).resolve().parent.parent / "styles"
CARD_STYLES = ("soft", "lines")          # rounded soft cards | thin rules, no card backgrounds
COVER_LAYOUTS = ("panel", "bloom", "editorial")
MOTIFS = ("bow", "flower", "none")
REQUIRED_COLORS = ("primary", "accent", "background", "ink", "muted", "fill", "line")


def _template_to_preset(key: str, d: dict, css: str = "") -> dict:
    """Flatten a template JSON definition into the preset dict used by resolve()."""
    missing = [c for c in REQUIRED_COLORS if c not in (d.get("colors") or {})]
    if missing or not d.get("label"):
        raise ValueError(f"Template style '{key}' is missing {missing or 'a label'}")
    f = d.get("fonts") or {}
    p = {**d["colors"],
         "label": d["label"], "description": d.get("description", ""), "featured": bool(d.get("featured")),
         "order": d.get("order", 99), "aliases": d.get("aliases", []),
         "title_font": f.get("title", "Playfair Display"), "heading_font": f.get("heading", f.get("title", "Playfair Display")),
         "body_font": f.get("body", "Poppins"), "script_font": f.get("script", f.get("body", "Poppins")),
         "title_scale": float(d.get("title_scale", 1.0)), "corner": d.get("corner", "rounded"),
         "cards": d.get("cards") if d.get("cards") in CARD_STYLES else "soft",
         "cover_layout": d.get("cover") if d.get("cover") in COVER_LAYOUTS else "panel",
         "decoration": d.get("decoration", "bow"), "motif_kind": d.get("motif") if d.get("motif") in MOTIFS else "bow",
         "accent_role": "decorative" if d.get("accent_role") == "decorative" else "graphic",
         "swatches": d.get("swatches") or [d["colors"]["primary"], d["colors"]["accent"], d["colors"]["background"]],
         "css": css}
    if d.get("rainbow"):
        p["rainbow"] = d["rainbow"]
    return p


def load_templates(folder: Path = STYLE_DIR) -> tuple[dict, dict]:
    """(presets by key, alias -> key), ordered by each template's 'order'."""
    found = {}
    for jf in sorted(folder.glob("*.json")):
        key = jf.stem
        css_file = jf.with_suffix(".css")
        found[key] = _template_to_preset(key, json.loads(jf.read_text(encoding="utf-8")),
                                         css_file.read_text(encoding="utf-8") if css_file.exists() else "")
    presets = dict(sorted(found.items(), key=lambda kv: (kv[1]["order"], kv[0])))
    aliases = {a: k for k, p in presets.items() for a in p["aliases"]}
    return presets, aliases


PRESETS, ALIASES = load_templates()
DEFAULT_PRESET = "sky_classic"


def template_key(name: str | None) -> str:
    """Template key for a stored preset name (old 'brand' projects map to Sky Classic)."""
    name = ALIASES.get(name or "", name)
    return name if name in PRESETS else DEFAULT_PRESET


def featured_templates() -> list[str]:
    return [k for k, p in PRESETS.items() if p["featured"]]


CORNERS = {"square": 0, "soft": 6, "rounded": 14, "bubbly": 22}


def _mix(hex1: str, hex2: str, t: float) -> str:
    a = [int(hex1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(hex2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b))


def _valid_hex(v) -> bool:
    if not (isinstance(v, str) and len(v) == 7 and v.startswith("#")):
        return False
    try:
        int(v[1:], 16)
        return True
    except ValueError:
        return False


# ------------------------------------------------------------ contrast (WCAG 2.x)
TEXT_MIN = 4.5     # normal body / heading text
ACCENT_MIN = 3.0   # accent is used for bands, icons and large hand-lettering; small accent text is auto-darkened


def luminance(hex_color: str) -> float:
    def ch(c: int) -> float:
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(fg: str, bg: str) -> float:
    a, b = sorted((luminance(fg), luminance(bg)), reverse=True)
    return round((a + 0.05) / (b + 0.05), 2)


def fix_contrast(fg: str, bg: str, minimum: float = TEXT_MIN) -> str:
    """Nudge fg toward black (light background) or white (dark background) until it is readable."""
    if contrast(fg, bg) >= minimum:
        return fg.upper()
    target = "#000000" if luminance(bg) > 0.18 else "#FFFFFF"
    for step in range(1, 51):
        c = _mix(fg, target, step / 50)
        if contrast(c, bg) >= minimum:
            return c
    return target


# Page types whose colours can be overridden, and the page kinds that belong to each.
PAGE_GROUPS = {
    "cover": ["cover", "divider"],
    "month": ["month", "month_goals", "goal_review"],
    "week": ["week", "namaz_week"],
    "day": ["day"],
    "habits": ["month_habits"],
    "notes": ["notes"],
}
GROUP_OF = {kind: g for g, kinds in PAGE_GROUPS.items() for kind in kinds}
COLOR_ROLES = {"background": "background", "heading": "primary", "body": "ink", "accent": "accent"}


def page_overrides(theme_cfg: dict, group: str | None) -> dict:
    """Theme config with one page type's colour overrides applied (heading → primary, body → ink)."""
    over = ((theme_cfg.get("pages") or {}).get(group) or {}) if group else {}
    merged = dict(theme_cfg)
    for role, key in COLOR_ROLES.items():
        if _valid_hex(over.get(role)):
            merged[key] = over[role]
    return merged


def contrast_issues(theme_cfg: dict) -> list[dict]:
    """Every heading / body / accent colour that is hard to read on its page background."""
    out = []
    for group in [None] + list(PAGE_GROUPS):
        if group and not (theme_cfg.get("pages") or {}).get(group):
            continue
        t = resolve(theme_cfg, group=group)
        checks = [("heading", "primary", TEXT_MIN), ("body", "ink", TEXT_MIN)]
        if t["accent_role"] != "decorative":  # decorative accents (e.g. Ink & Gold's gold rules) never carry meaning
            checks.append(("accent", "accent", ACCENT_MIN))
        for role, key, minimum in checks:
            ratio = contrast(t[key], t["background"])
            if ratio < minimum:
                out.append({"group": group or "all", "role": role, "color": t[key], "background": t["background"],
                            "ratio": ratio, "minimum": minimum, "fix": fix_contrast(t[key], t["background"], minimum)})
    return out


def resolve(theme_cfg: dict, ink_saving: bool = False, group: str | None = None) -> dict:
    """Full colour + font set for a project; `group` applies that page type's colour overrides."""
    key = template_key(theme_cfg.get("preset"))
    preset = PRESETS[key]
    t = dict(preset)
    t["preset"] = key
    theme_cfg = page_overrides(theme_cfg, group)
    for k in ("primary", "accent", "background", "ink"):
        if _valid_hex(theme_cfg.get(k)):
            t[k] = theme_cfg[k].upper()
    new_accent = _valid_hex(theme_cfg.get("accent"))
    new_bg = _valid_hex(theme_cfg.get("background"))
    fonts = all_fonts()
    if theme_cfg.get("heading_font") in fonts:
        t["heading_font"] = theme_cfg["heading_font"]
        if t["title_font"] not in SCRIPT_FONTS:
            t["title_font"] = theme_cfg["heading_font"]
    if theme_cfg.get("body_font") in fonts:
        t["body_font"] = theme_cfg["body_font"]
    corner = theme_cfg.get("corner") or t["corner"]
    t["radius"] = CORNERS.get(corner, 6)
    t["line_style"] = theme_cfg.get("line_style") or "lined"
    # Derived soft tints.  A new accent re-tints them from the accent; a new background blends the preset's
    # own tints toward it (so a blush or butter page keeps the palette's character instead of turning grey).
    if new_accent:
        t["fill"] = _mix(t["accent"], t["background"], 0.88)
        t["line"] = _mix(t["accent"], t["background"], 0.70)
        t["fill_strong"] = _mix(t["accent"], t["background"], 0.78)
    elif new_bg:
        for k in ("fill", "line", "fill_strong"):
            if k in preset:
                t[k] = _mix(preset[k], t["background"], 0.25 if k == "line" else 0.35)
    if new_bg:
        t["muted"] = _mix(t["ink"], t["background"], 0.30)
        for k, base in (("highlight_soft", "highlight"), ("note_soft", "note")):
            if base in t:
                t[k] = _mix(t[base], t["background"], 0.72)
    if "fill_strong" not in t:
        t["fill_strong"] = _mix(t["primary"], t["background"], 0.82)
    t["accent_soft"] = _mix(t["accent"], t["background"], 0.80)
    dark = luminance(t["background"]) < 0.18
    t["card"] = _mix(t["background"], "#FFFFFF", 0.06 if dark else 0.55)
    # small text in the accent colour is darkened (or lightened) just enough to stay readable
    t["accent_text"] = fix_contrast(t["accent"], t["card"], TEXT_MIN)
    t["muted"] = fix_contrast(t["muted"], t["card"], TEXT_MIN)
    t["on_accent"] = "#FFFFFF" if contrast("#FFFFFF", t["accent"]) >= contrast(t["primary"], t["accent"]) else t["primary"]
    t["motif"] = theme_cfg.get("motif", True) is not False and t["motif_kind"] != "none"
    # checkboxes, rings and other marks you write in: the accent, unless the template's accent is purely decorative
    t["mark"] = t["accent"] if t["accent_role"] != "decorative" else t["primary"]
    t["ink_saving"] = ink_saving
    if ink_saving:
        t["fill"] = t["background"]
        t["fill_strong"] = _mix(t["primary"], t["background"], 0.95)
        t["accent_soft"] = _mix(t["accent"], t["background"], 0.93)
        t["line"] = _mix(t["line"], t["background"], 0.25)
    t.setdefault("rainbow", [t["accent"]] * 12)
    t.setdefault("script_font", t["body_font"])
    t.setdefault("highlight", t["accent"])
    t.setdefault("highlight_soft", t["accent_soft"])
    t.setdefault("note_soft", t["fill"])
    t.setdefault("sky", t["accent_soft"])
    if ink_saving:
        t["card"] = t["background"]
        t["highlight_soft"] = _mix(t["highlight_soft"], t["background"], 0.6)
    t["arabic_font"] = "Amiri"
    return t
