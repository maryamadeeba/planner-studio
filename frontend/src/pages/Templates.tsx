import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, fmtDate } from "../api";
import { Field, Icon, Modal, PageHeader, Svg, useConfirm, useMeta, useToast } from "../components/ui";

export default function Templates() {
  const meta = useMeta();
  const nav = useNavigate();
  const toast = useToast();
  const { confirm, dialog } = useConfirm();
  const [items, setItems] = useState<any[]>([]);
  const [q, setQ] = useState("");
  const [type, setType] = useState("");
  const [theme, setTheme] = useState("");
  const [mode, setMode] = useState("");
  const [edit, setEdit] = useState<any>(null);
  const [newFrom, setNewFrom] = useState<any>(null);
  const [newName, setNewName] = useState("");

  const load = () => {
    const p = new URLSearchParams({ q, planner_type: type, theme, mode });
    api.get(`/api/templates?${p}`).then(setItems);
  };
  useEffect(() => { const t = setTimeout(load, 200); return () => clearTimeout(t); }, [q, type, theme, mode]);
  useEffect(() => {
    // thumbnails are generated in the background – refresh once shortly after
    if (items.some((i) => !i.thumbnail)) { const t = setTimeout(load, 6000); return () => clearTimeout(t); }
  }, [items]);

  return (
    <div className="mx-auto max-w-6xl p-8">
      {dialog}
      <PageHeader title="Template Library" sub="Reusable planner set-ups. Start a new planner from any template and just change the year, name or size." />
      <div className="mb-6 flex flex-wrap gap-3">
        <input className="input max-w-xs" placeholder="Search name or tag…" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search templates" />
        <select className="input w-auto" value={type} onChange={(e) => setType(e.target.value)} aria-label="Planner type">
          <option value="">All planner types</option>
          {Object.entries(meta.planner_types).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
        </select>
        <select className="input w-auto" value={theme} onChange={(e) => setTheme(e.target.value)} aria-label="Theme">
          <option value="">All themes</option>
          {Object.entries(meta.themes).map(([k, v]: [string, any]) => <option key={k} value={k}>{v.label}</option>)}
        </select>
        <select className="input w-auto" value={mode} onChange={(e) => setMode(e.target.value)} aria-label="Calendar mode">
          <option value="">Gregorian & Hijri</option><option value="gregorian">Gregorian</option><option value="hijri">Hijri</option>
        </select>
      </div>
      {items.length === 0 && <div className="card p-8 text-center text-sm text-sand-500">No templates yet. Open a project and click “Save as template”.</div>}
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {items.map((t) => (
          <div key={t.id} className="card flex flex-col overflow-hidden">
            <div className="flex aspect-[3/4] items-center justify-center bg-sand-100">
              {t.thumbnail ? <img src={`${t.thumbnail}?v=${t.updated}`} alt="" className="h-full w-full object-contain" /> : <span className="text-xs text-sand-500">Generating preview…</span>}
            </div>
            <div className="flex flex-1 flex-col p-3">
              <div className="font-semibold">{t.name}</div>
              <div className="text-xs text-sand-500">{meta.planner_types[t.planner_type]?.label} · {meta.themes[t.theme]?.label.split(" /")[0]} · {t.calendar_mode}</div>
              <div className="mt-1 flex flex-wrap gap-1">{t.tags.map((g: string) => <span key={g} className="rounded bg-sand-100 px-1.5 text-[11px]">{g}</span>)}</div>
              <div className="mt-1 text-[11px] text-sand-500">{fmtDate(t.updated)}</div>
              <div className="mt-auto flex gap-1.5 pt-3">
                <button className="btn-primary flex-1 px-2" onClick={() => { setNewFrom(t); setNewName(""); }}>New from template</button>
                <button className="btn-ghost px-2" title="Rename / tags" aria-label="Rename" onClick={() => setEdit({ ...t, tags: t.tags.join(", ") })}>✎</button>
                <button className="btn-ghost px-2" title="Duplicate" aria-label="Duplicate" onClick={async () => { await api.post(`/api/templates/${t.id}/duplicate`); load(); toast("Template duplicated"); }}><Svg d={Icon.copy} /></button>
                <button className="btn-danger px-2" title="Delete" aria-label="Delete" onClick={async () => { if (await confirm(`Delete the template “${t.name}”?`)) { await api.del(`/api/templates/${t.id}`); load(); } }}><Svg d={Icon.trash} /></button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <Modal open={!!edit} title="Rename template" onClose={() => setEdit(null)}>
        {edit && (
          <div className="space-y-3">
            <Field label="Name"><input className="input" value={edit.name} onChange={(e) => setEdit({ ...edit, name: e.target.value })} /></Field>
            <Field label="Tags"><input className="input" value={edit.tags} onChange={(e) => setEdit({ ...edit, tags: e.target.value })} /></Field>
            <div className="flex justify-end gap-2"><button className="btn-ghost" onClick={() => setEdit(null)}>Cancel</button>
              <button className="btn-primary" onClick={async () => { await api.put(`/api/templates/${edit.id}`, { name: edit.name, tags: edit.tags }); setEdit(null); load(); }}>Save</button></div>
          </div>
        )}
      </Modal>
      <Modal open={!!newFrom} title="New planner from template" onClose={() => setNewFrom(null)}>
        <div className="space-y-3">
          <p className="text-sm text-sand-500">A new project is created from “{newFrom?.name}”. Next you can change the year, name and sizes.</p>
          <Field label="Project name"><input className="input" value={newName} placeholder={`${newFrom?.name} (copy)`} onChange={(e) => setNewName(e.target.value)} /></Field>
          <div className="flex justify-end gap-2"><button className="btn-ghost" onClick={() => setNewFrom(null)}>Cancel</button>
            <button className="btn-primary" onClick={async () => { const p = await api.post("/api/projects", { template_id: newFrom.id, name: newName || undefined }); nav(`/project/${p.id}/2`); }}>Create</button></div>
        </div>
      </Modal>
    </div>
  );
}
