"""Jinja2 rendering of planner pages to HTML (shared by preview and PDF export)."""
from __future__ import annotations

import html
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

from . import themes
from .calendar import WEEKDAYS, WEEKDAYS_SHORT, WEEKDAYS_LETTER
from .catalog import LABELS, PLANNER_TYPES, PRAYERS, SIZES, normalize
from .planner import Plan

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
LINK_PREFIX = "https://planner-studio.local/p/"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def possessive(name: str) -> str:
    name = name.strip()
    return f"{name}'" if name.lower().endswith("s") else f"{name}'s"


def fit(text: str, base: float, max_chars: int, minimum: float = 0.45) -> str:
    """Return a CSS font-size (rem) that shrinks for long text so it never overflows."""
    n = len(text or "")
    scale = 1.0 if n <= max_chars else max(minimum, max_chars / n)
    return f"{base * scale:.3f}rem"


def geometry(size_key: str, variant: str, cfg: dict, has_footer: bool) -> dict:
    _, w, h = SIZES[size_key]
    small = w < 700 or h < 700
    landscape = w > h
    rem = min(w, h / 1.414) / (52 if small or landscape else 60)
    out = cfg["output"]
    if variant == "printable":
        m = 36 if small else 48
        g = {"mt": m, "mr": m, "mb": m - 8, "ml": m + (34 if out.get("binder_margin") else 0), "tabs_w": 0, "top_h": 0}
    else:
        m = 20 if small else 26
        g = {"mt": m - 6, "mr": 0, "mb": m - 10, "ml": m, "tabs_w": round(w * (0.045 if landscape else 0.06)),
             "top_h": round(rem * 2.2)}
        g["gap_r"] = round(m * 0.6)
    g.update(w=w, h=h, rem=round(rem, 3), small=small, landscape=landscape,
             foot_h=round(rem * 1.6) if has_footer else 0)
    return g


class Renderer:
    def __init__(self, plan: Plan, size_key: str, variant: str, *, link_mode: str = "pdf",
                 font_base: str = "/fonts", asset_base: str = "/assets", asset_map: dict | None = None,
                 brand_logo: str | None = None):
        self.plan = plan
        self.cfg = plan.cfg
        self.brand_logo = brand_logo  # shop logo from Settings (asset name), shown on the cover
        self.size_key = size_key
        self.variant = variant
        self.digital = variant == "digital"
        self.link_mode = link_mode
        self.font_base = font_base
        self.asset_base = asset_base
        self.asset_map = asset_map or {}
        out = self.cfg["output"]
        self.ink_saving = bool(variant == "printable" and out.get("ink_saving"))
        self.theme = themes.resolve(self.cfg["theme"], ink_saving=self.ink_saving)
        self._group_themes: dict = {}
        foot = self.cfg["footer"]
        pers = self.cfg["personalization"]
        self.has_footer = bool((foot.get("enabled") and (foot.get("text") or foot.get("logo")))
                               or (pers.get("name") and pers.get("mode") == "throughout") or not self.digital)
        self.geom = geometry(size_key, variant, self.cfg, self.has_footer)
        self.index_map = plan.index_of()

    # -------------------------------------------------------------- helpers
    def L(self, key: str) -> str:
        return (self.cfg["labels"].get(key) or LABELS.get(key, key)).strip()

    def T(self, key: str) -> str:
        """Page title label, personalised ("Ayesha's Week") in 'throughout' mode."""
        lbl = self.L(key)
        p = self.cfg["personalization"]
        if p.get("name") and p.get("mode") == "throughout":
            return f"{possessive(p['name'])} {lbl}"
        return lbl

    def S(self, key: str) -> bool:
        return bool(self.cfg["sections"].get(key, True))

    def href(self, target: str | None) -> str | None:
        if not target or target not in self.index_map:
            return None
        if self.link_mode == "preview":
            return f"#{target}"
        return LINK_PREFIX + target

    def page_no(self, target: str | None) -> str:
        i = self.index_map.get(target or "")
        return "" if i is None else str(i + 1)

    def asset_url(self, name: str | None) -> str | None:
        if not name:
            return None
        if name in self.asset_map:
            return self.asset_map[name]
        return f"{self.asset_base}/{name}"

    def affirmations(self) -> list[str]:
        items = [a for a in self.cfg.get("affirmations", []) if a.strip()]
        p = self.cfg["personalization"]
        if p.get("name") and p.get("mode") == "throughout":
            n = p["name"].strip()
            items = [("I, " + n + ", am " + a[5:]) if a.startswith("I am ") else a for a in items]
        return items

    def cover_title(self) -> str:
        if self.cfg["labels"].get("cover.title"):
            return self.cfg["labels"]["cover.title"]
        return PLANNER_TYPES[self.cfg["planner_type"]]["label"].title()

    def year_label(self) -> str:
        """'2027', '2027 – 2028', or the short period ('November 2026'); empty when undated."""
        return self.plan.engine.period_label()

    def cover_logo(self) -> str | None:
        if not self.cfg["personalization"].get("cover_logo", True):
            return None
        return self.asset_url(self.brand_logo or self.cfg["footer"].get("logo"))

    def chips(self) -> list:
        if self.plan.short:  # calendar pages are reached through the side tabs
            groups = {p.id: p.group for p in self.plan.pages}
            return [(l, t) for l, t in self.plan.sections if groups.get(t) != "calendar"]
        years = {self.plan.engine.year_title(y) for y in self.plan.targets}
        return [(l, t) for l, t in self.plan.sections if l not in years]

    def start_links(self) -> list:
        """Links on a short planner's start page (the cover): one per side tab, with full names."""
        by_id = {p.id: p for p in self.plan.pages}
        names = {"month_goals": "Goals & notes", "month_habits": "Habit tracker", "namaz_month": "Prayer tracker",
                 "goal_review": "Monthly review"}
        out = []
        for label, tid, _ in self.plan.tabs:
            p = by_id.get(tid)
            if not p:
                continue
            if p.kind in ("month", "quarter"):
                name = p.title
            elif p.kind == "day" and label in WEEKDAYS_SHORT:
                name = p.data["day"].weekday_name
            elif label.startswith("W") and label[1:].isdigit():
                name = f"Week {label[1:]}"
            else:
                name = names.get(p.kind, label)
            out.append((name, tid))
        return out

    def short_tabs(self, p) -> list:
        """Side tabs for short periods: only pages that exist, current one highlighted."""
        return [(label, tid, "on" if p.id in ids else "") for label, tid, ids in self.plan.tabs
                if tid in self.index_map]

    def who(self, word: str) -> str:
        p = self.cfg["personalization"]
        if p.get("name") and p.get("mode") == "throughout":
            return f"{possessive(p['name'])} {word} · "
        return ""

    def whose(self, word: str) -> str:
        """'Ayesha's Month' in 'throughout' mode (no trailing separator), else ''."""
        return self.who(word)[:-3]

    def personal_footer(self) -> str:
        p = self.cfg["personalization"]
        if p.get("name") and p.get("mode") == "throughout":
            yl = self.year_label()
            return f"{possessive(p['name'])} Planner" + (f" · {yl}" if yl else "")
        return ""

    def month_color(self, month: int) -> str:
        return self.theme["rainbow"][(month - 1) % 12]

    # ------------------------------------------------- per page colours
    def page_theme(self, p) -> dict:
        """The theme for one page, with its page type's colour overrides (cover, month, week, day …)."""
        group = themes.GROUP_OF.get(p.kind)
        if not group or not (self.cfg["theme"].get("pages") or {}).get(group):
            return self.theme
        if group not in self._group_themes:
            self._group_themes[group] = themes.resolve(self.cfg["theme"], ink_saving=self.ink_saving, group=group)
        return self._group_themes[group]

    @staticmethod
    def css_vars(t: dict) -> str:
        return (f"--primary:{t['primary']};--accent:{t['accent']};--bg:{t['background']};--ink:{t['ink']};"
                f"--muted:{t['muted']};--fill:{t['fill']};--fill2:{t['fill_strong']};--accent-soft:{t['accent_soft']};"
                f"--line:{t['line']};--card:{t['card']};--accent-text:{t['accent_text']};--on-accent:{t['on_accent']};"
                f"--hi:{t['highlight']};--hi-soft:{t['highlight_soft']};--note-soft:{t['note_soft']};--sky:{t['sky']};"
                f"--mark:{t['mark']};")

    # ------------------------------------------------------ quotes / pictures
    def quote(self, p) -> dict | None:
        return self.plan.quote_of.get(p.id)

    def image(self, role: str) -> dict | None:
        from .catalog import image_setting
        s = image_setting(self.cfg, role)
        if s:
            s["url"] = self.asset_url(s["asset"])
        return s

    # ------------------------------------------------------------ rendering
    def context(self) -> dict:
        return dict(
            r=self, plan=self.plan, cfg=self.cfg, t=self.theme, g=self.geom, digital=self.digital,
            L=self.L, T=self.T, S=self.S, href=self.href, page_no=self.page_no, fit=fit,
            WEEKDAYS=WEEKDAYS, WEEKDAYS_SHORT=WEEKDAYS_SHORT, WEEKDAYS_LETTER=WEEKDAYS_LETTER, PRAYERS=PRAYERS,
            eng=self.plan.engine, mode=self.plan.engine.mode, lay=self.cfg["layout"],
            pers=self.cfg["personalization"], foot=self.cfg["footer"], targets=self.plan.targets,
            preview=self.link_mode == "preview", undated=self.plan.undated, short=self.plan.short,
        )

    def css(self) -> str:
        ctx = self.context()
        css = env.get_template("styles.css.j2").render(**ctx, font_faces=Markup(themes.font_faces_css(self.font_base)))
        if self.theme.get("css"):  # the template style's own small extra rules (backend/app/styles/<key>.css)
            css += "\n/* template: " + self.theme["preset"] + " */\n" + env.from_string(self.theme["css"]).render(**ctx)
        return css

    def render_pages(self, pages) -> str:
        tpl = env.get_template("page.html")
        ctx = self.context()
        parts = []
        for p in pages:
            pt = self.page_theme(p)
            parts.append(tpl.render(**{**ctx, "t": pt}, p=p, pidx=self.index_map[p.id],
                                    page_vars=self.css_vars(pt) if pt is not self.theme else ""))
        return "".join(parts)

    def document(self, pages=None) -> str:
        pages = self.plan.pages if pages is None else pages
        return env.get_template("document.html").render(
            **self.context(), css=Markup(self.css()), body=Markup(self.render_pages(pages)))


def render_preview(cfg: dict, duas: list, size_key: str, variant: str, page_index: int, quotes: list | None = None):
    from .planner import build_plan
    plan = build_plan(normalize(cfg), duas, quotes)
    page_index = max(0, min(page_index, len(plan.pages) - 1))
    r = Renderer(plan, size_key, variant, link_mode="preview")
    return r.document([plan.pages[page_index]]), plan


def escape(s: str) -> str:
    return html.escape(s or "")
