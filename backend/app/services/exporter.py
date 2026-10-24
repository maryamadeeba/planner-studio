"""Background export jobs: PDFs (all sizes / variants / splits), buyer guide, listing images, zip."""
from __future__ import annotations

import io
import json
import re
import threading
import traceback
import uuid
import zipfile
from datetime import datetime
from pathlib import Path

from markupsafe import Markup
from sqlmodel import Session

from .. import models
from . import images, mockups, pdf, themes
from .catalog import SIZES, normalize
from .mockups import inside_list
from .planner import build_plan, split_configs
from .render import Renderer, env

ETSY_LIMIT = 20 * 1024 * 1024
KB_PER_PAGE = {"digital": 20, "printable": 14}
BASE_KB = {"digital": 1600, "printable": 1100}  # embedded font subsets etc.
FONT_BASE = themes.FONT_DIR.resolve().as_uri()

JOBS: dict[str, dict] = {}
_LOCK = threading.Lock()


def slug(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", s or "planner").strip("-")
    return s[:60] or "planner"


def brand_logo() -> str | None:
    """The shop logo uploaded in Settings (asset name), if the file still exists."""
    n = (models.get_settings().get("shop_logo") or "").strip()
    return n if n and (models.ASSET_DIR / n).exists() else None


def image_roles(cfg: dict) -> dict:
    """asset name -> largest size it is shown at (see images.PDF_MAX_PX)."""
    from .catalog import image_setting
    roles: dict = {}

    def want(name, role):
        if name:
            roles[name] = max(roles.get(name, 0), images.PDF_MAX_PX[role])
    for role in ("cover", "divider"):
        s = image_setting(cfg, role)
        if s:
            want(s["asset"], f"{role}_full" if s["mode"] == "full" else role)
    s = image_setting(cfg, "month_header")
    if s:
        want(s["asset"], "month_header")
    want(cfg["footer"].get("logo"), "logo")
    want(brand_logo(), "logo")
    return roles


def asset_map(cfg: dict, workdir: Path | None = None) -> dict:
    """Map asset names to file:// URIs of PDF-sized copies (downscaled + compressed with Pillow)."""
    out = {}
    compress = cfg["output"].get("compress_images")
    for n, max_px in image_roles(cfg).items():
        src = models.ASSET_DIR / n
        if not src.exists():
            continue
        if workdir:
            try:
                dst = images.pdf_copy(src, workdir, int(max_px * (0.75 if compress else 1)), 70 if compress else 82)
                out[n] = dst.resolve().as_uri()
                continue
            except Exception:
                pass
        out[n] = src.resolve().as_uri()
    return out


def selected_duas(cfg: dict) -> list[dict]:
    from sqlmodel import select
    with Session(models.engine) as s:
        rows = s.exec(select(models.Dua).order_by(models.Dua.sort, models.Dua.id)).all()
    ids = set(cfg.get("dua_ids") or [])
    return [r.model_dump() for r in rows if not ids or r.id in ids]


def selected_quotes(cfg: dict) -> list[dict]:
    """Quote library rows for this planner (filtered by the chosen categories); empty when quotes are off."""
    from sqlmodel import select
    q = cfg.get("quotes") or {}
    if q.get("mode", "none") == "none":
        return []
    with Session(models.engine) as s:
        rows = s.exec(select(models.Quote).order_by(models.Quote.sort, models.Quote.id)).all()
    cats = set(q.get("categories") or [])
    return [r.model_dump() for r in rows if not cats or r.category in cats]


def estimate(cfg: dict) -> dict:
    cfg = normalize(cfg)
    duas = selected_duas(cfg)
    quotes = selected_quotes(cfg)
    out = cfg["output"]
    # PDF copies are at most ~PDF_MAX_PX on the long edge: estimate ~0.25 bytes per pixel after JPEG compression
    asset_bytes = sum(min((models.ASSET_DIR / n).stat().st_size, int(px * px * 0.75 * 0.25))
                      for n, px in image_roles(cfg).items() if (models.ASSET_DIR / n).exists())
    if out.get("compress_images"):
        asset_bytes //= 2
    files = []
    for tag, c in split_configs(cfg, out.get("split", "none")):
        plan = build_plan(c, duas, quotes)
        n = len(plan.pages)
        for size in out["sizes"]:
            for v in out["variants"]:
                est = (n * KB_PER_PAGE[v] + BASE_KB[v]) * 1024 + asset_bytes * 2
                files.append({"part": tag, "size": size, "variant": v, "pages": n, "bytes": est,
                              "over_limit": est > ETSY_LIMIT})
    return {"files": files, "total_bytes": sum(f["bytes"] for f in files),
            "any_over": any(f["over_limit"] for f in files), "limit": ETSY_LIMIT}


def dua_warnings(cfg: dict, duas: list) -> list[str]:
    if not cfg["modules"].get("dua_list"):
        return []
    bad = [d["title"] for d in duas if not d.get("verified")]
    if bad:
        return [f"{len(bad)} dua(s) in this planner are NOT marked verified: " + ", ".join(bad[:8]) +
                ("…" if len(bad) > 8 else "") + ". Paste verified text in the Dua Library and tick 'verified'."]
    return []


def has_arabic(plan) -> bool:
    kinds = {p.kind for p in plan.pages}
    islamic = {"dua_list", "dua_journal", "duas_answered", "ramadan_tracker", "ramadan_day", "last_ten", "eid_prep",
               "meal_planner", "juz_tracker", "surah_checklist", "khatam", "reflection", "namaz_month", "namaz_week"}
    return bool(kinds & islamic) or (plan.engine.mode == "hijri" and plan.cfg["calendar"].get("arabic_month_names"))


def arabic_check_png(b, cfg, duas, out: Path):
    from .hijri import HIJRI_MONTHS_AR
    t = themes.resolve(cfg["theme"])
    sample = next((d for d in duas if d.get("arabic") and not d["arabic"].startswith("[")), None)
    rows = ""
    if sample:
        rows += f"<div class='lbl'>Dua: {sample['title']} ({'verified' if sample.get('verified') else 'UNVERIFIED'})</div><div class='ar' dir='rtl' lang='ar'>{sample['arabic']}</div>"
    rows += "<div class='lbl'>Hijri month names (shaping + tashkeel test)</div><div class='ar' dir='rtl' lang='ar'>" + " · ".join(HIJRI_MONTHS_AR) + "</div>"
    html = f"""<!doctype html><html><head><meta charset='utf-8'><style>{themes.font_faces_css(FONT_BASE)}
    body{{margin:0;padding:40px;width:1100px;font-family:'Inter';background:#fff;color:{t['ink']}}}
    .lbl{{font-size:14px;color:#888;margin-top:18px}} .ar{{font-family:'Amiri';font-size:34px;direction:rtl;text-align:right;line-height:2}}
    h1{{font-size:20px}}</style></head><body><h1>Arabic rendering check – Amiri font, right-to-left</h1>{rows}</body></html>"""
    pdf.screenshot_html(b, html, 1180, 520, out, 1.0)


def build_guide(b, cfg, plans_info, out: Path, settings: dict, amap: dict | None = None):
    out_cfg = cfg["output"]
    t = themes.resolve(cfg["theme"])
    plan = plans_info[0]["plan"]
    logo = brand_logo()
    r = Renderer(plan, "A4", "printable", font_base=FONT_BASE, asset_map=amap, brand_logo=logo)
    gsize = "Letter" if ("Letter" in out_cfg["sizes"] and "A4" not in out_cfg["sizes"]) else "A4"
    _, w, h = SIZES[gsize]
    size_notes = {"A4": "standard paper outside the US", "Letter": "standard US paper",
                  "A5": "half of A4 – great for small binders", "HalfLetter": "half of US Letter – fits Classic-size discbound",
                  "iPadPortrait": "made for tablets – best for GoodNotes / Notability",
                  "iPadLandscape": "landscape tablet layout"}
    files = []
    for info in plans_info:
        for f in info["files"]:
            files.append({"name": f["name"], "desc": ("Digital hyperlinked PDF" if f["variant"] == "digital" else "Printable PDF")
                          + f" · {SIZES[f['size']][0].split(' (')[0]}", "pages": f["pages"]})
    eng = plan.engine
    cal_note = ""
    if plan.undated:
        cal_note = ("This planner is undated: write the month, week and dates in yourself, so you can reuse it "
                    "again and again. Weeks start on Monday.")
    elif any(p.kind in ("month", "week", "day", "year_overview") for p in plan.pages):
        cal_note = ("Calendar pages use the Hijri (Umm al-Qura) calendar"
                    + (f", adjusted {eng.offset:+d} day(s) for local moon sighting" if eng.offset else "")
                    + ". Weeks start on Monday.") if eng.mode == "hijri" else "Weeks start on Monday."
    shop = cfg["footer"].get("text") or settings.get("shop_name", "")
    html = env.get_template("guide.html").render(
        t=t, font_faces=Markup(themes.font_faces_css(FONT_BASE)), page_w=w, page_h=h,
        title=r.cover_title(), subtitle=" · ".join(x for x in (r.year_label(), settings.get("shop_name", "")) if x),
        files=files, inside=inside_list(plan), calendar_note=cal_note,
        sizes=[{"label": SIZES[s][0], "note": size_notes.get(s, "")} for s in out_cfg["sizes"]],
        has_printable="printable" in out_cfg["variants"], has_digital="digital" in out_cfg["variants"],
        has_days=plan.cfg["modules"].get("day"), has_weeks=plan.cfg["modules"].get("week"), short=plan.short,
        binder=out_cfg.get("binder_margin"), ink=out_cfg.get("ink_saving"),
        year=datetime.now().year, shop=shop, etsy=settings.get("shop_etsy", ""),
        logo=r.asset_url(logo) if logo else None, contact=settings.get("shop_contact", ""))
    pdf.render_simple_pdf(b, html, w, h, out)


# ------------------------------------------------------------------ jobs
def start_job(project_id: int) -> str:
    job_id = uuid.uuid4().hex[:12]
    JOBS[job_id] = {"id": job_id, "project_id": project_id, "status": "queued", "progress": 0.0, "stage": "Queued",
                    "message": "", "result": None, "cancel": False, "log": []}
    threading.Thread(target=_run, args=(job_id,), daemon=True).start()
    return job_id


def public(job: dict) -> dict:
    return {k: v for k, v in job.items() if k != "cancel"}


def _run(job_id: str):
    job = JOBS[job_id]
    with _LOCK:  # one export at a time keeps memory use low
        try:
            job["status"] = "running"
            _export(job)
            job["status"] = "done"
            job["progress"] = 1.0
            job["stage"] = "Finished"
        except pdf.Cancelled:
            job["status"] = "cancelled"
            job["stage"] = "Cancelled"
            job["message"] = "Export cancelled. Partial files were removed."
        except pdf.EngineError as e:
            job["status"] = "error"
            job["message"] = str(e)
        except ValueError as e:
            job["status"] = "error"
            job["message"] = str(e)
        except Exception as e:  # pragma: no cover
            traceback.print_exc()
            job["status"] = "error"
            job["message"] = f"Unexpected error: {e}"


def _export(job: dict):
    import shutil
    import tempfile
    with Session(models.engine) as s:
        proj = s.get(models.Project, job["project_id"])
        if not proj:
            raise ValueError("Project not found")
        name, cfg = proj.name, normalize(json.loads(proj.config or "{}"))
    settings = models.get_settings()
    out_cfg = cfg["output"]
    if not out_cfg["sizes"] or not out_cfg["variants"]:
        raise ValueError("Pick at least one page size and one PDF variant in step 3.")
    duas = selected_duas(cfg)
    quotes = selected_quotes(cfg)
    warnings = dua_warnings(cfg, duas)
    for c in themes.contrast_issues(cfg["theme"]):
        where = "all pages" if c["group"] == "all" else f"{c['group']} pages"
        warnings.append(f"Hard to read: {c['role']} colour {c['color']} on {c['background']} ({where}) has contrast "
                        f"{c['ratio']}:1 – at least {c['minimum']}:1 is recommended. Use Auto-fix in step 4.")
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    folder = models.export_root() / slug(name) / stamp
    folder.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="assets_"))
    cancelled = lambda: job["cancel"]
    try:
        amap = asset_map(cfg, tmp)
        logo = brand_logo()
        parts = split_configs(cfg, out_cfg.get("split", "none"))
        plans = [(tag, c, build_plan(c, duas, quotes)) for tag, c in parts]
        tasks = [(tag, plan, size, v) for tag, c, plan in plans for size in out_cfg["sizes"] for v in out_cfg["variants"]]
        weights = [len(p.pages) * (1.3 if v == "digital" else 1.0) for _, p, _, v in tasks]
        extra = (sum(weights) * 0.08 if out_cfg.get("listing_images") else 0) + (sum(weights) * 0.02 if out_cfg.get("buyer_guide") else 0)
        total_w = sum(weights) + extra or 1
        done_w = 0.0
        files = []
        plans_info = []
        job["stage"] = "Starting Chromium"
        with pdf.browser() as b:
            for (tag, plan, size, v), wgt in zip(tasks, weights):
                fname = f"{slug(name)}_{size}_{v}{('_' + tag) if tag else ''}.pdf"
                job["stage"] = f"Rendering {fname} ({len(plan.pages)} pages)"
                r = Renderer(plan, size, v, font_base=FONT_BASE, asset_map=amap, brand_logo=logo)
                base = done_w

                def prog(f, base=base, wgt=wgt):
                    job["progress"] = min(0.99, (base + f * wgt) / total_w)
                res = pdf.render_pdf(r, folder / fname, b=b, progress=prog, cancelled=cancelled)
                done_w += wgt
                size_b = pdf.file_size(folder / fname)
                info = {"name": fname, "size": size, "variant": v, "part": tag, "pages": res["pages"], "bytes": size_b,
                        "links": res.get("links", 0), "verify": res.get("verify"), "clipping": len(res.get("clipping", []))}
                if res.get("clipping"):
                    ex = res["clipping"][0]
                    warnings.append(f"{fname}: {len(res['clipping'])} piece(s) of text may be cut off "
                                    f"(first on page '{ex['page']}': “{ex['text']}”). Try shorter text or a larger size.")
                if v == "digital":
                    ver = res.get("verify") or {}
                    if res.get("broken") or ver.get("unresolved"):
                        warnings.append(f"{fname}: {res.get('broken', 0) + ver.get('unresolved', 0)} link(s) could not be resolved.")
                    if ver.get("pages") != ver.get("expected_pages"):
                        warnings.append(f"{fname}: page count mismatch ({ver.get('pages')} vs {ver.get('expected_pages')}).")
                if size_b > ETSY_LIMIT:
                    info["over_limit"] = True
                    warnings.append(f"{fname} is {size_b / 1048576:.1f} MB – over Etsy's 20 MB per-file limit. "
                                    "Re-export with 'Compress images' or split per year / half-year.")
                files.append(info)
                pi = next((x for x in plans_info if x["plan"] is plan), None)
                if not pi:
                    plans_info.append({"plan": plan, "files": [info]})
                else:
                    pi["files"].append(info)

            # Arabic check
            arabic = None
            if any(has_arabic(p) for _, _, p in plans):
                job["stage"] = "Checking Arabic rendering"
                first_pdf = folder / files[0]["name"]
                embedded = pdf.pdf_uses_font(first_pdf, "Amiri")
                png = folder / "arabic-check.png"
                arabic_check_png(b, cfg, duas, png)
                arabic = {"embedded": embedded, "image": png.name}
                if not embedded:
                    warnings.append("Arabic font (Amiri) was not found embedded in the first PDF – check arabic-check.png.")

            guide_name = None
            if out_cfg.get("buyer_guide"):
                if cancelled():
                    raise pdf.Cancelled()
                job["stage"] = "Writing buyer instructions PDF"
                guide_name = "How-to-use-your-planner.pdf"
                build_guide(b, cfg, plans_info, folder / guide_name, settings, amap)
            listing = []
            if out_cfg.get("listing_images"):
                if cancelled():
                    raise pdf.Cancelled()
                job["stage"] = "Creating Etsy listing images"
                pref = next((s for s in ("iPadPortrait", "A4", "Letter", "A5", "HalfLetter") if s in out_cfg["sizes"]),
                            out_cfg["sizes"][0])
                base = done_w

                def lprog(f):
                    job["progress"] = min(0.99, (base + f * extra) / total_w)
                imgs = mockups.generate(b, plans[0][2], cfg, pref, out_cfg["variants"], out_cfg["sizes"],
                                        folder / "listing-images", FONT_BASE, amap, progress=lprog, brand_logo=logo,
                                        quotes=quotes)
                listing = [f"listing-images/{p.name}" for p in imgs]

        job["stage"] = "Zipping bundle"
        zname = f"{slug(name)}_bundle.zip"
        with zipfile.ZipFile(folder / zname, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(folder.rglob("*")):
                if f.is_file() and f.name != zname:
                    z.write(f, f.relative_to(folder))
        cal = cfg["calendar"]
        if plans[0][2].undated:
            span = f"undated ({cal.get('period') or 'year'})"
        elif (cal.get("period") or "year") == "year":
            span = f"{cal['mode']} {cal['start_year']}-{cal['start_month']:02d} → {cal['end_year']}-{cal['end_month']:02d}"
        else:
            span = f"{cal['mode']} {plans[0][2].engine.period_label()}"
        summary = (f"{cfg['planner_type']} · {span} · {', '.join(out_cfg['sizes'])} · "
                   f"{' + '.join(out_cfg['variants'])} · template {themes.PRESETS[themes.template_key(cfg['theme']['preset'])]['label']}"
                   + (f" · split per {out_cfg['split']}" if out_cfg.get("split") not in (None, "none") else ""))
        result = {"folder": str(folder), "files": files, "guide": guide_name, "listing": listing, "zip": zname,
                  "warnings": warnings, "arabic": arabic, "summary": summary}
        with Session(models.engine) as s:
            rec = models.ExportRecord(project_id=job["project_id"], project_name=name, summary=summary,
                                      folder=str(folder), files=json.dumps(result), warnings=json.dumps(warnings))
            s.add(rec)
            s.commit()
            result["record_id"] = rec.id
        job["result"] = result
    except pdf.Cancelled:
        shutil.rmtree(folder, ignore_errors=True)
        raise
    except Exception:
        if not any(folder.iterdir()):
            shutil.rmtree(folder, ignore_errors=True)
        raise
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
