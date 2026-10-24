# Maryam's Planner Studio

A local desktop web app for creating printable and digital (hyperlinked) planner PDFs for the Etsy shop **Productivity Shop by M** (etsy.com/shop/productivityshopbym). It runs only on your own Windows PC. There is no login and nothing is uploaded anywhere.

---

## 1. What you need

| | |
|---|---|
| **Windows 10 or 11** | |
| **Python 3.11, 3.12 or 3.13** | Download from <https://www.python.org/downloads/>. During installation, tick **"Add python.exe to PATH"**. |
| **Internet** | Needed on the **first run only**, to download the Python packages and the Chromium PDF engine (about 200 MB in total). |
| Node.js | *Not needed.* The interface is already built and included in `frontend/dist`. You only need Node.js (LTS, <https://nodejs.org>) if you change the interface code. |

## 2. First run

1. Unzip `planner-studio.zip` somewhere permanent, for example `Documents\planner-studio`. Don't run it from inside the zip.
2. Double-click **`start.bat`**.
3. The first run takes 3–6 minutes. It:
   - creates a private Python environment in `backend\.venv`
   - installs the packages
   - downloads Chromium, the engine that makes the PDFs
4. Your browser opens at **http://localhost:8000**.
5. **Keep the black window open** while you work. Close it to stop the studio.

Later runs start in a few seconds. To make a desktop shortcut, right-click `start.bat` and choose **Send to → Desktop (create shortcut)**.

## 3. Using the studio

The sidebar has: **Dashboard · New Planner · Template Library · Dua Library · Quotes Library · Settings · Export History · Help**. The **Help** page explains each feature below in short.

Making a planner takes eight steps:

1. **Template & type**
   - **Template style** (with live thumbnails): sets the colours, fonts, card style, cover layout and decorations for every page.
     - **Sky Classic** – sky blue and cream, Playfair headings, rounded soft cards and a bow. Calm and professional.
     - **Blush Bloom** – blush pink and butter yellow on white, Caveat handwritten headings, bubbly shapes, flowers and dots. Cute and feminine.
     - **Ink & Gold Minimal** – deep ink #1D4E5F text, gold #C9A24B accent, thin lines instead of cards, Poppins only, lots of white space. Premium and minimalist.
     - "Show more colour styles" lists the older presets (Minimal, Soft pastel, Islamic geometric, Colourful).
     Custom colours, pictures and quotes always apply on top of the template. Islamic pages, Arabic (right-to-left, Amiri font) and the Hijri calendar work in every template.
   - **Planner type**: Yearly, Quarterly, Monthly, Weekly, Daily, Compact monthly set (3 pages), Goal, Manifestation, Namaz, Dua, Ramadan or Quran.
2. **Calendar & dates**
   - **Period**: Full year, Single month, Quarter, Single week or Custom date range (up to one year).
     Short periods never contain year-level pages (no year overview, index or 12 month tabs). The cover becomes a
     start page that links to every section, and the side tabs only show pages that exist.
     - Single month: start page, month calendar, goals & notes page, plus whatever you tick in step 5 (weekly pages, daily pages, habit tracker, monthly review, notes…).
     - Quarter: a quarter overview page plus its three months.
     - Single week: only that Monday–Sunday week (plus its daily pages if ticked).
   - **Dated / Undated**: undated pages have blank "Month: ____", "Week of: ____" and "Date: ____" fields and weekday headings only, so one file can be reused. Each undated month has 5 "Week of" spreads with 7 daily pages each. The toggle is hidden for planner types without dates (Manifestation, Dua, Quran).
   - Choose **Gregorian** or **Hijri**. The two are never mixed on one page.
   - Set any range from Jan 2026 to Dec 2040. In Hijri mode the range is Rajab 1447 to Dhul Hijjah 1462.
   - Weeks always start on Monday. ISO week numbers are optional.
   - Hijri mode also has the Hijri offset, the Islamic event toggles and your own custom events.
   - Gregorian mode has a holiday list that you fill in yourself.
3. **Sizes & PDF**
   - Sizes: A4, US Letter, A5, Half Letter, iPad portrait and iPad landscape. You can pick several.
   - Variants: **Digital** (hyperlinked) and/or **Printable**.
   - Printable options: binder margin and ink-saving.
   - Extras: Etsy listing images and the buyer guide.
   - File-size options: compress images, or split the PDF per year / half-year.
4. **Theme & colours**: the template style again, plus colours for all pages and per page type, a readability check with Auto-fix, the bow/flower motif on or off, fonts, corners and the style of the notes lines. The brand palette: sky #93E2F0, deep sky #2A93B3, ink #1D4E5F, text #35535E, cream #FFFCF8, blush #F7C6D2, butter #FFE59A.
5. **Sections & text**: switch each page type on or off. Click **"Sections & text"** to:
   - hide sections on that page
   - rename any title or label (e.g. "To Do" → "Tasks")
   - set options such as weekly layout, schedule hours, habits, affirmations, number of pages and which duas to include
6. **Personalisation**
   - Name, shown on the cover only or on the cover and throughout ("Ayesha's Week").
   - Subtitle, monogram and the shop logo on the cover.
   - **Pictures** for the cover, section dividers and monthly page headers (see below).
   - **Quotes & affirmations**: none, one per page type, or a different one on every page.
   - Shop footer: text, logo, position and opacity.
7. **Preview**: a live preview of every page, with page navigation, zoom and thumbnails. Links work in the preview: click a tab or a date to jump.
8. **Export**: estimated file sizes, the 20 MB warning with one-click fixes, listing-image text, a progress bar with a **Cancel** button, and the results.

Each export creates a folder containing:

- `<name>_<size>_<digital|printable>.pdf` for every size and variant you chose
- `How-to-use-your-planner.pdf`, the buyer instructions in your theme
- `listing-images/`: 7–8 PNGs at 2000 × 2000 in your template style, including a **"compare all templates"** image that shows the same planner in each featured template side by side, plus optional 2700 × 2025 versions
- `arabic-check.png`, a picture of the Arabic rendering test (only when Arabic is used)
- `<name>_bundle.zip`, everything above in one zip

**Hyperlinks.** Every digital PDF is checked automatically after export. The result screen shows something like "3863/3863 links ✓", which means every link was confirmed to land on its correct page. Links work in GoodNotes, Notability, Noteshelf, Xodo and Acrobat. PDF bookmarks are added too.

**Colours (step 4).** Pick a background, heading, body-text and accent colour for all pages, then optionally override them per page type (cover & dividers, monthly, weekly, daily, habit tracker, notes). The palette swatches are the brand colours. A readability check warns when text is hard to read (WCAG contrast below 4.5:1 for text, 3:1 for the accent used on bands and icons) and offers **Auto-fix**, which darkens or lightens the colour just enough.

**Pictures (step 6).** Upload PNG or JPG pictures for the cover (framed or full-bleed), section divider pages and a small header picture on monthly pages. Each has placement, fit (fill or whole picture), opacity and shape (rounded, circle or square). Pictures are rotated upright, resized and compressed with Pillow on upload, and again at the right size for each placement on export, so PDFs stay well under 20 MB.

**Quotes Library.** 70+ starter quotes and affirmations (goals, focus, habits, hope and faith-friendly) – original wording or public-domain lines. Add, edit or delete them in the sidebar's **Quotes Library**. In step 6 choose no quotes, one per page type, or a different quote on every page, and where they appear (cover, monthly, weekly, daily footer, dividers).

**Clipping check.** Every export checks every page in Chromium for text that is cut off or pushed off the page, and lists any problem in the export warnings.

**Shop logo.** Upload your logo (PNG) in **Settings → Shop logo** and press **Save settings**. It is used on planner covers (switch it off per project in step 6), the buyer guide, the Etsy listing images and the app sidebar. Without a logo, the sidebar shows the sky-blue bow.

**Adding a template style.** Templates are data, not page copies. To add one:

1. Copy `backend\app\styles\sky_classic.json` to a new name, e.g. `sage_garden.json` (the file name is the template's key).
2. Change `label`, `description`, `order`, the `colors` and `fonts`, and pick the building blocks:
   - `cards`: `soft` (rounded cards) or `lines` (thin rules, no card backgrounds)
   - `cover`: `panel`, `bloom` or `editorial`
   - `decoration`: `bow`, `bloom`, `minimal` (or the older `lines`, `dots`, `geometric`, `bands`)
   - `motif`: `bow`, `flower` or `none`; `corner`: `square`, `soft`, `rounded` or `bubbly`; `title_scale` to size titles
   - `accent_role`: `decorative` if the accent is only for thin lines (it is then skipped by the readability check and checkboxes use the text colour)
   - `featured: true` shows it in the step 1 picker and the "compare" listing image.
3. Optional: add `sage_garden.css` next to it for small extra CSS rules (it can use `{{ t.accent }}` etc.).
4. Restart `start.bat`. Every page type, size, picture, quote and colour override works with the new template automatically; run the tests to check for clipping.

## 4. Where your files are saved

| What | Where |
|---|---|
| Projects, templates, duas, settings | `planner-studio\data\studio.db` |
| Uploaded logos / cover images | `planner-studio\data\assets\` |
| Exports | `planner-studio\exports\<project-name>\<date_time>\` (you can change the folder in **Settings → Export folder**) |

**Export History** lists every past export. Use **Open folder** to jump to one.

## 5. Backing up

Go to **Settings → Backup → Download backup**. This saves one zip with the database, logos, images and template thumbnails. Keep it somewhere safe, such as Google Drive or a USB stick.

To restore, use **Settings → Restore from backup…**. Your current database is kept as `data\studio.before-import.db` in case you need it.

Exported PDFs are **not** inside the backup. Back up the `exports` folder separately.

## 6. Hijri dates and the offset

- The Hijri calendar uses the **Umm al-Qura** calculation (package `hijridate`).
- Local moon sighting often differs by a day. Pakistan, for example, is often **one day behind** Saudi Arabia.
- Set the offset in **step 2** for one planner, or set a default in **Settings → Default Hijri offset** for every new planner.
- `-1` means every Hijri date, and every Islamic event, moves **one day later** on the calendar. `+1` moves them one day earlier. The range is −2 to +2.
- After an official moon-sighting announcement, open the project, change the offset and export again.

## 7. Duas and Arabic text

- The **Dua Library** starts with clearly marked **placeholder** entries. The app never writes Quranic or dua Arabic text itself.
- Paste verified Arabic, the English meaning and the reference, then tick **Verified**.
- Any unverified dua included in a planner shows a warning in step 8 and in the export results.
- Arabic is shaped and connected by Chromium, displayed right-to-left, keeps its tashkeel, and uses the embedded **Amiri** font.
- Every export that contains Arabic checks that the font is embedded. It also saves `arabic-check.png` so you can look at the result.

## 8. Fonts and licences

All bundled fonts are from Google Fonts under the **SIL Open Font License** and may be used in products you sell:

- **English:** Inter, Poppins, Playfair Display, Lora, Dancing Script, Great Vibes, Caveat
- **Arabic:** Amiri, Noto Naskh Arabic, Scheherazade New

The licence files are in `backend\app\fonts\licenses\`.

**Adding fonts:**

1. Copy `.ttf` or `.otf` files into `backend\app\fonts\extra\`. Use only fonts licensed for commercial use.
2. Name the files `Family-Style.ttf`, with underscores for spaces. For example, `Open_Sans-Regular.ttf` shows up as "Open Sans".
3. Close and re-open `start.bat`. The font appears in **step 4 → Heading/Body font**.
4. Keep the font's licence file next to it.

## 9. Etsy file-size limit

Etsy allows **20 MB per file**. As a rough guide, a 1-year hyperlinked daily planner with all sections is about 600 pages and about 13 MB.

Step 8 estimates each file's size before you export. Any file over 20 MB is flagged, both in the estimate and after export, with these fixes:

- **Compress images**: shrinks your cover image and logo.
- **Split per year / per half-year**: makes one PDF per period. Each part is a complete planner with its own working links.

## 10. Troubleshooting

| Problem | Fix |
|---|---|
| "Python 3.11 or newer was not found" | Install Python from python.org and tick **Add python.exe to PATH**. If you have several versions, the `py` launcher picks the newest. |
| "Chromium is not installed" / PDF engine problem on the Dashboard | Close the window and run `start.bat` again while online. Or open a terminal in the planner-studio folder and run `backend\.venv\Scripts\python -m playwright install chromium`. |
| "Address already in use" / port 8000 | The studio is already running in another window. Just open <http://localhost:8000>. Or close the other window. |
| Browser didn't open | Open <http://localhost:8000> yourself. |
| Package install fails | Check your internet connection or antivirus/proxy, then run `start.bat` again. To start completely fresh, delete the `backend\.venv` folder and run `start.bat` again. |
| Export is slow | Multi-year daily planners have thousands of pages. Pages are rendered in batches, roughly 40 s per 600 pages per size and variant. You can cancel at any time. |
| Antivirus warns about `start.bat` | It is a plain text script. Open it in Notepad to see exactly what it does. |
| Something else | The black window shows the technical error. Copy it when asking for help. |

## 11. For developers

```
planner-studio/
  start.bat                 launcher (venv, pip, playwright install chromium, builds UI if missing, starts server)
  backend/
    requirements.txt        pinned, tested versions
    app/main.py             FastAPI app: /api/* + static UI + /fonts + /assets
    app/models.py           SQLModel tables (SQLite)
    app/routers/            projects.py (projects, preview, export jobs), library.py (templates, duas, settings, backup, history)
    app/services/           calendar.py, hijri.py, catalog.py, planner.py (page list + links), render.py (Jinja2),
                            pdf.py (Playwright print, batching, merge, link wiring + verification),
                            mockups.py (listing PNGs), exporter.py (background jobs, buyer guide, zip), themes.py
    app/templates/          page.html, styles.css.j2, pages/*.html (one per page type), listing/, guide.html
    app/styles/             template styles: <key>.json (+ optional <key>.css)
    app/fonts/              bundled OFL fonts + licences (+ extra/)
    tests/                  pytest: calendar + Hijri (2026–2040), planner structure, rendering, PDF links
  frontend/                 React + Vite + TypeScript + Tailwind (dist/ is the built UI)
  data/  exports/
```

**Running the tests:**

```
backend\.venv\Scripts\python -m pytest backend\tests -q
```

Run this from the `planner-studio` folder, or run `pytest` from inside `backend`.

**Developing the interface:** run `npm install` and then `npm run dev` inside `frontend`. That serves the UI on port 5173 and proxies `/api` to port 8000. Run `npm run build` when you're done.

**How links work.** Each `<a>` points to `https://planner-studio.local/p/<page-id>`. Chromium prints these as link annotations, keeping the exact clickable area of every link. After the batches are merged, pypdf rewrites each one into an internal GoTo destination for the matching page. The finished PDF is then re-opened to check that every link resolves.
