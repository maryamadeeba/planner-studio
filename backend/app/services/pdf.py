"""HTML -> PDF with Playwright/Chromium, batch rendering, merging and hyperlink wiring.

How the clickable links work
----------------------------
Every internal link in the HTML is an <a href="https://planner-studio.local/p/<page-id>">.
Chromium turns each <a> into a PDF link annotation with the exact clickable
rectangle.  Pages are printed in batches (fast + cancellable); after merging,
each of those annotations is rewritten into an *internal* GoTo destination that
points at the PDF page whose id matches.  The result behaves exactly like
<a href="#page-id"> anchors (works in GoodNotes, Notability, Acrobat, Xodo…)
but also works across batches, and lets us verify that every link lands on the
correct page.
"""
from __future__ import annotations

import math
import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, NameObject, NullObject

from .render import LINK_PREFIX, Renderer

CHROMIUM_HELP = (
    "Chromium (the PDF engine) is not installed or could not start. Close the app and double-click "
    "start.bat again – it installs Chromium automatically. Or open a terminal in the planner-studio "
    "folder and run:  backend\\.venv\\Scripts\\python -m playwright install chromium"
)


class Cancelled(Exception):
    pass


class EngineError(Exception):
    pass


@contextmanager
def browser():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:  # pragma: no cover
        raise EngineError("Playwright is not installed. Run start.bat again to install requirements.") from e
    pw = sync_playwright().start()
    try:
        try:
            b = pw.chromium.launch(args=["--font-render-hinting=none"])
        except Exception as e:
            msg = str(e)
            if "Executable doesn't exist" in msg or "playwright install" in msg:
                raise EngineError(CHROMIUM_HELP) from e
            raise EngineError(f"Could not start Chromium: {msg.splitlines()[0]}") from e
        try:
            yield b
        finally:
            b.close()
    finally:
        pw.stop()


def chromium_status() -> dict:
    try:
        with browser():
            return {"ok": True, "message": "Chromium is installed and working."}
    except EngineError as e:
        return {"ok": False, "message": str(e)}
    except Exception as e:  # pragma: no cover
        return {"ok": False, "message": f"{CHROMIUM_HELP} ({e})"}


# Finds anything a buyer would see cut off: text clipped by a box (overflow: hidden) or by the page edge,
# labels shortened with an ellipsis, and boxes pushed outside the page's content area.
CLIP_JS = r"""
() => {
  const T = 1.5, out = [];
  const inside = (r, b) => r.left >= b.left - T && r.right <= b.right + T && r.top >= b.top - T && r.bottom <= b.bottom + T;
  for (const page of document.querySelectorAll('section.page')) {
    const pr = page.getBoundingClientRect();
    const report = (what, el) => out.push({page: page.id, what, text: (el.textContent || el.className || '').trim().slice(0, 50)});
    const w = document.createTreeWalker(page, NodeFilter.SHOW_TEXT);
    while (w.nextNode()) {
      const n = w.currentNode;
      if (!n.textContent.trim()) continue;
      const range = document.createRange(); range.selectNodeContents(n);
      const rects = [...range.getClientRects()].filter(r => r.width > 0.5 && r.height > 0.5);
      if (!rects.length) continue;
      let clipped = rects.some(r => !inside(r, pr));
      for (let a = n.parentElement; a && a !== page && !clipped; a = a.parentElement) {
        const cs = getComputedStyle(a);
        if (cs.textOverflow === 'ellipsis' && a.scrollWidth > a.clientWidth + 1) { report('truncated', a); clipped = null; break; }
        // cards (.box) don't clip, so text spilling out of one would overlap its neighbour – test their edges too
        if (a.classList.contains('box') || cs.overflow !== 'visible' || cs.overflowX !== 'visible' || cs.overflowY !== 'visible') {
          const ar = a.getBoundingClientRect();
          if (rects.some(r => !inside(r, ar))) clipped = true;
        }
      }
      if (clipped) report('clipped', n.parentElement);
    }
    const content = page.querySelector('.content');
    if (content) {
      const cr = content.getBoundingClientRect();
      for (const el of content.querySelectorAll('.box, .tgrid, .mgrid, .quote-card, .img-frame')) {
        const r = el.getBoundingClientRect();
        if (r.width > 0 && !inside(r, cr)) report('overflow', el);
      }
      // write-in marks and lined areas must stay inside their (non-clipping) card
      for (const box of content.querySelectorAll('.box')) {
        const br = box.getBoundingClientRect();
        for (const el of box.querySelectorAll('.cb, .circle, .num, .ls, .hours > div, .checks > div')) {
          const r = el.getBoundingClientRect();
          if (r.width > 0 && r.height > 0 && !inside(r, br)) { report('spills', el); break; }
        }
      }
    }
  }
  return out;
}
"""


def _open(b, html: str, workdir: Path, name: str):
    f = workdir / f"{name}.html"
    f.write_text(html, encoding="utf-8")
    page = b.new_page()
    page.goto(f.as_uri(), wait_until="load", timeout=180_000)
    page.evaluate("document.fonts.ready.then(() => true)")
    return page


def _print_html(b, html: str, workdir: Path, name: str, w: float, h: float, out: Path, check: bool = False):
    page = _open(b, html, workdir, name)
    try:
        issues = page.evaluate(CLIP_JS) if check else []
        page.pdf(path=str(out), width=f"{w}px", height=f"{h}px", print_background=True,
                 prefer_css_page_size=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        return issues
    finally:
        page.close()


def clipping_report(b, renderer: Renderer, pages=None) -> list[dict]:
    """Render pages in Chromium and list every clipped / truncated / overflowing element."""
    workdir = Path(tempfile.mkdtemp(prefix="clip_"))
    try:
        page = _open(b, renderer.document(pages), workdir, "clip")
        try:
            return page.evaluate(CLIP_JS)
        finally:
            page.close()
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def wire_links(writer: PdfWriter, page_ids: list[str]) -> dict:
    """Convert URI link annotations into internal page destinations, then verify them."""
    index = {pid: i for i, pid in enumerate(page_ids)}
    total = broken = 0
    for pno, page in enumerate(writer.pages):
        annots = page.get("/Annots")
        if not annots:
            continue
        for a in annots:
            ann = a.get_object()
            if ann.get("/Subtype") != "/Link":
                continue
            act = ann.get("/A")
            act = act.get_object() if act is not None else None
            uri = str(act.get("/URI", "")) if act is not None else ""
            if not uri.startswith(LINK_PREFIX):
                continue
            target = uri[len(LINK_PREFIX):]
            total += 1
            if target not in index:
                broken += 1
                continue
            dest = ArrayObject([writer.pages[index[target]].indirect_reference, NameObject("/XYZ"),
                                NullObject(), NullObject(), NullObject()])
            del ann["/A"]
            ann[NameObject("/Dest")] = dest
    return {"links": total, "broken": broken}


def verify_links(path: Path, page_ids: list[str], expected_targets: list[list[str]] | None = None) -> dict:
    """Re-open the finished PDF and check every link resolves to a valid page."""
    reader = PdfReader(str(path))
    refs = {p.indirect_reference.idnum: i for i, p in enumerate(reader.pages)}
    total = ok = 0
    leftovers = 0
    for page in reader.pages:
        for a in page.get("/Annots") or []:
            ann = a.get_object()
            if ann.get("/Subtype") != "/Link":
                continue
            if "/Dest" in ann:
                total += 1
                dest = ann["/Dest"]
                if isinstance(dest, ArrayObject) and dest and dest[0].idnum in refs:
                    ok += 1
            elif "/A" in ann and str(ann["/A"].get_object().get("/URI", "")).startswith(LINK_PREFIX):
                leftovers += 1
    return {"links": total, "resolved": ok, "unresolved": total - ok + leftovers,
            "pages": len(reader.pages), "expected_pages": len(page_ids)}


def render_pdf(renderer: Renderer, out_path: Path, *, b=None, progress=None, cancelled=None, batch_size: int = 90) -> dict:
    pages = renderer.plan.pages
    ids = [p.id for p in pages]
    g = renderer.geom
    workdir = Path(tempfile.mkdtemp(prefix="planner_"))
    parts = []
    clipping: list = []
    try:
        batches = [pages[i:i + batch_size] for i in range(0, len(pages), batch_size)]
        for bi, chunk in enumerate(batches):
            if cancelled and cancelled():
                raise Cancelled()
            html = renderer.document(chunk)
            part = workdir / f"part{bi:04d}.pdf"
            clipping += _print_html(b, html, workdir, f"part{bi:04d}", g["w"], g["h"], part, check=True)
            n = len(PdfReader(str(part)).pages)
            if n != len(chunk):
                raise EngineError(
                    f"Layout problem: batch {bi + 1} produced {n} PDF pages for {len(chunk)} planner pages "
                    "(content overflowed a page). Try a larger page size or fewer sections.")
            parts.append(part)
            if progress:
                progress((bi + 1) / len(batches))
        writer = PdfWriter()
        for part in parts:
            writer.append(str(part))
        link_stats = wire_links(writer, ids) if renderer.digital else {"links": 0, "broken": 0}
        writer.add_metadata({"/Title": renderer.cover_title(), "/Creator": "Maryam's Planner Studio",
                             "/Producer": "Maryam's Planner Studio (Chromium + pypdf)"})
        # bookmarks / outline for digital planners
        if renderer.digital:
            idx = {pid: i for i, pid in enumerate(ids)}
            for label, tid in renderer.plan.sections:
                if tid in idx:
                    writer.add_outline_item(label, idx[tid])
        try:
            writer.compress_identical_objects(remove_identicals=True, remove_orphans=True)
        except Exception:
            pass
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as fh:
            writer.write(fh)
        result = {"pages": len(pages), **link_stats, "clipping": clipping}
        if renderer.digital:
            result["verify"] = verify_links(out_path, ids)
        return result
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def render_simple_pdf(b, html: str, w: float, h: float, out_path: Path):
    workdir = Path(tempfile.mkdtemp(prefix="planner_"))
    try:
        _print_html(b, html, workdir, "doc", w, h, out_path)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def screenshot_html(b, html: str, w: float, h: float, out_path: Path, scale: float = 1.0, selector: str | None = None):
    workdir = Path(tempfile.mkdtemp(prefix="shot_"))
    try:
        f = workdir / "shot.html"
        f.write_text(html, encoding="utf-8")
        # round up: a viewport a fraction narrower than the page (793 px for A4's 793.7) shifts the page by a
        # sub-pixel and Chromium then paints element screenshots at the wrong scale
        ctx = b.new_context(viewport={"width": math.ceil(w), "height": math.ceil(h)}, device_scale_factor=scale)
        page = ctx.new_page()
        try:
            page.goto(f.as_uri(), wait_until="load", timeout=120_000)
            page.evaluate("document.fonts.ready.then(() => true)")
            if selector:
                page.locator(selector).first.screenshot(path=str(out_path))
            else:
                page.screenshot(path=str(out_path), full_page=False)
        finally:
            ctx.close()
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def pdf_uses_font(path: Path, needle: str) -> bool:
    reader = PdfReader(str(path))
    for page in reader.pages[:400]:
        res = page.get("/Resources")
        fonts = res.get_object().get("/Font") if res else None
        if not fonts:
            continue
        for f in fonts.get_object().values():
            base = str(f.get_object().get("/BaseFont", ""))
            if needle.lower() in base.lower():
                return True
    return False


def file_size(path: Path) -> int:
    return os.path.getsize(path) if path.exists() else 0
