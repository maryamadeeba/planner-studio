from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from .. import models
from ..services import exporter, themes
from ..services.catalog import LABELS, PLANNER_TYPES, SIZES, catalog_payload, default_modules, normalize
from ..services.hijri import HIJRI_MAX, HIJRI_MIN, HIJRI_MONTHS_EN
from ..services.planner import build_plan
from ..services.render import Renderer

router = APIRouter(prefix="/api")

LABEL_PREFIX = {
    "cover": ["cover."], "index": ["index."], "year_overview": ["year."], "quarter": ["quarter."],
    "quarter_review": ["quarter_review."], "month": ["month."], "month_habits": ["habits."], "week": ["week."],
    "day": ["day."], "notes": ["notes."], "month_goals": ["month_goals."], "goal_vision": ["goal_vision."], "goal_smart": ["goal_smart."],
    "goal_milestones": ["goal_milestones."], "goal_actions": ["goal_actions."], "goal_progress": ["goal_progress."],
    "goal_review": ["goal_review."], "affirmations": ["affirmations."], "vision_board": ["vision_board."],
    "gratitude": ["gratitude."], "scripting": ["scripting."], "method369": ["method369."], "namaz_month": ["namaz.", "ar.namaz"],
    "namaz_week": ["namaz_week."], "dua_list": ["dua_list.", "ar.dua"], "dua_journal": ["dua_journal."],
    "duas_answered": ["duas_answered."], "ramadan_tracker": ["ramadan_tracker.", "ar.ramadan"], "ramadan_day": ["ramadan_day."],
    "last_ten": ["last_ten."], "eid_prep": ["eid_prep."], "meal_planner": ["meal_planner."], "juz_tracker": ["juz_tracker.", "ar.quran"],
    "surah_checklist": ["surah_checklist."], "khatam": ["khatam."], "reflection": ["reflection."],
}


@router.get("/meta")
def meta():
    p = catalog_payload()
    p["themes"] = {k: {kk: vv for kk, vv in v.items() if kk != "css"} for k, v in themes.PRESETS.items()}
    p["featured_templates"] = themes.featured_templates()
    p["fonts"] = {"english": themes.ENGLISH_FONTS + [f for f in themes.extra_fonts() if f not in themes.FONTS],
                  "arabic": themes.ARABIC_FONTS}
    p["label_prefix"] = LABEL_PREFIX
    p["brand"] = themes.BRAND
    p["page_groups"] = list(themes.PAGE_GROUPS)
    p["contrast"] = {"text": themes.TEXT_MIN, "accent": themes.ACCENT_MIN}
    p["quote_categories"] = models.QUOTE_CATEGORIES
    p["hijri"] = {"min": HIJRI_MIN, "max": HIJRI_MAX, "months": HIJRI_MONTHS_EN}
    p["etsy_limit"] = exporter.ETSY_LIMIT
    return p


class ProjectIn(BaseModel):
    name: str | None = None
    config: dict | None = None
    template_id: int | None = None
    planner_type: str | None = None
    style: str | None = None  # template style key, e.g. "blush_bloom"


def _out(p: models.Project) -> dict:
    return {"id": p.id, "name": p.name, "config": normalize(json.loads(p.config or "{}")),
            "created": p.created.isoformat(), "updated": p.updated.isoformat()}


def new_config(planner_type: str | None = None, style: str | None = None) -> dict:
    s = models.get_settings()
    cfg = normalize({})
    if planner_type in PLANNER_TYPES:
        cfg["planner_type"] = planner_type
        cfg["modules"] = default_modules(planner_type)
        cfg["calendar"]["period"] = PLANNER_TYPES[planner_type].get("period", "year")
    cfg["calendar"]["hijri_offset"] = int(s.get("default_hijri_offset") or 0)
    cfg["theme"]["preset"] = themes.template_key(style if style in themes.PRESETS else s.get("default_theme"))
    cfg["footer"]["text"] = s.get("shop_name") or cfg["footer"]["text"]
    cfg["footer"]["logo"] = s.get("shop_logo") or None
    cfg["listing"]["shop_line"] = s.get("shop_name") or cfg["listing"]["shop_line"]
    return cfg


@router.get("/projects")
def list_projects():
    with Session(models.engine) as s:
        rows = s.exec(select(models.Project).order_by(models.Project.updated.desc())).all()
        return [{"id": p.id, "name": p.name, "updated": p.updated.isoformat(),
                 "planner_type": (models.loads(p.config, {}) or {}).get("planner_type", "")} for p in rows]


@router.post("/projects")
def create_project(body: ProjectIn):
    with Session(models.engine) as s:
        cfg = new_config(body.planner_type, body.style)
        name = body.name or "Untitled planner"
        if body.template_id:
            t = s.get(models.Template, body.template_id)
            if not t:
                raise HTTPException(404, "Template not found")
            cfg = normalize(json.loads(t.config))
            name = body.name or f"{t.name} (copy)"
        if body.config:
            cfg = normalize(body.config)
        p = models.Project(name=name, config=json.dumps(cfg))
        s.add(p)
        s.commit()
        s.refresh(p)
        return _out(p)


@router.get("/projects/{pid}")
def get_project(pid: int):
    with Session(models.engine) as s:
        p = s.get(models.Project, pid)
        if not p:
            raise HTTPException(404, "Project not found")
        return _out(p)


@router.put("/projects/{pid}")
def update_project(pid: int, body: ProjectIn):
    with Session(models.engine) as s:
        p = s.get(models.Project, pid)
        if not p:
            raise HTTPException(404, "Project not found")
        if body.name is not None:
            p.name = body.name.strip() or p.name
        if body.config is not None:
            p.config = json.dumps(normalize(body.config))
        p.updated = models.now()
        s.add(p)
        s.commit()
        s.refresh(p)
        return _out(p)


@router.delete("/projects/{pid}")
def delete_project(pid: int):
    with Session(models.engine) as s:
        p = s.get(models.Project, pid)
        if p:
            s.delete(p)
            s.commit()
    return {"ok": True}


@router.post("/projects/{pid}/duplicate")
def duplicate_project(pid: int):
    with Session(models.engine) as s:
        p = s.get(models.Project, pid)
        if not p:
            raise HTTPException(404, "Project not found")
        q = models.Project(name=f"{p.name} (copy)", config=p.config)
        s.add(q)
        s.commit()
        s.refresh(q)
        return _out(q)


# ------------------------------------------------------------------ preview
class PreviewIn(BaseModel):
    config: dict
    size: str = "A4"
    variant: str = "digital"
    index: int = 0


def _plan(cfg: dict):
    try:
        cfg = normalize(cfg)
        return build_plan(cfg, exporter.selected_duas(cfg), exporter.selected_quotes(cfg))
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/preview/pages")
def preview_pages(body: PreviewIn):
    plan = _plan(body.config)
    return {"count": len(plan.pages),
            "pages": [{"i": i, "id": p.id, "kind": p.kind, "title": p.title} for i, p in enumerate(plan.pages)]}


@router.post("/preview/html", response_class=HTMLResponse)
def preview_html(body: PreviewIn, request: Request):
    plan = _plan(body.config)
    size = body.size if body.size in SIZES else "A4"
    variant = body.variant if body.variant in ("digital", "printable") else "digital"
    i = max(0, min(body.index, len(plan.pages) - 1))
    base = str(request.base_url).rstrip("/")
    r = Renderer(plan, size, variant, link_mode="preview", font_base=f"{base}/fonts", asset_base=f"{base}/assets",
                 brand_logo=exporter.brand_logo())
    return HTMLResponse(r.document([plan.pages[i]]))


@router.post("/estimate")
def estimate(body: PreviewIn):
    try:
        return exporter.estimate(body.config)
    except ValueError as e:
        raise HTTPException(400, str(e))


# ------------------------------------------------------------------- export
@router.post("/projects/{pid}/export")
def export(pid: int):
    with Session(models.engine) as s:
        if not s.get(models.Project, pid):
            raise HTTPException(404, "Project not found")
    running = [j for j in exporter.JOBS.values() if j["status"] in ("queued", "running")]
    if running:
        raise HTTPException(409, "Another export is still running – wait for it to finish or cancel it.")
    return {"job_id": exporter.start_job(pid)}


@router.get("/jobs/{jid}")
def job(jid: str):
    j = exporter.JOBS.get(jid)
    if not j:
        raise HTTPException(404, "Job not found")
    return exporter.public(j)


@router.post("/jobs/{jid}/cancel")
def cancel(jid: str):
    j = exporter.JOBS.get(jid)
    if j:
        j["cancel"] = True
        j["stage"] = "Cancelling…"
    return {"ok": True}


@router.get("/labels")
def labels():
    return LABELS
