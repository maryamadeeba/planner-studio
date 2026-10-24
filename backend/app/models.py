"""SQLite storage (SQLModel).  Database file: <planner-studio>/data/studio.db"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine, select

ROOT = Path(os.environ.get("PLANNER_STUDIO_ROOT") or Path(__file__).resolve().parents[2])
DATA_DIR = ROOT / "data"
ASSET_DIR = DATA_DIR / "assets"
THUMB_DIR = DATA_DIR / "thumbs"
DB_PATH = DATA_DIR / "studio.db"
DEFAULT_EXPORT_DIR = ROOT / "exports"
for d in (DATA_DIR, ASSET_DIR, THUMB_DIR, DEFAULT_EXPORT_DIR):
    d.mkdir(parents=True, exist_ok=True)


def now() -> datetime:
    return datetime.now().astimezone().replace(microsecond=0)


class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = "Untitled planner"
    config: str = "{}"
    created: datetime = Field(default_factory=now)
    updated: datetime = Field(default_factory=now)


class Template(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    tags: str = ""
    planner_type: str = ""
    theme: str = ""
    calendar_mode: str = ""
    config: str = "{}"
    thumbnail: Optional[str] = None
    created: datetime = Field(default_factory=now)
    updated: datetime = Field(default_factory=now)


class Dua(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    arabic: str = ""
    english: str = ""
    reference: str = ""
    category: str = ""
    verified: bool = False
    sort: int = 0


class Quote(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    author: str = ""          # empty = original (no attribution printed)
    category: str = ""        # goals | focus | habits | hope | faith
    kind: str = "affirmation"  # affirmation | quote
    sort: int = 0


class ExportRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: Optional[int] = None
    project_name: str = ""
    created: datetime = Field(default_factory=now)
    status: str = "done"
    summary: str = ""
    folder: str = ""
    files: str = "[]"
    warnings: str = "[]"


class Setting(SQLModel, table=True):
    key: str = Field(primary_key=True)
    value: str = ""


engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})

DEFAULT_SETTINGS = {
    "shop_name": "Productivity Shop by M",
    "shop_etsy": "productivityshopbym",
    "shop_logo": "",
    "shop_contact": "Questions? Message me on Etsy (productivityshopbym) – I reply within 24 hours.",
    "default_hijri_offset": "0",
    "default_theme": "sky_classic",
    "export_dir": "",
}

# One-time rebrand: values that were the old shipped defaults are replaced; anything you typed yourself is kept.
OLD_SHOP_NAME = "Maryam's Digital Prints"
REBRAND_SETTINGS = {
    "shop_name": OLD_SHOP_NAME,
    "shop_contact": "Questions? Message me on Etsy at Maryam's Digital Prints – I reply within 24 hours.",
    "default_theme": "minimal",
}

# Placeholder duas: the app NEVER generates Quranic / dua Arabic text.
PLACEHOLDER_DUAS = [
    ("Dua before eating", "Daily"), ("Dua after eating", "Daily"), ("Dua before sleeping", "Daily"),
    ("Dua upon waking", "Daily"), ("Dua for entering the home", "Daily"), ("Dua for leaving the home", "Daily"),
    ("Dua for travelling", "Travel"), ("Dua for parents", "Family"), ("Dua for forgiveness", "Forgiveness"),
    ("Dua for knowledge", "Knowledge"), ("Dua at iftar", "Ramadan"), ("Dua for Laylat al-Qadr", "Ramadan"),
]


# Starter quotes: original affirmations (no author) or public-domain lines (authors who died before 1900,
# old translations, traditional proverbs).  No copyrighted quotes.
QUOTE_CATEGORIES = ["goals", "focus", "habits", "hope", "faith"]
SEED_QUOTES = [
    # goals
    ("Small steps every day add up to big changes.", "", "goals"),
    ("I set clear goals and take one brave step toward them today.", "", "goals"),
    ("A goal without a plan is only a wish – so let's make the plan.", "", "goals"),
    ("Dream it, plan it, then gently begin.", "", "goals"),
    ("My goals are worth the time I give them.", "", "goals"),
    ("Progress, not perfection.", "", "goals"),
    ("Write it down, break it down, show up.", "", "goals"),
    ("I am becoming someone who finishes what they start.", "", "goals"),
    ("Big dreams are built on ordinary Tuesdays.", "", "goals"),
    ("This month, I choose progress over pressure.", "", "goals"),
    ("Every page I fill is a promise I keep to myself.", "", "goals"),
    ("My future is shaped by what I do today.", "", "goals"),
    ("Well done is better than well said.", "Benjamin Franklin", "goals"),
    ("A journey of a thousand miles begins with a single step.", "Laozi", "goals"),
    ("If one advances confidently in the direction of his dreams, he will meet with a success unexpected in common hours.",
     "Henry David Thoreau", "goals"),
    ("The best time to plant a tree was twenty years ago. The second best time is now.", "Proverb", "goals"),
    # focus
    ("One thing at a time, done well.", "", "focus"),
    ("I give my full attention to what matters most today.", "", "focus"),
    ("Clear desk, clear mind, clear plan.", "", "focus"),
    ("Busy is not the same as productive – choose what counts.", "", "focus"),
    ("Protect your mornings; they set the tone for the day.", "", "focus"),
    ("I say no to the noise and yes to my priorities.", "", "focus"),
    ("Do the important thing first.", "", "focus"),
    ("Calm focus beats frantic hurry.", "", "focus"),
    ("My time is precious, and I spend it with intention.", "", "focus"),
    ("Less scrolling, more living.", "", "focus"),
    ("Today I will finish one thing I have been putting off.", "", "focus"),
    ("Lost time is never found again.", "Benjamin Franklin", "focus"),
    ("While we are postponing, life speeds by.", "Seneca", "focus"),
    ("Finish each day and be done with it.", "Ralph Waldo Emerson", "focus"),
    # habits
    ("Tiny habits, repeated kindly, change everything.", "", "habits"),
    ("I show up for myself, even on slow days.", "", "habits"),
    ("Consistency is a quiet kind of magic.", "", "habits"),
    ("Missed a day? Begin again – no guilt, just a gentle restart.", "", "habits"),
    ("My habits are building the life I want.", "", "habits"),
    ("Water, rest, movement, kindness – small things, big difference.", "", "habits"),
    ("Make it easy, make it daily, make it mine.", "", "habits"),
    ("I am proud of every box I tick.", "", "habits"),
    ("A good routine is a gift to tomorrow's me.", "", "habits"),
    ("Habits are the bricks; my life is the house.", "", "habits"),
    ("Energy and persistence conquer all things.", "Benjamin Franklin", "habits"),
    ("Little by little, one travels far.", "Spanish proverb", "habits"),
    ("Slow and steady wins the race.", "Aesop", "habits"),
    ("Well begun is half done.", "Proverb", "habits"),
    # hope
    ("Every sunrise is an invitation to begin again.", "", "hope"),
    ("Better days are being planned right here.", "", "hope"),
    ("I am allowed to rest and still be proud of myself.", "", "hope"),
    ("Be gentle with yourself – you are still growing.", "", "hope"),
    ("Hard seasons do not last forever.", "", "hope"),
    ("There is so much good still ahead of me.", "", "hope"),
    ("I am grateful for today and hopeful for tomorrow.", "", "hope"),
    ("Softly, steadily, I am getting there.", "", "hope"),
    ("Hope is a plan with a pretty pen.", "", "hope"),
    ("My best chapter is still being written.", "", "hope"),
    ("Good things are coming – I am making room for them.", "", "hope"),
    ("Write it on your heart that every day is the best day in the year.", "Ralph Waldo Emerson", "hope"),
    ("The creation of a thousand forests is in one acorn.", "Ralph Waldo Emerson", "hope"),
    ("I am not afraid of storms, for I am learning how to sail my ship.", "Louisa May Alcott", "hope"),
    ("Things do not change; we change.", "Henry David Thoreau", "hope"),
    ("Fall seven times, stand up eight.", "Japanese proverb", "hope"),
    ("Bloom where you are planted.", "Traditional saying", "hope"),
    # faith-friendly (original wording)
    ("Begin with Bismillah, end with Alhamdulillah.", "", "faith"),
    ("I plan with intention and leave the outcome to God.", "", "faith"),
    ("Every blessing is a reason to say Alhamdulillah.", "", "faith"),
    ("Pray, plan, then put in the work.", "", "faith"),
    ("My prayers anchor my day; my plans give it shape.", "", "faith"),
    ("Trust the timing – the best plan is already written.", "", "faith"),
    ("Sabr today, shukr tomorrow.", "", "faith"),
    ("My heart is calm because my trust is in Allah.", "", "faith"),
    ("Faith over fear, plans with prayer.", "", "faith"),
    ("Tie your camel, then put your trust in God.", "Traditional saying", "faith"),
    ("Grateful heart, hopeful plans, peaceful mind.", "", "faith"),
]


def init_db():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        if not s.exec(select(Quote)).first():
            for i, (text, author, cat) in enumerate(SEED_QUOTES):
                s.add(Quote(text=text, author=author, category=cat, kind="quote" if author else "affirmation", sort=i))
        for k, v in DEFAULT_SETTINGS.items():
            if not s.get(Setting, k):
                s.add(Setting(key=k, value=v))
        if not s.exec(select(Dua)).first():
            for i, (title, cat) in enumerate(PLACEHOLDER_DUAS):
                s.add(Dua(title=title, category=cat, sort=i,
                          arabic="[PASTE VERIFIED ARABIC TEXT HERE]",
                          english="[Paste the verified English meaning here]",
                          reference="[Source / reference]", verified=False))
        s.commit()
        if not s.get(Setting, "rebrand_v1"):
            _rebrand(s)
            s.add(Setting(key="rebrand_v1", value="done"))
            s.commit()
        if not s.get(Setting, "templates_v1"):
            _rename_brand_preset(s)
            s.add(Setting(key="templates_v1", value="done"))
            s.commit()


def _rename_brand_preset(s: Session):
    """The 'brand' theme preset became the 'Sky Classic' template style (key sky_classic)."""
    row = s.get(Setting, "default_theme")
    if row and row.value == "brand":
        row.value = "sky_classic"
        s.add(row)
    for row in list(s.exec(select(Project)).all()) + list(s.exec(select(Template)).all()):
        cfg = loads(row.config, {}) or {}
        if (cfg.get("theme") or {}).get("preset") == "brand":
            cfg["theme"]["preset"] = "sky_classic"
            row.config = json.dumps(cfg)
            if isinstance(row, Template):
                row.theme = "sky_classic"
            s.add(row)


def _rebrand(s: Session):
    """Replace the old shop name (default settings, footers and listing shop lines) with the new brand."""
    for k, old in REBRAND_SETTINGS.items():
        row = s.get(Setting, k)
        if row and row.value == old:
            row.value = DEFAULT_SETTINGS[k]
            s.add(row)
    new_name = DEFAULT_SETTINGS["shop_name"]
    for row in list(s.exec(select(Project)).all()) + list(s.exec(select(Template)).all()):
        if OLD_SHOP_NAME in (row.config or ""):
            cfg = loads(row.config, {}) or {}
            for path in (("footer", "text"), ("listing", "shop_line")):
                sec = cfg.get(path[0]) or {}
                if sec.get(path[1]) == OLD_SHOP_NAME:
                    sec[path[1]] = new_name
            row.config = json.dumps(cfg)
            s.add(row)


def get_settings() -> dict:
    with Session(engine) as s:
        out = dict(DEFAULT_SETTINGS)
        for row in s.exec(select(Setting)).all():
            out[row.key] = row.value
        return out


def export_root() -> Path:
    p = get_settings().get("export_dir") or ""
    path = Path(p) if p.strip() else DEFAULT_EXPORT_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def loads(s: str, default=None):
    try:
        return json.loads(s)
    except Exception:
        return default
