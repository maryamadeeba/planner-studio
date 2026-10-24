"""Maryam's Planner Studio – FastAPI app (API + built React frontend on one port)."""
from __future__ import annotations

import asyncio
import os
import sys
import threading
import time
import webbrowser
from contextlib import asynccontextmanager
from pathlib import Path

if sys.platform.startswith("win"):
    # Playwright needs the Proactor loop on Windows to launch Chromium subprocesses.
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import models
from .routers import library, projects
from .services.themes import FONT_DIR

FRONTEND_DIST = models.ROOT / "frontend" / "dist"
PORT = int(os.environ.get("PS_PORT", "8000"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.init_db()
    if os.environ.get("PS_OPEN_BROWSER") == "1":
        def _open():
            time.sleep(1.5)
            webbrowser.open(f"http://localhost:{PORT}")
        threading.Thread(target=_open, daemon=True).start()
    yield


app = FastAPI(title="Maryam's Planner Studio", lifespan=lifespan)


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": f"Something went wrong: {exc}"})


app.include_router(projects.router)
app.include_router(library.router)
app.mount("/fonts", StaticFiles(directory=str(FONT_DIR)), name="fonts")
app.mount("/assets", StaticFiles(directory=str(models.ASSET_DIR)), name="assets")

if (FRONTEND_DIST / "static").exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIST / "static")), name="static")


@app.get("/{full_path:path}", include_in_schema=False)
def spa(full_path: str):
    if full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"detail": "Not found"})
    f = (FRONTEND_DIST / full_path).resolve()
    if full_path and f.is_file() and FRONTEND_DIST.resolve() in f.parents:
        return FileResponse(f)
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(index, headers={"Cache-Control": "no-cache"})
    return JSONResponse(status_code=503, content={
        "detail": "The interface has not been built yet. Install Node.js (LTS) from nodejs.org and run start.bat again."})
