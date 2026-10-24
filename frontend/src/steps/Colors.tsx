import { useState } from "react";
import type { Config } from "../api";
import { contrast, contrastIssues, effectiveColors, isHex, PAGE_GROUP_LABELS, ROLES } from "../contrast";
import { Toggle, useMeta } from "../components/ui";

const BRAND_SWATCHES = ["sky", "deep_sky", "ink", "text", "cream", "soft_sky", "blush", "blush_soft", "butter", "butter_soft"];

function ColorField({ label, value, inherited, onChange, swatches }: {
  label: string; value: string | null | undefined; inherited: string; onChange: (v: string | null) => void; swatches: string[];
}) {
  const shown = isHex(value) ? value : inherited;
  const [text, setText] = useState<string | null>(null);
  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <span className="label mb-0">{label}</span>
        {isHex(value) ? <button className="text-xs text-brand-600 hover:underline" onClick={() => onChange(null)}>reset</button>
          : <span className="text-[11px] text-sand-500">inherited</span>}
      </div>
      <div className="flex items-center gap-2">
        <input type="color" className="h-9 w-11 flex-none cursor-pointer rounded border border-sand-300" value={shown.toLowerCase()}
          onChange={(e) => onChange(e.target.value.toUpperCase())} aria-label={`${label} colour`} />
        <input className="input w-24 py-1.5 font-mono text-xs uppercase" value={text ?? shown} aria-label={`${label} hex`}
          onChange={(e) => { setText(e.target.value); if (isHex(e.target.value)) onChange(e.target.value.toUpperCase()); }}
          onBlur={() => setText(null)} />
      </div>
      <div className="mt-1.5 flex flex-wrap gap-1">
        {swatches.map((c) => (
          <button key={c} title={c} aria-label={`Use ${c}`} onClick={() => onChange(c)}
            className={`h-5 w-5 rounded-full border ${shown.toUpperCase() === c.toUpperCase() ? "ring-2 ring-brand-500 ring-offset-1" : "border-sand-300"}`} style={{ background: c }} />
        ))}
      </div>
    </div>
  );
}

/** Step 4 colours: one set for every page, optional overrides per page type, and a WCAG contrast guard. */
export default function ColorsCard({ cfg, set }: { cfg: Config; set: (path: string, value: unknown) => void }) {
  const meta = useMeta();
  const [group, setGroup] = useState<string>(meta.page_groups[0]);
  const tplSwatches: string[] = meta.themes[cfg.theme.preset]?.swatches || [];
  const swatches = Array.from(new Set([...tplSwatches, ...BRAND_SWATCHES.map((k) => meta.brand[k])].filter(Boolean).map((c) => c.toUpperCase())));
  const global = effectiveColors(cfg, meta);
  const pageCols = effectiveColors(cfg, meta, group);
  const pageOver = cfg.theme.pages?.[group] || {};
  const issues = contrastIssues(cfg, meta);
  const pathFor = (g: string | null, role: string) => {
    const r = ROLES.find((x) => x.key === role)!;
    return g ? `theme.pages.${g}.${role}` : `theme.${r.theme}`;
  };
  const overridden = (g: string) => Object.values(cfg.theme.pages?.[g] || {}).some(isHex);

  return (
    <>
      <section className="card mb-4 p-5">
        <h3 className="font-semibold">Colours – all pages</h3>
        <p className="mb-3 mt-0.5 text-xs text-sand-500">Leave on the theme preset, or pick your own. The preview updates as you change them.</p>
        <div className="grid grid-cols-2 gap-4">
          {ROLES.map((r) => (
            <ColorField key={r.key} label={r.label} value={cfg.theme[r.theme]} inherited={global[r.key]} swatches={swatches}
              onChange={(v) => set(`theme.${r.theme}`, v)} />
          ))}
        </div>
        <div className="mt-4 border-t border-sand-100 pt-3">
          <Toggle checked={cfg.theme.motif !== false} onChange={(v) => set("theme.motif", v)} label="Bow motif" hint="A small bow from the logo next to page titles and on the cover." />
        </div>
      </section>

      <section className="card mb-4 p-5">
        <h3 className="font-semibold">Colours per page type</h3>
        <p className="mb-3 mt-0.5 text-xs text-sand-500">Override the background or text colours for one kind of page. Empty = same as all pages.</p>
        <div className="mb-4 flex flex-wrap gap-1.5" role="tablist">
          {meta.page_groups.map((g) => (
            <button key={g} role="tab" aria-selected={group === g} className={`chip py-1 text-xs ${group === g ? "chip-on" : ""}`} onClick={() => setGroup(g)}>
              {PAGE_GROUP_LABELS[g] || g}{overridden(g) && <span className="ml-1.5 h-1.5 w-1.5 rounded-full bg-brand-500" />}
            </button>
          ))}
        </div>
        <div className="grid grid-cols-2 gap-4">
          {ROLES.map((r) => (
            <ColorField key={`${group}-${r.key}`} label={r.label} value={pageOver[r.key]} inherited={global[r.key]} swatches={swatches}
              onChange={(v) => set(`theme.pages.${group}.${r.key}`, v)} />
          ))}
        </div>
        <div className="mt-4 flex items-center gap-3 rounded-lg p-3" style={{ background: pageCols.background }}>
          <span className="font-display text-lg font-semibold" style={{ color: pageCols.heading }}>Heading</span>
          <span className="text-sm" style={{ color: pageCols.body }}>Body text sample</span>
          <span className="ml-auto h-3 w-10 rounded-full" style={{ background: pageCols.accent }} />
        </div>
        {overridden(group) && <button className="btn-ghost mt-3" onClick={() => set(`theme.pages.${group}`, {})}>Clear {PAGE_GROUP_LABELS[group]?.toLowerCase()} overrides</button>}
      </section>

      <section className={`card mb-4 p-5 ${issues.length ? "border-amber-300" : ""}`} aria-live="polite">
        <h3 className="font-semibold">Readability check</h3>
        {issues.length === 0 ? (
          <p className="mt-1 text-sm text-brand-700">✓ All text colours are easy to read on their backgrounds (WCAG contrast {meta.contrast.text}:1 for text).</p>
        ) : (
          <>
            <p className="mb-3 mt-1 text-sm text-amber-800">Some colours are hard to read. Text needs a contrast of at least {meta.contrast.text}:1; the accent (bands, icons and large hand-lettering) needs {meta.contrast.accent}:1.</p>
            <ul className="space-y-2">
              {issues.map((i) => (
                <li key={`${i.group}-${i.role}`} className="flex flex-wrap items-center gap-2 rounded-lg bg-amber-50 p-2 text-sm">
                  <span className="flex h-8 w-12 items-center justify-center rounded text-xs font-semibold" style={{ background: i.background, color: i.color }}>Aa</span>
                  <span className="flex-1"><b className="capitalize">{i.role}</b> on {i.group ? PAGE_GROUP_LABELS[i.group]?.toLowerCase() : "all pages"} · <span className="font-mono">{i.ratio}:1</span></span>
                  <span className="h-5 w-5 rounded-full border border-sand-300" style={{ background: i.fix }} title={i.fix} />
                  <button className="btn-ghost py-1 text-xs" onClick={() => set(pathFor(i.group, i.role), i.fix)}>Auto-fix → {contrast(i.fix, i.background)}:1</button>
                </li>
              ))}
            </ul>
            {issues.length > 1 && <button className="btn-primary mt-3" onClick={() => issues.forEach((i) => set(pathFor(i.group, i.role), i.fix))}>Fix all</button>}
          </>
        )}
      </section>
    </>
  );
}
