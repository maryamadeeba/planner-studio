import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api";
import { ErrorBox, Field, PageHeader, useMeta } from "../components/ui";
import TemplatePicker from "../steps/TemplatePicker";
import TypePicker from "../steps/TypePicker";

export default function NewPlanner() {
  const meta = useMeta();
  const [params] = useSearchParams();
  const nav = useNavigate();
  const [type, setType] = useState(params.get("type") || "daily");
  const [style, setStyle] = useState(params.get("style") || meta.featured_templates[0]);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const create = async () => {
    setBusy(true);
    setErr(null);
    try {
      const p = await api.post("/api/projects", { name: name.trim() || `${meta.planner_types[type].label}`, planner_type: type, style });
      nav(`/project/${p.id}/2`);
    } catch (e: any) {
      setErr(e.message);
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl p-8">
      <PageHeader title="New planner" sub="Step 1 of 8 – choose a template style and what kind of planner you are making.">
        <Link to="/templates" className="btn-ghost">Start from a saved template</Link>
      </PageHeader>
      <div className="card mb-6 p-5">
        <Field label="Project name" hint="Only for you – used for the export folder and file names.">
          <input className="input" value={name} placeholder={`e.g. 2027 ${meta.planner_types[type].label} – ${meta.themes[style]?.label ?? ""}`} onChange={(e) => setName(e.target.value)} />
        </Field>
      </div>
      <h2 className="section-title mb-3">Template style</h2>
      <div className="mb-8"><TemplatePicker value={style} onChange={setStyle} /></div>
      <h2 className="section-title mb-3">Planner type</h2>
      <TypePicker value={type} onChange={setType} />
      <ErrorBox error={err} />
      <div className="sticky bottom-0 mt-6 flex justify-end border-t border-sand-200 bg-cream py-4">
        <button className="btn-primary" disabled={busy} onClick={create}>{busy ? "Creating…" : "Continue →"}</button>
      </div>
    </div>
  );
}
