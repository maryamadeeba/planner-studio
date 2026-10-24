import { useEffect, useState } from "react";
import { api } from "../api";
import { Icon, PageHeader, Svg, useConfirm, useMeta, useToast } from "../components/ui";

export default function Quotes() {
  const meta = useMeta();
  const toast = useToast();
  const { confirm, dialog } = useConfirm();
  const [items, setItems] = useState<any[]>([]);
  const [dirty, setDirty] = useState<Record<number, boolean>>({});
  const [filter, setFilter] = useState("");
  const load = () => api.get("/api/quotes").then(setItems);
  useEffect(() => { load(); }, []);
  const upd = (id: number, k: string, v: any) => { setItems((x) => x.map((q) => (q.id === id ? { ...q, [k]: v } : q))); setDirty((d) => ({ ...d, [id]: true })); };
  const save = async (q: any) => {
    try { await api.put(`/api/quotes/${q.id}`, q); setDirty((x) => ({ ...x, [q.id]: false })); toast("Quote saved"); }
    catch (e: any) { toast(e.message, "error"); }
  };
  const add = async () => {
    try {
      await api.post("/api/quotes", { text: "Write your new affirmation here.", category: filter || "goals", sort: items.length });
      await load();
    } catch (e: any) { toast(e.message, "error"); }
  };
  const shown = items.filter((q) => !filter || q.category === filter);

  return (
    <div className="mx-auto max-w-4xl p-8">
      {dialog}
      <PageHeader title="Quotes Library" sub="Uplifting quotes and affirmations printed on covers, monthly, weekly and daily pages. Only use quotes you wrote yourself or that are in the public domain.">
        <button className="btn-primary" onClick={add}><Svg d={Icon.plus} /> Add quote</button>
      </PageHeader>
      <div className="mb-4 flex flex-wrap gap-1.5">
        {["", ...meta.quote_categories].map((c) => (
          <button key={c || "all"} className={`chip py-1 text-sm capitalize ${filter === c ? "chip-on" : ""}`} onClick={() => setFilter(c)}>
            {c ? (c === "faith" ? "faith-friendly" : c) : "All"} <span className="ml-1 text-xs text-sand-500">{items.filter((q) => !c || q.category === c).length}</span>
          </button>
        ))}
      </div>
      <div className="space-y-3">
        {shown.map((q) => (
          <div key={q.id} className="card p-4">
            <textarea className="input h-16 font-hand text-xl leading-snug text-ink" value={q.text} maxLength={240}
              onChange={(e) => upd(q.id, "text", e.target.value)} aria-label="Quote text" />
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <input className="input w-56" value={q.author} placeholder="Author (empty = your own words)" onChange={(e) => upd(q.id, "author", e.target.value)} aria-label="Author" />
              <select className="input w-40 capitalize" value={q.category} onChange={(e) => upd(q.id, "category", e.target.value)} aria-label="Category">
                {meta.quote_categories.map((c) => <option key={c} value={c}>{c === "faith" ? "faith-friendly" : c}</option>)}
              </select>
              <select className="input w-36" value={q.kind} onChange={(e) => upd(q.id, "kind", e.target.value)} aria-label="Type">
                <option value="affirmation">Affirmation</option><option value="quote">Quote</option>
              </select>
              <span className="text-xs text-sand-500">{q.text.length}/240</span>
              <div className="ml-auto flex gap-2">
                <button className="btn-primary" disabled={!dirty[q.id]} onClick={() => save(q)}>Save</button>
                <button className="btn-danger px-2" aria-label="Delete" onClick={async () => { if (await confirm("Delete this quote?")) { await api.del(`/api/quotes/${q.id}`); load(); } }}><Svg d={Icon.trash} /></button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
