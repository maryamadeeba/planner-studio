"""Picture uploads and PDF-ready copies (Pillow).  Keeps planners well under Etsy's 20 MB per file."""
from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageOps

UPLOAD_MAX_PX = 2400                  # longest edge kept on upload
UPLOAD_TYPES = {".png", ".jpg", ".jpeg"}
# longest edge used inside the PDF, per placement (A4 at ~200 dpi is ~1650 px tall)
PDF_MAX_PX = {"cover_full": 1800, "cover": 1300, "divider_full": 1800, "divider": 1300, "month_header": 700,
              "logo": 600, "other": 1200}


def _has_alpha(im: Image.Image) -> bool:
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        alpha = im.convert("RGBA").getchannel("A")
        return alpha.getextrema()[0] < 255
    return False


def _encode(im: Image.Image, quality: int) -> tuple[bytes, str]:
    buf = io.BytesIO()
    if _has_alpha(im):
        im.convert("RGBA").save(buf, "PNG", optimize=True)
        return buf.getvalue(), ".png"
    im.convert("RGB").save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    return buf.getvalue(), ".jpg"


def process_upload(data: bytes, filename: str) -> tuple[bytes, str, tuple[int, int]]:
    """Validate a PNG/JPG upload, fix phone rotation, downscale and compress.  Returns (bytes, ext, size)."""
    ext = Path(filename or "").suffix.lower()
    if ext not in UPLOAD_TYPES:
        raise ValueError("Please upload a PNG or JPG image.")
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
    except Exception:
        raise ValueError("That file could not be opened as an image.")
    if im.format not in ("PNG", "JPEG", "MPO"):
        raise ValueError("Please upload a PNG or JPG image.")
    im = ImageOps.exif_transpose(im)
    im.thumbnail((UPLOAD_MAX_PX, UPLOAD_MAX_PX), Image.LANCZOS)
    out, ext = _encode(im, 88)
    return out, ext, im.size


def pdf_copy(src: Path, dst_dir: Path, max_px: int, quality: int = 82) -> Path:
    """A downscaled, compressed copy of an uploaded picture for embedding in a PDF."""
    im = ImageOps.exif_transpose(Image.open(src))
    im.thumbnail((max_px, max_px), Image.LANCZOS)
    data, ext = _encode(im, quality)
    dst = dst_dir / f"{src.stem}_{max_px}{ext}"
    dst.write_bytes(data)
    # never make a file bigger than the original
    return src if dst.stat().st_size >= src.stat().st_size and max(Image.open(src).size) <= max_px else dst
