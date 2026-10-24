import { useEffect, useState } from "react";
import { api } from "../api";
import { useMeta } from "../components/ui";

// A November 2026 compact set is enough to show a template's cover and month page.
const SAMPLE = { planner_type: "compact", calendar: { period: "month", period_year: 2026, period_month: 11 }, quotes: { mode: "per_type" } };
const cache = new Map<string, string>();

function Mini({ style, index, label }: { style: string; index: number; label: string }) {
  const key = `${style}|${index}`;
  const [html, setHtml] = useState(cache.get(key) || "");
  useEffect(() => {
    if (cache.has(key)) return;
    api.post("/api/preview/html", { config: { ...SAMPLE, theme: { preset: style } }, size: "A4", variant: "printable", index })
      .then((t: string) => { cache.set(key, t); setHtml(t); }).catch(() => {});
  }, [key]);
  const w = 793.7, h = 1122.5, width = 96, scale = width / w;
  return (
    <div className="overflow-hidden rounded border border-sand-200 bg-white" style={{ width, height: h * scale }} aria-label={label}>
      {html && <iframe title={label} srcDoc={html} tabIndex={-1}
        style={{ width: w, height: h, transform: `scale(${scale})`, transformOrigin: "0 0", pointerEvents: "none", border: 0 }} />}
    </div>
  );
}

/** "Template style" picker: featured templates with live cover + month thumbnails, older styles folded away. */
export default function TemplatePicker({ value, onChange, hasCustomColours, onResetColours }: {
  value: string; onChange: (k: string) => void; hasCustomColours?: boolean; onResetColours?: () => void;
}) {
  const meta = useMeta();
  const featured = meta.featured_templates;
  const others = Object.keys(meta.themes).filter((k) => !featured.includes(k));
  const [more, setMore] = useState(!featured.includes(value));
  return (
    <div>
      <div className="grid gap-3 sm:grid-cols-3">
        {featured.map((k) => {
          const th = meta.themes[k];
          return (
            <button key={k} type="button" aria-pressed={value === k} onClick={() => onChange(k)}
              className={`card p-3 text-left transition hover:border-brand-500 ${value === k ? "border-brand-500 ring-2 ring-brand-100" : ""}`}>
              <div className="flex gap-2"><Mini style={k} index={0} label={`${th.label} cover`} /><Mini style={k} index={1} label={`${th.label} month page`} /></div>
              <div className="mt-2 font-semibold">{th.label}</div>
              <div className="mt-0.5 text-xs leading-snug text-sand-500">{th.description}</div>
              <div className="mt-2 flex gap-1">{th.swatches.slice(0, 5).map((c: string) => <span key={c} className="h-3.5 w-3.5 rounded-full border border-sand-200" style={{ background: c }} />)}</div>
            </button>
          );
        })}
      </div>
      {hasCustomColours && onResetColours && (
        <p className="mt-3 text-xs text-sand-500">Your custom colours from step 4 stay on top of any template.{" "}
          <button className="font-semibold text-brand-600 hover:underline" onClick={onResetColours}>Use the template's own colours</button></p>
      )}
      <button className="mt-3 text-xs font-semibold text-brand-600 hover:underline" onClick={() => setMore(!more)} aria-expanded={more}>
        {more ? "Hide" : "Show"} more colour styles ({others.length})
      </button>
      {more && (
        <div className="mt-2 flex flex-wrap gap-2">
          {others.map((k) => (
            <button key={k} className={`chip gap-2 text-xs ${value === k ? "chip-on" : ""}`} onClick={() => onChange(k)}>
              <span className="flex">{meta.themes[k].swatches.slice(0, 3).map((c: string) => <span key={c} className="-mr-1 h-3 w-3 rounded-full border border-white" style={{ background: c }} />)}</span>
              {meta.themes[k].label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
