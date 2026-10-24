from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import threading
import uuid
import zipfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from sqlmodel import Session, select

from .. import models
from ..services import exporter, images, mockups, pdf
from ..services.catalog import normalize
from ..services.planner import build_plan

router = APIRouter(prefix="/api")


# ---------------------------------------------------------------- templates
class TemplateIn(BaseModel):
    project_id: int | None = None
    name: str | None = None
    tags: str | None = None


def _tpl_out(t: models.Template) -> dict:
    return {"id": t.id, "name": t.name, "tags": [x.strip() for x in (t.tags or "").split(",") if x.strip()],
            "planner_type": t.planner_type, "theme": t.theme, "calendar_mode": t.calendar_mode,
            "thumbnail": f"/api/templates/{t.id}/thumb" if t.thumbnail else None,
            "created": t.created.isoformat(), "updated": t.updated.isoformat()}


def _make_thumb(tid: int, cfg: dict):
    try:
        plan = build_plan(cfg, exporter.selected_duas(cfg), exporter.selected_quotes(cfg))
        out = models.THUMB_DIR / f"template_{tid}.png"
        with pdf.browser() as b:
            mockups.thumbnail(b, plan, exporter.FONT_BASE, exporter.asset_map(cfg), out)
        with Session(models.engine) as s:
            t = s.get(models.Template, tid)
            if t:
                t.thumbnail = out.name
                s.add(t)
                s.commit()
    except Exception as e:  # thumbnails are optional
        print("Thumbnail failed:", e)


@router.get("/templates")
def list_templates(q: str = "", planner_type: str = "", theme: str = "", mode: str = ""):
    with Session(models.engine) as s:
        rows = s.exec(select(models.Template).order_by(models.Template.updated.desc())).all()
    out = []
    for t in rows:
        if q and q.lower() not in (t.name + " " + t.tags).lower():
            continue
        if planner_type and t.planner_type != planner_type:
            continue
        if theme and t.theme != theme:
            continue
        if mode and t.calendar_mode != mode:
            continue
        out.append(_tpl_out(t))
    return out


@router.post("/templates")
def save_template(body: TemplateIn):
    with Session(models.engine) as s:
        p = s.get(models.Project, body.project_id or 0)
        if not p:
            raise HTTPException(404, "Project not found – save the project first")
        cfg = normalize(json.loads(p.config))
        t = models.Template(name=(body.name or p.name).strip(), tags=body.tags or "", config=json.dumps(cfg),
                            planner_type=cfg["planner_type"], theme=cfg["theme"]["preset"],
                            calendar_mode=cfg["calendar"]["mode"])
        s.add(t)
        s.commit()
        s.refresh(t)
        threading.Thread(target=_make_thumb, args=(t.id, cfg), daemon=True).start()
        return _tpl_out(t)


@router.put("/templates/{tid}")
def update_template(tid: int, body: TemplateIn):
    with Session(models.engine) as s:
        t = s.get(models.Template, tid)
        if not t:
            raise HTTPException(404, "Template not found")
        if body.name:
            t.name = body.name.strip()
        if body.tags is not None:
            t.tags = body.tags
        t.updated = models.now()
        s.add(t)
        s.commit()
        s.refresh(t)
        return _tpl_out(t)


@router.post("/templates/{tid}/duplicate")
def duplicate_template(tid: int):
    with Session(models.engine) as s:
        t = s.get(models.Template, tid)
        if not t:
            raise HTTPException(404, "Template not found")
        n = models.Template(name=f"{t.name} (copy)", tags=t.tags, planner_type=t.planner_type, theme=t.theme,
                            calendar_mode=t.calendar_mode, config=t.config)
        s.add(n)
        s.commit()
        s.refresh(n)
        if t.thumbnail and (models.THUMB_DIR / t.thumbnail).exists():
            dst = models.THUMB_DIR / f"template_{n.id}.png"
            shutil.copy(models.THUMB_DIR / t.thumbnail, dst)
            n.thumbnail = dst.name
            s.add(n)
            s.commit()
            s.refresh(n)
        return _tpl_out(n)


@router.delete("/templates/{tid}")
def delete_template(tid: int):
    with Session(models.engine) as s:
        t = s.get(models.Template, tid)
        if t:
            if t.thumbnail:
                (models.THUMB_DIR / t.thumbnail).unlink(missing_ok=True)
            s.delete(t)
            s.commit()
    return {"ok": True}


@router.get("/templates/{tid}/thumb")
def template_thumb(tid: int):
    with Session(models.engine) as s:
        t = s.get(models.Template, tid)
        if not t or not t.thumbnail or not (models.THUMB_DIR / t.thumbnail).exists():
            raise HTTPException(404, "No thumbnail")
        return FileResponse(models.THUMB_DIR / t.thumbnail, headers={"Cache-Control": "no-cache"})


# --------------------------------------------------------------------- duas
class DuaIn(BaseModel):
    title: str = ""
    arabic: str = ""
    english: str = ""
    reference: str = ""
    category: str = ""
    verified: bool = False
    sort: int = 0


@router.get("/duas")
def list_duas():
    with Session(models.engine) as s:
        return [d.model_dump() for d in s.exec(select(models.Dua).order_by(models.Dua.sort, models.Dua.id)).all()]


@router.post("/duas")
def add_dua(body: DuaIn):
    with Session(models.engine) as s:
        d = models.Dua(**body.model_dump())
        if not d.title.strip():
            d.title = "New dua"
        s.add(d)
        s.commit()
        s.refresh(d)
        return d.model_dump()


@router.put("/duas/{did}")
def update_dua(did: int, body: DuaIn):
    with Session(models.engine) as s:
        d = s.get(models.Dua, did)
        if not d:
            raise HTTPException(404, "Dua not found")
        for k, v in body.model_dump().items():
            setattr(d, k, v)
        s.add(d)
        s.commit()
        s.refresh(d)
        return d.model_dump()


@router.delete("/duas/{did}")
def delete_dua(did: int):
    with Session(models.engine) as s:
        d = s.get(models.Dua, did)
        if d:
            s.delete(d)
            s.commit()
    return {"ok": True}


# ------------------------------------------------------------------- quotes
class QuoteIn(BaseModel):
    text: str = ""
    author: str = ""
    category: str = ""
    kind: str = "affirmation"
    sort: int = 0


def _clean_quote(body: QuoteIn) -> dict:
    d = body.model_dump()
    d["text"] = d["text"].strip()
    if not d["text"]:
        raise HTTPException(400, "A quote needs some text.")
    if len(d["text"]) > 240:
        raise HTTPException(400, "Keep quotes under 240 characters so they fit on the page.")
    d["kind"] = "quote" if d["kind"] == "quote" else "affirmation"
    return d


@router.get("/quotes")
def list_quotes():
    with Session(models.engine) as s:
        return [q.model_dump() for q in s.exec(select(models.Quote).order_by(models.Quote.sort, models.Quote.id)).all()]


@router.post("/quotes")
def add_quote(body: QuoteIn):
    with Session(models.engine) as s:
        q = models.Quote(**_clean_quote(body))
        s.add(q)
        s.commit()
        s.refresh(q)
        return q.model_dump()


@router.put("/quotes/{qid}")
def update_quote(qid: int, body: QuoteIn):
    with Session(models.engine) as s:
        q = s.get(models.Quote, qid)
        if not q:
            raise HTTPException(404, "Quote not found")
        for k, v in _clean_quote(body).items():
            setattr(q, k, v)
        s.add(q)
        s.commit()
        s.refresh(q)
        return q.model_dump()


@router.delete("/quotes/{qid}")
def delete_quote(qid: int):
    with Session(models.engine) as s:
        q = s.get(models.Quote, qid)
        if q:
            s.delete(q)
            s.commit()
    return {"ok": True}


# ----------------------------------------------------------------- settings
@router.get("/settings")
def get_settings():
    s = models.get_settings()
    s["effective_export_dir"] = str(models.export_root())
    return s


@router.get("/settings/logo")
def shop_logo():
    """The shop logo uploaded in Settings (used by the app header)."""
    name = exporter.brand_logo()
    if not name:
        raise HTTPException(404, "No logo uploaded")
    return FileResponse(models.ASSET_DIR / name, headers={"Cache-Control": "no-cache"})


@router.put("/settings")
def put_settings(body: dict):
    with Session(models.engine) as s:
        for k, v in body.items():
            if k not in models.DEFAULT_SETTINGS:
                continue
            if k == "export_dir" and str(v).strip():
                try:
                    Path(str(v)).mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    raise HTTPException(400, f"Cannot use that export folder: {e}")
            if k == "default_hijri_offset" and str(v) not in ("-2", "-1", "0", "1", "2"):
                raise HTTPException(400, "Hijri offset must be between -2 and +2")
            if k == "shop_logo" and v and (Path(str(v)).suffix.lower() not in (".png", ".jpg") or not (models.ASSET_DIR / str(v)).exists()):
                raise HTTPException(400, "The shop logo must be an uploaded PNG image.")
            row = s.get(models.Setting, k) or models.Setting(key=k)
            row.value = str(v if v is not None else "")
            s.add(row)
        s.commit()
    return get_settings()


# ------------------------------------------------------------------- assets
@router.post("/assets")
async def upload_asset(file: UploadFile = File(...)):
    """PNG / JPG upload: rotated upright, downscaled to 2400 px and compressed with Pillow before saving."""
    data = await file.read()
    if len(data) > 25 * 1024 * 1024:
        raise HTTPException(400, "Image is larger than 25 MB – please resize it first.")
    try:
        out, ext, size = images.process_upload(data, file.filename or "")
    except ValueError as e:
        raise HTTPException(400, str(e))
    name = f"{uuid.uuid4().hex[:12]}{ext}"
    (models.ASSET_DIR / name).write_bytes(out)
    return {"name": name, "url": f"/assets/{name}", "bytes": len(out), "original_bytes": len(data),
            "width": size[0], "height": size[1]}


# ------------------------------------------------------------------ exports
def _rec_out(r: models.ExportRecord) -> dict:
    data = models.loads(r.files, {}) or {}
    return {"id": r.id, "project_id": r.project_id, "project_name": r.project_name, "created": r.created.isoformat(),
            "summary": r.summary, "folder": r.folder, "exists": Path(r.folder).exists(),
            "warnings": models.loads(r.warnings, []), "result": data}


@router.get("/exports")
def list_exports():
    with Session(models.engine) as s:
        return [_rec_out(r) for r in s.exec(select(models.ExportRecord).order_by(models.ExportRecord.created.desc())).all()]


@router.delete("/exports/{eid}")
def delete_export(eid: int, delete_files: bool = False):
    with Session(models.engine) as s:
        r = s.get(models.ExportRecord, eid)
        if r:
            if delete_files and r.folder and Path(r.folder).exists():
                shutil.rmtree(r.folder, ignore_errors=True)
            s.delete(r)
            s.commit()
    return {"ok": True}


def open_folder(path: str):
    if not Path(path).exists():
        raise HTTPException(404, "That export folder no longer exists.")
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as e:
        raise HTTPException(500, f"Could not open the folder: {e}. It is here: {path}")


@router.post("/exports/{eid}/open")
def open_export(eid: int):
    with Session(models.engine) as s:
        r = s.get(models.ExportRecord, eid)
        if not r:
            raise HTTPException(404, "Export not found")
        open_folder(r.folder)
    return {"ok": True}


@router.post("/open-folder")
def open_any(body: dict):
    open_folder(body.get("path", ""))
    return {"ok": True}


@router.get("/exports/{eid}/file")
def export_file(eid: int, path: str):
    with Session(models.engine) as s:
        r = s.get(models.ExportRecord, eid)
        if not r:
            raise HTTPException(404, "Export not found")
        base = Path(r.folder).resolve()
        f = (base / path).resolve()
        if base not in f.parents or not f.is_file():
            raise HTTPException(404, "File not found")
        return FileResponse(f, filename=f.name)


# ------------------------------------------------------------------- backup
@router.get("/backup")
def backup():
    buf = io.BytesIO()
    models.engine.dispose()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        if models.DB_PATH.exists():
            z.write(models.DB_PATH, "studio.db")
        for folder, arc in ((models.ASSET_DIR, "assets"), (models.THUMB_DIR, "thumbs")):
            for f in folder.glob("*"):
                if f.is_file():
                    z.write(f, f"{arc}/{f.name}")
    from datetime import datetime
    name = f"planner-studio-backup_{datetime.now():%Y-%m-%d_%H%M}.zip"
    return Response(buf.getvalue(), media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="{name}"'})


@router.post("/backup/import")
async def import_backup(file: UploadFile = File(...)):
    data = await file.read()
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise HTTPException(400, "That file is not a valid backup zip.")
    if "studio.db" not in z.namelist():
        raise HTTPException(400, "Backup zip does not contain studio.db")
    models.engine.dispose()
    safety = models.DATA_DIR / "studio.before-import.db"
    if models.DB_PATH.exists():
        shutil.copy(models.DB_PATH, safety)
    for n in z.namelist():
        if n.endswith("/") or ".." in n:
            continue
        if n == "studio.db":
            models.DB_PATH.write_bytes(z.read(n))
        elif n.startswith("assets/"):
            (models.ASSET_DIR / Path(n).name).write_bytes(z.read(n))
        elif n.startswith("thumbs/"):
            (models.THUMB_DIR / Path(n).name).write_bytes(z.read(n))
    models.init_db()
    return {"ok": True, "message": "Backup restored. Your previous database was saved as data/studio.before-import.db"}


@router.get("/health")
def health(check_chromium: bool = False):
    out = {"ok": True, "root": str(models.ROOT)}
    if check_chromium:
        out["chromium"] = pdf.chromium_status()
    return out
