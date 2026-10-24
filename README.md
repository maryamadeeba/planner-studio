# Planner Studio

A local-first web app that generates print-ready and hyperlinked digital planner and calendar PDFs. I built it to produce the products for my Etsy shop, Productivity Shop by M, on a single Windows machine with no login, no cloud backend and no external services.

## What it does

- Generates calendars and planners (monthly, weekly, daily, goals, habit trackers, notes and more) as PDFs at exact page sizes
- Produces two output modes: a print version, and a digital version with internal hyperlinks (month tabs, back-to-index, day-to-week navigation) for GoodNotes, Notability and similar apps
- Supports Gregorian and Hijri calendars (Umm al-Qura, with a configurable ±2 day offset for local moon sighting)
- Supports Arabic and Latin typography with bundled open-licence fonts (Amiri, Noto Naskh Arabic, Scheherazade New, Playfair Display, Poppins and others), including RTL layout
- Customisable themes, colours, fonts and page sets per project
- Generates marketplace extras: 2000×2000 listing images, a buyer guide PDF and a bundle zip
- Warns when a file exceeds Etsy's 20 MB limit and can compress or split it by year or half-year

## Architecture

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Persistence | SQLite via SQLModel (single local file) |
| Page rendering | Jinja2 templates to HTML/CSS, then Playwright (headless Chromium) `page.pdf` |
| PDF post-processing | pypdf: merging, link rewriting and verification |
| Calendar logic | Custom Gregorian engine plus `hijridate` |
| Frontend | React, Vite, TypeScript, Tailwind CSS |
| Serving | FastAPI serves the built frontend, so the whole app runs on one port (8000) |

### Design decisions

- **HTML/CSS to PDF instead of a canvas library.** Templates are plain Jinja2 and CSS, so layout, fonts and RTL text are handled by a real browser engine, and a new page type is a template file rather than drawing code.
- **Links are wired after rendering.** Pages are rendered with placeholder URIs (`https://planner-studio.local/p/<page-id>`). After merging, pypdf rewrites each link annotation into an internal GoTo destination, then a verification pass checks that every link resolves. This avoids broken links when pages are batched or reordered.
- **Exports run as background jobs** with progress reporting and cancellation, so large planners don't block the UI.
- **Single-user, local-first.** No authentication, no network dependencies at runtime. Data lives in `data/studio.db`.

## Quality checks

- 86 automated tests (pytest) covering the calendar engine, Hijri conversion and planner generation
- Layout clipping checked across 6 page sizes and 4 themes
- End-to-end export of a 601-page digital planner completed in about 40 seconds, about 13 MB, with 18,317 of 18,317 internal links verified

## Getting started (Windows)

Requirements: Windows, Python 3.11+, and an internet connection on the first run only.

1. Extract the project (do not run it from inside the zip).
2. Double-click `start.bat`.
3. On the first run it creates a virtual environment, installs the pinned dependencies, installs Chromium for Playwright, builds the frontend, and opens http://127.0.0.1:8000.

To run the tests:

```bash
cd backend
pytest
```

## Project structure

```
backend/
  app/
    main.py            FastAPI entry point
    models.py          SQLModel tables (projects, templates, settings, exports)
    routers/           API routes
    services/          calendar, hijri, themes, planner, render, pdf, exporter
    templates/         Jinja2 page and document templates
    fonts/             bundled open-licence fonts
  tests/
frontend/
  src/                 React + TypeScript UI
start.bat              one-click launcher
```

## Notes

- Built as a real production tool for a small business, not a demo: the output has to print correctly and the links have to work.
- The placeholder duas in the library are unverified sample text and should be replaced with checked sources before any commercial use.
