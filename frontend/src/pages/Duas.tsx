import { useEffect, useState } from "react";
import { api } from "../api";
import { Icon, PageHeader, Svg, useConfirm, useToast } from "../components/ui";

export default function Duas() {
  const toast = useToast();
  const { confirm, dialog } = useConfirm();
  const [items, setItems] = useState<any[]>([]);
  const [dirty, setDirty] = useState<Record<number, boolean>>({});
  const load = () => api.get("/api/duas").then(setItems);
  useEffect(() => { load(); }, []);
  const upd = (id: number, k: string, v: any) => { setItems((x) => x.map((d) => (d.id === id ? { ...d, [k]: v } : d))); setDirty((d) => ({ ...d, [id]: true })); };
  const save = async (d: any) => {
    try { await api.put(`/api/duas/${d.id}`, d); setDirty((x) => ({ ...x, [d.id]: false })); toast("Dua saved"); }
    catch (e: any) { toast(e.message, "error"); }
  };

  return (
    <div className="mx-auto max-w-5xl p-8">
      {dialog}
      <PageHeader title="Dua Library" sub="Arabic text, English meaning and reference. The app never writes Quranic or dua Arabic itself – paste text from a trusted source and tick “verified”.">
        <button className="btn-primary" onClick={async () => { await api.post("/api/duas", { title: "New dua", sort: items.length }); load(); }}><Svg d={Icon.plus} /> Add dua</button>
      </PageHeader>
      <div className="mb-4 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800">
        Entries marked <b>UNVERIFIED</b> show a warning on export. Placeholders in [square brackets] must be replaced before selling.
      </div>
      <div className="space-y-4">
        {items.map((d) => (
          <div key={d.id} className="card p-4">
            <div className="flex flex-wrap items-center gap-3">
              <input className="input max-w-sm font-semibold" value={d.title} onChange={(e) => upd(d.id, "title", e.target.value)} aria-label="Title" />
              <input className="input w-40" value={d.category} placeholder="Category" onChange={(e) => upd(d.id, "category", e.target.value)} aria-label="Category" />
              <label className={`flex items-center gap-2 rounded-full px-3 py-1 text-sm font-medium ${d.verified ? "bg-brand-50 text-brand-700" : "bg-rose-50 text-rose-500"}`}>
                <input type="checkbox" checked={d.verified} onChange={(e) => upd(d.id, "verified", e.target.checked)} /> {d.verified ? "Verified" : "Unverified"}
              </label>
              <div className="ml-auto flex gap-2">
                <button className="btn-primary" disabled={!dirty[d.id]} onClick={() => save(d)}>Save</button>
                <button className="btn-danger px-2" aria-label="Delete" onClick={async () => { if (await confirm(`Delete “${d.title}”?`)) { await api.del(`/api/duas/${d.id}`); load(); } }}><Svg d={Icon.trash} /></button>
              </div>
            </div>
            <textarea dir="rtl" lang="ar" className="input mt-3 h-24 text-right text-2xl leading-loose" style={{ fontFamily: "Amiri, 'Noto Naskh Arabic', serif" }}
              value={d.arabic} placeholder="النص العربي" onChange={(e) => upd(d.id, "arabic", e.target.value)} aria-label="Arabic text" />
            <textarea className="input mt-2 h-16" value={d.english} placeholder="English meaning" onChange={(e) => upd(d.id, "english", e.target.value)} aria-label="English meaning" />
            <input className="input mt-2" value={d.reference} placeholder="Reference (e.g. source, book and number)" onChange={(e) => upd(d.id, "reference", e.target.value)} aria-label="Reference" />
          </div>
        ))}
      </div>
    </div>
  );
}
