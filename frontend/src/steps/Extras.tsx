import { Link } from "react-router-dom";
import { api, fmtBytes, type Config } from "../api";
import { Field, Toggle, useMeta, useToast } from "../components/ui";

const Section = ({ title, sub, children }: { title: string; sub?: string; children: React.ReactNode }) => (
  <section className="card mb-4 p-5">
    <h3 className="font-semibold">{title}</h3>
    {sub && <p className="mb-3 mt-0.5 text-xs text-sand-500">{sub}</p>}
    {children}
  </section>
);

const ROLES = [
  { key: "cover", title: "Cover", modes: [["framed", "Framed"], ["full", "Full-bleed"]] },
  { key: "divider", title: "Section divider pages", modes: [["framed", "Framed"], ["full", "Full-bleed"]] },
  { key: "month_header", title: "Monthly page header", modes: [["right", "Small, right"], ["left", "Small, left"], ["banner", "Banner strip"]] },
] as const;

function Chips({ value, options, onChange }: { value: string; options: readonly (readonly [string, string])[]; onChange: (v: string) => void }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {options.map(([k, l]) => <button key={k} className={`chip py-1 text-xs ${value === k ? "chip-on" : ""}`} aria-pressed={value === k} onClick={() => onChange(k)}>{l}</button>)}
    </div>
  );
}

/** Pictures on the cover, section dividers and monthly page headers (PNG / JPG, compressed on upload). */
export function PicturesCard({ cfg, set }: { cfg: Config; set: (path: string, value: unknown) => void }) {
  const toast = useToast();
  const images = cfg.images || {};
  const setAsset = (role: string, name: string | null) => {
    set(`images.${role}.asset`, name);
    if (role === "cover") set("personalization.cover_image", name);  // older field kept in sync
  };
  const upload = async (role: string, file?: File) => {
    if (!file) return;
    try {
      const r = await api.upload("/api/assets", file);
      setAsset(role, r.name);
      toast(r.original_bytes > r.bytes ? `Picture compressed: ${fmtBytes(r.original_bytes)} → ${fmtBytes(r.bytes)}` : "Picture added");
    } catch (e: any) { toast(e.message, "error"); }
  };
  return (
    <Section title="Pictures" sub="PNG or JPG. Pictures are resized and compressed automatically so your PDFs stay under Etsy's 20 MB limit.">
      <div className="space-y-5">
        {ROLES.map((role) => {
          const s = images[role.key] || {};
          const modeKey = role.key === "month_header" ? "position" : "mode";
          return (
            <div key={role.key} className="rounded-lg border border-sand-200 p-3">
              <div className="flex items-center gap-3">
                {s.asset ? <img src={`/assets/${s.asset}`} alt="" className={`h-14 w-14 flex-none object-cover ${s.shape === "circle" ? "rounded-full" : "rounded-lg"}`} />
                  : <div className="flex h-14 w-14 flex-none items-center justify-center rounded-lg bg-sand-100 text-[10px] text-sand-500">none</div>}
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-semibold">{role.title}</div>
                  {role.key === "divider" && !cfg.modules.divider && (
                    <button className="text-xs text-brand-600 hover:underline" onClick={() => set("modules.divider", true)}>Turn on section divider pages</button>
                  )}
                </div>
                <label className="btn-ghost cursor-pointer py-1 text-xs">{s.asset ? "Replace" : "Upload"}
                  <input type="file" accept="image/png,image/jpeg" className="sr-only" onChange={(e) => { upload(role.key, e.target.files?.[0]); e.target.value = ""; }} />
                </label>
                {s.asset && <button className="btn-ghost py-1 text-xs" onClick={() => setAsset(role.key, null)}>Remove</button>}
              </div>
              {s.asset && (
                <div className="mt-3 grid grid-cols-2 gap-3">
                  <Field label="Placement"><Chips value={s[modeKey]} options={role.modes} onChange={(v) => set(`images.${role.key}.${modeKey}`, v)} /></Field>
                  <Field label="Fit"><Chips value={s.fit || "cover"} options={[["cover", "Fill (crop)"], ["contain", "Whole picture"]]} onChange={(v) => set(`images.${role.key}.fit`, v)} /></Field>
                  <Field label="Shape"><Chips value={s.shape || "rounded"} options={[["rounded", "Rounded"], ["circle", "Circle"], ["square", "Square"]]} onChange={(v) => set(`images.${role.key}.shape`, v)} /></Field>
                  <Field label={`Opacity ${Math.round((s.opacity ?? 1) * 100)}%`}>
                    <input type="range" min={0.1} max={1} step={0.05} value={s.opacity ?? 1} className="w-full accent-brand-600" onChange={(e) => set(`images.${role.key}.opacity`, +e.target.value)} />
                  </Field>
                  {role.key !== "month_header" && (
                    <Field label={s.mode === "full" ? "Focus point" : "Position on page"}>
                      <Chips value={s.position || "center"} options={s.mode === "full"
                        ? [["center", "Centre"], ["top", "Top"], ["bottom", "Bottom"], ["left", "Left"], ["right", "Right"]]
                        : [["top", "Top"], ["center", "Middle"], ["bottom", "Bottom"]]} onChange={(v) => set(`images.${role.key}.position`, v)} />
                    </Field>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </Section>
  );
}

/** Quote / affirmation options: none, one per page type, or a different one on every page. */
export function QuotesCard({ cfg, set }: { cfg: Config; set: (path: string, value: unknown) => void }) {
  const meta = useMeta();
  const q = cfg.quotes || { mode: "none", categories: [], pages: {} };
  const cats: string[] = q.categories || [];
  const toggleCat = (c: string) => set("quotes.categories", cats.includes(c) ? cats.filter((x) => x !== c) : [...cats, c]);
  return (
    <Section title="Quotes & affirmations" sub="Picked from your Quotes library.">
      <Chips value={q.mode} options={[["none", "No quotes"], ["per_type", "One per page type"], ["per_page", "Different on every page"]]} onChange={(v) => set("quotes.mode", v)} />
      {q.mode !== "none" && (
        <div className="mt-4 space-y-3">
          <Field label="Themes" hint="None selected = every quote in the library.">
            <div className="flex flex-wrap gap-1.5">
              {meta.quote_categories.map((c) => <button key={c} className={`chip py-1 text-xs capitalize ${cats.includes(c) ? "chip-on" : ""}`} aria-pressed={cats.includes(c)} onClick={() => toggleCat(c)}>{c === "faith" ? "faith-friendly" : c}</button>)}
            </div>
          </Field>
          <Field label="Show on">
            <div className="grid grid-cols-2">
              {[["cover", "Cover"], ["month", "Monthly pages"], ["week", "Weekly pages"], ["day", "Daily pages (footer)"], ["divider", "Section dividers"]].map(([k, l]) => (
                <Toggle key={k} checked={q.pages?.[k] !== false} onChange={(v) => set(`quotes.pages.${k}`, v)} label={l} />
              ))}
            </div>
          </Field>
          <p className="text-xs text-sand-500">Add, edit or delete quotes in the <Link to="/quotes" className="text-brand-600 hover:underline">Quotes library</Link>.</p>
        </div>
      )}
    </Section>
  );
}
