import { useEffect, useState } from "react";
import { api, GREG_MONTHS, type Config, type Meta } from "../api";
import { Field, Toggle, useMeta, useToast } from "../components/ui";
import TypePicker from "./TypePicker";
import TemplatePicker from "./TemplatePicker";
import ColorsCard from "./Colors";
import { PicturesCard, QuotesCard } from "./Extras";

export interface StepProps {
  cfg: Config;
  set: (path: string, value: unknown) => void;
  setCfg: (c: Config) => void;
}

const Card = ({ title, children, sub }: { title: string; sub?: string; children: React.ReactNode }) => (
  <section className="card mb-4 p-5">
    <h3 className="font-semibold">{title}</h3>
    {sub && <p className="mb-3 mt-0.5 text-xs text-sand-500">{sub}</p>}
    <div className={sub ? "" : "mt-3"}>{children}</div>
  </section>
);

/** Modules actually used for the chosen period (mirrors catalog.effective_modules). */
export function effectiveModules(cfg: Config, meta: Meta): Record<string, boolean> {
  const rules = meta.period_rules[cfg.calendar.period || "year"] || meta.period_rules.year;
  const out = { ...cfg.modules };
  rules.off.forEach((m) => (out[m] = false));
  rules.on.forEach((m) => (out[m] = true));
  return out;
}

// ---------------------------------------------------------------- step 1
export function StepType({ cfg, set, setCfg }: StepProps) {
  const meta = useMeta();
  const t = cfg.theme;
  const custom = ["primary", "accent", "background", "ink"].some((k) => t[k]) || Object.values(t.pages || {}).some((p: any) => Object.values(p || {}).some(Boolean));
  return (
    <>
      <Card title="Template style" sub="Sets the colours, fonts, card style, cover layout and decorations for every page. Custom colours, pictures and quotes work on top of any template.">
        <TemplatePicker value={t.preset} onChange={(k) => set("theme.preset", k)} hasCustomColours={custom}
          onResetColours={() => setCfg({ ...cfg, theme: { ...t, primary: null, accent: null, background: null, ink: null, pages: {} } })} />
      </Card>
      <Card title="Planner type">
        <TypePicker value={cfg.planner_type} onChange={(k) => {
          const mods: Record<string, boolean> = {};
          Object.keys(meta.modules).forEach((m) => (mods[m] = meta.planner_types[k].modules.includes(m)));
          const period = meta.planner_types[k].period;
          setCfg({ ...cfg, planner_type: k, modules: mods, calendar: period ? { ...cfg.calendar, period } : cfg.calendar });
        }} />
      </Card>
    </>
  );
}

// ---------------------------------------------------------------- step 2
const EVENT_LABELS: Record<string, string> = {
  new_year: "Islamic New Year (1 Muharram)", ashura: "Ashura (10 Muharram)", ramadan_start: "Start of Ramadan (1 Ramadan)",
  last_ten: "Last ten nights (21–29 Ramadan, odd nights highlighted)", eid_fitr: "Eid al-Fitr (1 Shawwal)",
  arafah: "Day of Arafah (9 Dhul Hijjah)", eid_adha: "Eid al-Adha (10 Dhul Hijjah)",
};

export function StepCalendar({ cfg, set, setCfg }: StepProps) {
  const meta = useMeta();
  const c = cfg.calendar;
  const hijri = c.mode === "hijri";
  const months = hijri ? meta.hijri.months : GREG_MONTHS;
  const years = hijri ? range(meta.hijri.min[0], meta.hijri.max[0]) : range(2026, 2040);
  const switchMode = (mode: string) => {
    if (mode === c.mode) return;
    const cal = mode === "hijri"
      ? { ...c, mode, start_year: 1448, start_month: 1, end_year: 1448, end_month: 12, period_year: 1448, period_month: 1, ramadan_year: null }
      : { ...c, mode, start_year: 2027, start_month: 1, end_year: 2027, end_month: 12, period_year: 2026, period_month: 11, ramadan_year: null };
    setCfg({ ...cfg, calendar: cal });
  };
  const start = c.start_year * 100 + c.start_month;
  const end = c.end_year * 100 + c.end_month;
  const period: string = c.period || "year";
  const dated = c.dated !== false;
  const canUndate = meta.undated_modules.some((m) => effectiveModules(cfg, meta)[m]);
  const periods = Object.entries(meta.period_rules).filter(([k]) => dated || k !== "custom");
  const pYear = c.period_year ?? (hijri ? 1448 : 2026);
  const yearSelect = (
    <select className="input w-28" value={pYear} onChange={(e) => set("calendar.period_year", +e.target.value)} aria-label="Year">
      {years.map((y) => <option key={y} value={y}>{y}{hijri ? " AH" : ""}</option>)}
    </select>
  );
  return (
    <>
      <Card title="Period" sub="How much time this planner covers. Short periods never include year-level pages.">
        <div className="flex flex-wrap gap-2" role="group" aria-label="Period">
          {periods.map(([k, r]) => (
            <button key={k} className={`chip ${period === k ? "chip-on" : ""}`} aria-pressed={period === k} onClick={() => set("calendar.period", k)}>{r.label}</button>
          ))}
        </div>
        {dated && period === "month" && (
          <div className="mt-4 flex gap-2">
            <select className="input" value={c.period_month ?? 1} onChange={(e) => set("calendar.period_month", +e.target.value)} aria-label="Month">
              {months.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
            </select>
            {yearSelect}
          </div>
        )}
        {dated && period === "quarter" && (
          <div className="mt-4 flex gap-2">
            {[1, 2, 3, 4].map((q) => (
              <button key={q} className={`chip ${(c.period_quarter ?? 1) === q ? "chip-on" : ""}`} onClick={() => set("calendar.period_quarter", q)}>Q{q}</button>
            ))}
            {yearSelect}
          </div>
        )}
        {dated && period === "week" && (
          <div className="mt-4">
            <Field label="Any day in the week" hint={`Weeks run Monday to Sunday.${hijri ? " Pick the date in the Gregorian calendar – the pages show Hijri dates." : ""}`}>
              <input type="date" className="input w-48" min="2026-01-05" max="2040-12-31" value={c.week_start || ""} onChange={(e) => set("calendar.week_start", e.target.value)} />
            </Field>
            {c.week_start && <p className="mt-2 text-sm text-brand-700">{weekText(c.week_start)}</p>}
          </div>
        )}
        {dated && period === "custom" && (
          <div className="mt-4 grid grid-cols-2 gap-3">
            <Field label="First day"><input type="date" className="input" min="2026-01-01" max="2040-12-31" value={c.range_start || ""} onChange={(e) => set("calendar.range_start", e.target.value)} /></Field>
            <Field label="Last day"><input type="date" className="input" min="2026-01-01" max="2040-12-31" value={c.range_end || ""} onChange={(e) => set("calendar.range_end", e.target.value)} /></Field>
            {c.range_start && c.range_end && c.range_end < c.range_start && <p className="col-span-2 text-sm text-rose-500">The last day is before the first day.</p>}
            <p className="col-span-2 text-xs text-sand-500">Up to one year. Month calendars are included for every month the range touches; days outside the range are greyed out.{hijri ? " Dates are picked in the Gregorian calendar – the pages show Hijri dates." : ""}</p>
          </div>
        )}
        {!dated && period !== "year" && (
          <p className="mt-3 text-xs text-sand-500">{period === "month" ? "One blank month with 5 ‘Week of’ spreads." : period === "quarter" ? "A blank quarter overview with 3 blank months." : "One blank Monday–Sunday week."}</p>
        )}
      </Card>
      {canUndate && (
        <Card title="Dates" sub="Undated pages have blank “Month: ____”, “Week of: ____” and “Date: ____” fields with weekday headings only, so one file can be reused.">
          <div className="grid grid-cols-2 gap-3">
            {[[true, "Dated", "Real dates printed on every page"], [false, "Undated", "Fill in the dates yourself – reusable"]].map(([v, l, d]) => (
              <button key={String(v)} type="button" aria-pressed={dated === v}
                onClick={() => setCfg({ ...cfg, calendar: { ...c, dated: v, period: !v && period === "custom" ? "month" : period } })}
                className={`card p-3 text-left ${dated === v ? "border-brand-500 ring-2 ring-brand-100" : ""}`}>
                <div className="font-semibold">{l as string}</div><div className="text-xs text-sand-500">{d as string}</div>
              </button>
            ))}
          </div>
        </Card>
      )}
      {!dated && canUndate ? null : <>
      <Card title="Calendar mode" sub="The two calendars are never mixed on a page.">
        <div className="grid grid-cols-2 gap-3">
          {[["gregorian", "Gregorian", "January – December, AD dates"], ["hijri", "Hijri", "Muharram – Dhul Hijjah, AH dates (Umm al-Qura)"]].map(([k, l, d]) => (
            <button key={k} type="button" aria-pressed={c.mode === k} onClick={() => switchMode(k)}
              className={`card p-3 text-left ${c.mode === k ? "border-brand-500 ring-2 ring-brand-100" : ""}`}>
              <div className="font-semibold">{l}</div><div className="text-xs text-sand-500">{d}</div>
            </button>
          ))}
        </div>
      </Card>
      <Card title={period === "year" ? "Date range" : "Week numbers"} sub={period !== "year" ? undefined : hijri ? "Hijri months from Rajab 1447 to Dhul Hijjah 1462 (covers 2026–2040)." : "Any range between January 2026 and December 2040. Can span several years."}>
        {period === "year" && <>
        <div className="grid gap-3">
          <Field label="Start">
            <div className="flex gap-2">
              <select className="input" value={c.start_month} onChange={(e) => set("calendar.start_month", +e.target.value)}>
                {months.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
              </select>
              <select className="input w-28" value={c.start_year} onChange={(e) => set("calendar.start_year", +e.target.value)}>
                {years.map((y) => <option key={y} value={y}>{y}</option>)}
              </select>
            </div>
          </Field>
          <Field label="End">
            <div className="flex gap-2">
              <select className="input" value={c.end_month} onChange={(e) => set("calendar.end_month", +e.target.value)}>
                {months.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
              </select>
              <select className="input w-28" value={c.end_year} onChange={(e) => set("calendar.end_year", +e.target.value)}>
                {years.map((y) => <option key={y} value={y}>{y}</option>)}
              </select>
            </div>
          </Field>
        </div>
        {end < start && <p className="mt-2 text-sm text-rose-500">The end month is before the start month.</p>}
        </>}
        <div className={period === "year" ? "mt-3" : ""}><Toggle checked={!!c.iso_weeks} onChange={(v) => set("calendar.iso_weeks", v)} label="Show ISO week numbers" hint="Weeks always start on Monday." /></div>
      </Card>
      {hijri && (
        <>
          <Card title="Hijri adjustment" sub="Shift all Hijri dates to match local moon sighting. Pakistan is often −1 compared with Umm al-Qura.">
            <div className="flex gap-2">
              {[-2, -1, 0, 1, 2].map((o) => (
                <button key={o} className={`chip ${+c.hijri_offset === o ? "chip-on" : ""}`} onClick={() => set("calendar.hijri_offset", o)}>
                  {o > 0 ? `+${o}` : o} day{Math.abs(o) === 1 ? "" : "s"}
                </button>
              ))}
            </div>
            <div className="mt-3"><Toggle checked={!!c.arabic_month_names} onChange={(v) => set("calendar.arabic_month_names", v)} label="Show Arabic month names in headings" /></div>
          </Card>
          <Card title="Islamic events" sub="Marked automatically on calendar pages.">
            {Object.entries(EVENT_LABELS).map(([k, l]) => (
              <Toggle key={k} checked={c.events?.[k] !== false} onChange={(v) => set(`calendar.events.${k}`, v)} label={l} />
            ))}
            <EventList title="Custom Hijri events" items={c.custom_hijri_events || []} months={meta.hijri.months}
              onChange={(v) => set("calendar.custom_hijri_events", v)} />
          </Card>
        </>
      )}
      {!hijri && (
        <Card title="Holidays (optional)" sub="Only the holidays you add here are printed – nothing is added automatically.">
          <EventList title="" items={c.gregorian_holidays || []} months={GREG_MONTHS} withYear onChange={(v) => set("calendar.gregorian_holidays", v)} />
        </Card>
      )}
      {(cfg.modules.ramadan_tracker || cfg.modules.ramadan_day || cfg.modules.last_ten || cfg.modules.meal_planner) && (
        <Card title="Ramadan year" sub="Which Ramadan the Ramadan pages are for.">
          <select className="input" value={c.ramadan_year ?? ""} onChange={(e) => set("calendar.ramadan_year", e.target.value ? +e.target.value : null)}>
            <option value="">Automatic – first Ramadan in the date range</option>
            {range(1447, 1462).map((y) => <option key={y} value={y}>Ramadan {y} AH</option>)}
          </select>
        </Card>
      )}
      </>}
    </>
  );
}

function weekText(iso: string) {
  const d = new Date(`${iso}T12:00:00`);
  if (isNaN(d.getTime())) return "";
  const mon = new Date(d);
  mon.setDate(d.getDate() - ((d.getDay() + 6) % 7));
  const sun = new Date(mon);
  sun.setDate(mon.getDate() + 6);
  const f = (x: Date, y = false) => x.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short", ...(y ? { year: "numeric" } : {}) });
  return `${f(mon)} – ${f(sun, true)}`;
}

function EventList({ title, items, months, onChange, withYear = false }: {
  title: string; items: any[]; months: string[]; onChange: (v: any[]) => void; withYear?: boolean;
}) {
  const upd = (i: number, k: string, v: any) => onChange(items.map((x, j) => (j === i ? { ...x, [k]: v } : x)));
  return (
    <div className="mt-3">
      {title && <div className="label">{title}</div>}
      <div className="space-y-2">
        {items.map((ev, i) => (
          <div key={i} className="flex gap-2">
            <select className="input w-36" value={ev.month} onChange={(e) => upd(i, "month", +e.target.value)} aria-label="Month">
              {months.map((m, k) => <option key={m} value={k + 1}>{m}</option>)}
            </select>
            <input className="input w-16" type="number" min={1} max={31} value={ev.day} onChange={(e) => upd(i, "day", +e.target.value)} aria-label="Day" />
            {withYear && <input className="input w-20" type="number" placeholder="Every yr" value={ev.year ?? ""} onChange={(e) => upd(i, "year", e.target.value ? +e.target.value : null)} aria-label="Year (optional)" />}
            <input className="input flex-1" placeholder="Event name" value={ev.name} onChange={(e) => upd(i, "name", e.target.value)} aria-label="Event name" />
            <button className="btn-danger px-2" aria-label="Remove" onClick={() => onChange(items.filter((_, j) => j !== i))}>×</button>
          </div>
        ))}
      </div>
      <button className="btn-ghost mt-2" onClick={() => onChange([...items, { month: 1, day: 1, name: "" }])}>+ Add event</button>
    </div>
  );
}

function range(a: number, b: number) {
  return Array.from({ length: b - a + 1 }, (_, i) => a + i);
}

// ---------------------------------------------------------------- step 3
export function StepOutput({ cfg, set }: StepProps) {
  const meta = useMeta();
  const o = cfg.output;
  const toggleIn = (path: string, list: string[], v: string) =>
    set(path, list.includes(v) ? list.filter((x) => x !== v) : [...list, v]);
  return (
    <>
      <Card title="Page sizes" sub="Pick several – each size is exported in one click.">
        <div className="flex flex-wrap gap-2">
          {Object.entries(meta.sizes).map(([k, s]) => (
            <button key={k} className={`chip ${o.sizes.includes(k) ? "chip-on" : ""}`} aria-pressed={o.sizes.includes(k)} onClick={() => toggleIn("output.sizes", o.sizes, k)}>{s.label}</button>
          ))}
        </div>
        {o.sizes.length === 0 && <p className="mt-2 text-sm text-rose-500">Choose at least one size.</p>}
      </Card>
      <Card title="PDF variants">
        <Toggle checked={o.variants.includes("digital")} onChange={() => toggleIn("output.variants", o.variants, "digital")}
          label="Digital (hyperlinked)" hint="For GoodNotes / Notability: side tabs, clickable dates, home & back buttons, index." />
        <Toggle checked={o.variants.includes("printable")} onChange={() => toggleIn("output.variants", o.variants, "printable")}
          label="Printable" hint="No links, safe home-printing margins, page numbers." />
        {o.variants.includes("printable") && (
          <div className="ml-12 mt-1 border-l border-sand-200 pl-4">
            <Toggle checked={o.binder_margin} onChange={(v) => set("output.binder_margin", v)} label="Binder / hole-punch margin" />
            <Toggle checked={o.ink_saving} onChange={(v) => set("output.ink_saving", v)} label="Ink-saving (lighter fills)" />
          </div>
        )}
      </Card>
      <Card title="Extras">
        <Toggle checked={o.buyer_guide} onChange={(v) => set("output.buyer_guide", v)} label="Buyer “How to use” PDF" />
        <Toggle checked={o.listing_images} onChange={(v) => set("output.listing_images", v)} label="Etsy listing images (2000 × 2000 PNG)" />
        {o.listing_images && <div className="ml-12"><Toggle checked={o.listing_landscape} onChange={(v) => set("output.listing_landscape", v)} label="Also 2700 × 2025 versions" /></div>}
      </Card>
      <Card title="File size (Etsy limit 20 MB per file)">
        <Toggle checked={o.compress_images} onChange={(v) => set("output.compress_images", v)} label="Compress images" hint="Downscales the cover image and logo before embedding." />
        {(cfg.calendar.period || "year") === "year" && cfg.calendar.dated !== false ? (
          <Field label="Split into several PDFs">
            <select className="input" value={o.split} onChange={(e) => set("output.split", e.target.value)}>
              <option value="none">No – one file per size/variant</option>
              <option value="year">One file per year</option>
              <option value="half">One file per half-year</option>
            </select>
          </Field>
        ) : <p className="text-xs text-sand-500">Short-period and undated planners are always exported as one file per size/variant.</p>}
      </Card>
    </>
  );
}

// ---------------------------------------------------------------- step 4
export function StepTheme({ cfg, set }: StepProps) {
  const meta = useMeta();
  const t = cfg.theme;
  const preset = meta.themes[t.preset] || meta.themes[meta.featured_templates[0]];
  return (
    <>
      <Card title="Template style" sub="The same choice as in step 1. Colours below are applied on top of it.">
        <div className="grid grid-cols-2 gap-3">
          {Object.entries(meta.themes).map(([k, th]: [string, any]) => (
            <button key={k} aria-pressed={t.preset === k} onClick={() => set("theme.preset", k)}
              className={`card overflow-hidden text-left ${t.preset === k ? "border-brand-500 ring-2 ring-brand-100" : ""}`}>
              <div className="flex h-10">{th.swatches.map((c: string) => <span key={c} className="flex-1" style={{ background: c }} />)}</div>
              <div className="p-3">
                <div className="text-sm font-semibold" style={{ fontFamily: th.title_font }}>{th.label}</div>
                <div className="text-xs text-sand-500">{th.title_font} · {th.body_font}</div>
              </div>
            </button>
          ))}
        </div>
      </Card>
      <ColorsCard cfg={cfg} set={set} />
      <Card title="Fonts & style">
        <div className="grid grid-cols-2 gap-3">
          <Field label="Heading font">
            <select className="input" value={t.heading_font || ""} onChange={(e) => set("theme.heading_font", e.target.value || null)}>
              <option value="">Preset ({preset.heading_font})</option>
              {meta.fonts.english.map((f) => <option key={f} value={f}>{f}</option>)}
            </select>
          </Field>
          <Field label="Body font">
            <select className="input" value={t.body_font || ""} onChange={(e) => set("theme.body_font", e.target.value || null)}>
              <option value="">Preset ({preset.body_font})</option>
              {meta.fonts.english.map((f) => <option key={f} value={f}>{f}</option>)}
            </select>
          </Field>
          <Field label="Corners">
            <select className="input" value={t.corner || ""} onChange={(e) => set("theme.corner", e.target.value || null)}>
              <option value="">Preset ({preset.corner})</option>
              <option value="square">Square</option><option value="soft">Soft</option><option value="rounded">Rounded</option>
            </select>
          </Field>
          <Field label="Notes area lines">
            <select className="input" value={t.line_style} onChange={(e) => set("theme.line_style", e.target.value)}>
              <option value="lined">Lined</option><option value="dotted">Dotted</option><option value="grid">Grid</option><option value="blank">Blank</option>
            </select>
          </Field>
        </div>
        <p className="mt-3 text-xs text-sand-500">Arabic text always uses Amiri (embedded). Add more fonts: see README → “Adding fonts”.</p>
      </Card>
    </>
  );
}

// ---------------------------------------------------------------- step 5
export function StepSections({ cfg, set }: StepProps) {
  const meta = useMeta();
  const [open, setOpen] = useState<string | null>(null);
  const [duas, setDuas] = useState<any[]>([]);
  useEffect(() => { api.get("/api/duas").then(setDuas); }, []);
  const groups = Object.entries(meta.modules).reduce<Record<string, [string, any][]>>((acc, [k, v]) => {
    (acc[v.group] ||= []).push([k, v]);
    return acc;
  }, {});
  const lay = cfg.layout;
  const num = (path: string, v: number, min: number, max: number, label: string) => (
    <Field label={label}><input className="input w-24" type="number" min={min} max={max} value={v}
      onChange={(e) => set(path, Math.max(min, Math.min(max, +e.target.value || min)))} /></Field>
  );
  const listEdit = (path: string, items: string[], label: string, hint?: string) => (
    <Field label={label} hint={hint ?? "One per line."}>
      <textarea className="input h-28" value={items.join("\n")} onChange={(e) => set(path, e.target.value.split("\n"))} />
    </Field>
  );

  const extra = (m: string) => {
    switch (m) {
      case "week":
        return (
          <Field label="Weekly layout">
            <div className="flex gap-2">{["vertical", "horizontal", "boxed"].map((l) => (
              <button key={l} className={`chip capitalize ${lay.week_layout === l ? "chip-on" : ""}`} onClick={() => set("layout.week_layout", l)}>{l}</button>
            ))}</div>
          </Field>
        );
      case "day":
        return (
          <div className="flex flex-wrap items-end gap-3">
            {num("layout.day_start", lay.day_start, 0, 12, "Schedule starts")}
            {num("layout.day_end", lay.day_end, 13, 23, "Schedule ends")}
            {num("layout.water_glasses", lay.water_glasses, 4, 12, "Water glasses")}
            <Toggle checked={lay.half_hours} onChange={(v) => set("layout.half_hours", v)} label="Half-hour lines" />
          </div>
        );
      case "month_habits":
        return <div className="space-y-3">{num("layout.habit_rows", lay.habit_rows, 3, 20, "Habit rows")}{listEdit("habits", cfg.habits, "Pre-filled habits")}</div>;
      case "goal_smart": return num("layout.goals_count", lay.goals_count, 1, 10, "Number of goals");
      case "notes": return num("layout.notes_pages", lay.notes_pages, 1, 50, "Notes pages");
      case "gratitude": return num("layout.gratitude_pages", lay.gratitude_pages, 1, 30, "Gratitude pages");
      case "scripting": return num("layout.scripting_pages", lay.scripting_pages, 1, 30, "Scripting pages");
      case "dua_journal": return num("layout.dua_journal_pages", lay.dua_journal_pages, 1, 30, "Journal pages");
      case "reflection": return num("layout.reflection_pages", lay.reflection_pages, 1, 30, "Reflection pages");
      case "affirmations": return listEdit("affirmations", cfg.affirmations, "Affirmations", "One per line. In ‘name throughout’ mode, “I am…” becomes “I, Name, am…”.");
      case "eid_prep": return listEdit("eid_checklist", cfg.eid_checklist, "Checklist items");
      case "dua_list": {
        const ids: number[] = cfg.dua_ids || [];
        return (
          <Field label="Duas to include" hint="None ticked = all duas in the library. Unverified duas trigger a warning on export.">
            <div className="max-h-48 space-y-1 overflow-auto rounded-lg border border-sand-200 p-2">
              {duas.map((d) => (
                <label key={d.id} className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={ids.includes(d.id)} onChange={() => set("dua_ids", ids.includes(d.id) ? ids.filter((x) => x !== d.id) : [...ids, d.id])} />
                  {d.title} {!d.verified && <span className="rounded bg-rose-50 px-1.5 text-[10px] font-bold text-rose-500">UNVERIFIED</span>}
                </label>
              ))}
            </div>
          </Field>
        );
      }
      default: return null;
    }
  };

  const rules = meta.period_rules[cfg.calendar.period || "year"] || meta.period_rules.year;
  const eff = effectiveModules(cfg, meta);

  return (
    <>
      {rules.on.length + rules.off.length > 0 && (
        <p className="mb-4 rounded-lg bg-brand-50 p-3 text-xs text-brand-700">
          <b>{rules.label}:</b> the start page{rules.on.includes("month") ? ", month calendar and goals & notes page are" : rules.on.includes("week") ? " and week page are" : " is"} always included.
          Year-level pages are switched off. Change the period in step 2.
        </p>
      )}
      {Object.entries(groups).map(([g, items]) => (
        <Card key={g} title={g}>
          <div className="divide-y divide-sand-100">
            {items.map(([k, v]) => {
              const on = !!eff[k];
              const locked = rules.on.includes(k) || rules.off.includes(k);
              const prefixes = meta.label_prefix[k] || [];
              const labelKeys = Object.keys(meta.labels).filter((lk) => prefixes.some((p) => lk === p || lk.startsWith(p)));
              const hasDetail = on && (v.sections.length > 0 || labelKeys.length > 0 || extra(k));
              return (
                <div key={k} className="py-1">
                  <div className="flex items-center justify-between">
                    <Toggle checked={on} disabled={locked} onChange={(val) => set(`modules.${k}`, val)} label={v.label}
                      hint={locked ? (on ? `Always included – ${rules.label.toLowerCase()}` : `Not used for a ${rules.label.toLowerCase()}`) : undefined} />
                    {hasDetail && (
                      <button className="text-xs font-semibold text-brand-600 hover:underline" aria-expanded={open === k} onClick={() => setOpen(open === k ? null : k)}>
                        {open === k ? "Close" : "Sections & text"}
                      </button>
                    )}
                  </div>
                  {hasDetail && open === k && (
                    <div className="mb-3 ml-12 space-y-4 rounded-lg bg-sand-50 p-4">
                      {v.sections.length > 0 && (
                        <div>
                          <div className="label">Show sections</div>
                          <div className="grid grid-cols-2">{v.sections.map((s: any) => {
                            const key = `${k}.${s.key}`;
                            return <Toggle key={key} checked={cfg.sections[key] !== false} onChange={(val) => set(`sections.${key.replace(/\./g, "\u0000")}`, val)} label={s.label} />;
                          })}</div>
                        </div>
                      )}
                      {extra(k)}
                      {labelKeys.length > 0 && (
                        <div>
                          <div className="label">Edit text</div>
                          <div className="space-y-2">{labelKeys.map((lk) => (
                            <input key={lk} className={`input ${lk.startsWith("ar.") ? "text-right" : ""}`} dir={lk.startsWith("ar.") ? "rtl" : undefined}
                              aria-label={lk} placeholder={meta.labels[lk]} value={cfg.labels[lk] ?? ""}
                              onChange={(e) => set(`labels.${lk.replace(/\./g, "\u0000")}`, e.target.value)} />
                          ))}</div>
                          <p className="mt-1 text-xs text-sand-500">Leave empty to keep the default shown in grey.</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </Card>
      ))}
      <Card title="Navigation text (digital)">
        <div className="grid grid-cols-2 gap-2">
          {["nav.home", "nav.back"].map((lk) => (
            <input key={lk} className="input" aria-label={lk} placeholder={meta.labels[lk]} value={cfg.labels[lk] ?? ""}
              onChange={(e) => set(`labels.${lk.replace(/\./g, "\u0000")}`, e.target.value)} />
          ))}
        </div>
      </Card>
    </>
  );
}

// ---------------------------------------------------------------- step 6
export function StepPersonal({ cfg, set }: StepProps) {
  const toast = useToast();
  const p = cfg.personalization;
  const f = cfg.footer;
  const upload = async (file: File | undefined, path: string) => {
    if (!file) return;
    try {
      const r = await api.upload("/api/assets", file);
      set(path, r.name);
    } catch (e: any) {
      toast(e.message, "error");
    }
  };
  return (
    <>
      <Card title="Name personalisation">
        <Field label="Name"><input className="input" value={p.name} placeholder="e.g. Ayesha (leave empty for no name)" onChange={(e) => set("personalization.name", e.target.value)} /></Field>
        <div className="mt-3 grid grid-cols-2 gap-3">
          {[["cover", "Name on cover only"], ["throughout", "Cover + throughout"]].map(([k, l]) => (
            <button key={k} aria-pressed={p.mode === k} onClick={() => set("personalization.mode", k)}
              className={`card p-3 text-left text-sm ${p.mode === k ? "border-brand-500 ring-2 ring-brand-100" : ""}`}>
              <div className="font-semibold">{l}</div>
              <div className="text-xs text-sand-500">{k === "cover" ? "Name only appears on the cover." : "“Ayesha's Week” headers, personalised affirmations and footers."}</div>
            </button>
          ))}
        </div>
        <p className="mt-2 text-xs text-sand-500">Long names shrink automatically to stay inside the margins.</p>
      </Card>
      <Card title="Cover">
        <div className="space-y-3">
          <Field label="Cover title" hint="Leave empty to use the planner type, e.g. “Daily Planner”.">
            <input className="input" value={cfg.labels["cover.title"] ?? ""} onChange={(e) => set("labels.cover\u0000title", e.target.value)} />
          </Field>
          <Field label="Subtitle / quote"><input className="input" value={p.subtitle} placeholder="Plan with intention, live with purpose" onChange={(e) => set("personalization.subtitle", e.target.value)} /></Field>
          <Toggle checked={p.monogram} onChange={(v) => set("personalization.monogram", v)} label="Monogram initial (needs a name)" />
          <Toggle checked={p.show_year} onChange={(v) => set("personalization.show_year", v)} label={cfg.calendar.dated === false ? "Show “Year: ____” on cover" : "Show year / period on cover"} />
          <Toggle checked={p.cover_logo !== false} onChange={(v) => set("personalization.cover_logo", v)} label="Show shop logo on cover" hint="Uses the logo from Settings (or this project's footer logo)." />
        </div>
      </Card>
      <PicturesCard cfg={cfg} set={set} />
      <QuotesCard cfg={cfg} set={set} />
      <Card title="Shop footer">
        <Toggle checked={f.enabled} onChange={(v) => set("footer.enabled", v)} label="Show shop footer on pages" />
        {f.enabled && (
          <div className="mt-3 space-y-3">
            <Field label="Footer text"><input className="input" value={f.text} onChange={(e) => set("footer.text", e.target.value)} /></Field>
            <Field label="Logo (PNG)">
              <div className="flex items-center gap-3">
                {f.logo && <img src={`/assets/${f.logo}`} alt="" className="h-10 w-auto" />}
                <input type="file" accept="image/png" className="text-sm" onChange={(e) => upload(e.target.files?.[0], "footer.logo")} />
                {f.logo && <button className="btn-ghost" onClick={() => set("footer.logo", null)}>Remove</button>}
              </div>
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Position">
                <select className="input" value={f.position} onChange={(e) => set("footer.position", e.target.value)}>
                  <option value="left">Left</option><option value="center">Centre</option><option value="right">Right</option>
                </select>
              </Field>
              <Field label={`Opacity ${Math.round(f.opacity * 100)}%`}>
                <input type="range" min={0.15} max={1} step={0.05} value={f.opacity} className="w-full accent-brand-600" onChange={(e) => set("footer.opacity", +e.target.value)} />
              </Field>
            </div>
          </div>
        )}
      </Card>
    </>
  );
}
