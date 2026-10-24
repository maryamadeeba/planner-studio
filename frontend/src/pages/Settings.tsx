import { useEffect, useState } from "react";
import { api } from "../api";
import { Field, PageHeader, useMeta, useToast } from "../components/ui";

export default function Settings() {
  const meta = useMeta();
  const toast = useToast();
  const [s, setS] = useState<any>(null);
  const [chromium, setChromium] = useState<any>(null);
  const [checking, setChecking] = useState(false);
  useEffect(() => { api.get("/api/settings").then(setS); }, []);
  if (!s) return <div className="p-8 text-sm text-sand-500">Loading…</div>;
  const save = async () => {
    try { setS(await api.put("/api/settings", s)); toast("Settings saved"); window.dispatchEvent(new Event("shop-logo-changed")); }
    catch (e: any) { toast(e.message, "error"); }
  };
  return (
    <div className="mx-auto max-w-3xl p-8">
      <PageHeader title="Settings" sub="Defaults used for every new planner."><button className="btn-primary" onClick={save}>Save settings</button></PageHeader>
      <section className="card mb-5 space-y-4 p-5">
        <h3 className="font-semibold">Shop</h3>
        <Field label="Shop name (footer default)"><input className="input" value={s.shop_name} onChange={(e) => setS({ ...s, shop_name: e.target.value })} /></Field>
        <Field label="Etsy shop" hint="Printed in the buyer guide as etsy.com/shop/…">
          <input className="input" value={s.shop_etsy} placeholder="productivityshopbym" onChange={(e) => setS({ ...s, shop_etsy: e.target.value.trim() })} />
        </Field>
        <Field label="Contact line (buyer instructions PDF)"><input className="input" value={s.shop_contact} onChange={(e) => setS({ ...s, shop_contact: e.target.value })} /></Field>
        <Field label="Shop logo (PNG)" hint="Used on planner covers, the buyer guide, Etsy listing images and in this app's sidebar. A transparent PNG looks best. Remember to press Save settings.">
          <div className="flex items-center gap-3">
            {s.shop_logo && <img src={`/assets/${s.shop_logo}`} alt="" className="h-10" />}
            <input type="file" accept="image/png" className="text-sm" onChange={async (e) => {
              const f = e.target.files?.[0]; if (!f) return;
              try { const r = await api.upload("/api/assets", f); setS({ ...s, shop_logo: r.name }); } catch (x: any) { toast(x.message, "error"); }
            }} />
            {s.shop_logo && <button className="btn-ghost" onClick={() => setS({ ...s, shop_logo: "" })}>Remove</button>}
          </div>
        </Field>
      </section>
      <section className="card mb-5 space-y-4 p-5">
        <h3 className="font-semibold">Defaults</h3>
        <Field label="Default Hijri offset" hint="Shifts Hijri dates to match local moon sighting (e.g. Pakistan is often −1).">
          <select className="input" value={s.default_hijri_offset} onChange={(e) => setS({ ...s, default_hijri_offset: e.target.value })}>
            {["-2", "-1", "0", "1", "2"].map((o) => <option key={o} value={o}>{+o > 0 ? `+${o}` : o} day(s)</option>)}
          </select>
        </Field>
        <Field label="Default theme">
          <select className="input" value={s.default_theme} onChange={(e) => setS({ ...s, default_theme: e.target.value })}>
            {Object.entries(meta.themes).map(([k, v]: [string, any]) => <option key={k} value={k}>{v.label}</option>)}
          </select>
        </Field>
        <Field label="Export folder" hint={`Leave empty for the default. Currently: ${s.effective_export_dir}`}>
          <div className="flex gap-2">
            <input className="input" value={s.export_dir} placeholder="e.g. C:\\Users\\Maryam\\Documents\\Planner Exports" onChange={(e) => setS({ ...s, export_dir: e.target.value })} />
            <button className="btn-ghost" onClick={() => api.post("/api/open-folder", { path: s.effective_export_dir }).catch((e) => toast(e.message, "error"))}>Open</button>
          </div>
        </Field>
      </section>
      <section className="card mb-5 space-y-3 p-5">
        <h3 className="font-semibold">Backup</h3>
        <p className="text-sm text-sand-500">Downloads one zip with your projects, templates, dua library, settings and uploaded logos/images.</p>
        <div className="flex flex-wrap gap-2">
          <a className="btn-primary" href="/api/backup">Download backup</a>
          <label className="btn-ghost cursor-pointer">Restore from backup…
            <input type="file" accept=".zip" className="sr-only" onChange={async (e) => {
              const f = e.target.files?.[0]; if (!f) return;
              if (!window.confirm("Restoring replaces your current library. Your current database is kept as studio.before-import.db. Continue?")) return;
              try { const r = await api.upload("/api/backup/import", f); toast(r.message); setS(await api.get("/api/settings")); } catch (x: any) { toast(x.message, "error"); }
            }} />
          </label>
        </div>
      </section>
      <section className="card space-y-3 p-5">
        <h3 className="font-semibold">PDF engine</h3>
        <button className="btn-ghost" disabled={checking} onClick={async () => { setChecking(true); try { setChromium((await api.get("/api/health?check_chromium=true")).chromium); } finally { setChecking(false); } }}>
          {checking ? "Checking…" : "Check Chromium"}
        </button>
        {chromium && <p className={`text-sm ${chromium.ok ? "text-brand-700" : "text-rose-500"}`}>{chromium.message}</p>}
      </section>
    </div>
  );
}
