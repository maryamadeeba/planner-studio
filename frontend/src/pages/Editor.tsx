import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, setIn, type Config, type Project } from "../api";
import Preview from "../components/Preview";
import { ErrorBox, Field, Modal, useToast } from "../components/ui";
import { StepCalendar, StepOutput, StepPersonal, StepSections, StepTheme, StepType } from "../steps/Steps";
import StepExport from "../steps/StepExport";

const STEPS = ["Template & type","Calendar & dates", "Sizes & PDF", "Theme & colours", "Sections & text", "Personalisation", "Preview", "Export"];

export default function Editor() {
  const { id, step } = useParams();
  const nav = useNavigate();
  const toast = useToast();
  const s = Math.min(8, Math.max(1, +(step || 1)));
  const [project, setProject] = useState<Project | null>(null);
  const [cfg, setCfgState] = useState<Config | null>(null);
  const [name, setName] = useState("");
  const [status, setStatus] = useState<"saved" | "saving" | "dirty" | "error">("saved");
  const [err, setErr] = useState<string | null>(null);
  const [tplOpen, setTplOpen] = useState(false);
  const [tplName, setTplName] = useState("");
  const [tplTags, setTplTags] = useState("");
  const pending = useRef<{ cfg?: Config; name?: string }>({});
  const timer = useRef<number | null>(null);

  useEffect(() => {
    api.get(`/api/projects/${id}`).then((p) => { setProject(p); setCfgState(p.config); setName(p.name); }).catch((e) => setErr(e.message));
  }, [id]);

  const flush = useCallback(async () => {
    if (timer.current) { clearTimeout(timer.current); timer.current = null; }
    const body = pending.current;
    if (!body.cfg && body.name === undefined) return;
    pending.current = {};
    setStatus("saving");
    try {
      await api.put(`/api/projects/${id}`, { config: body.cfg, name: body.name });
      setStatus("saved");
    } catch (e: any) {
      setStatus("error");
      toast(`Could not save: ${e.message}`, "error");
    }
  }, [id]);

  const schedule = () => {
    setStatus("dirty");
    if (timer.current) clearTimeout(timer.current);
    timer.current = window.setTimeout(flush, 700);
  };
  useEffect(() => () => { flush(); }, [flush]);

  const setCfg = (c: Config) => { setCfgState(c); pending.current.cfg = c; schedule(); };
  const set = (path: string, value: unknown) => setCfgState((old: Config) => {
    const c = setIn(old, path, value);
    pending.current.cfg = c;
    schedule();
    return c;
  });

  if (err) return <div className="p-8"><ErrorBox error={err} /></div>;
  if (!cfg || !project) return <div className="p-8 text-sm text-sand-500">Loading project…</div>;

  const go = (n: number) => { flush(); nav(`/project/${id}/${n}`); };
  const props = { cfg, set, setCfg };
  const wide = s === 7;

  return (
    <div className="flex h-full flex-col">
      <header className="flex flex-none flex-wrap items-center gap-3 border-b border-sand-200 bg-white px-6 py-3">
        <input className="min-w-0 flex-1 rounded border border-transparent bg-transparent px-1 font-display text-xl font-semibold hover:border-sand-200 focus:border-brand-500 focus:outline-none"
          aria-label="Project name" value={name} onChange={(e) => { setName(e.target.value); pending.current.name = e.target.value; schedule(); }} />
        <span className={`text-xs ${status === "error" ? "text-rose-500" : "text-sand-500"}`}>
          {status === "saved" ? "All changes saved" : status === "saving" ? "Saving…" : status === "dirty" ? "Unsaved…" : "Save failed"}
        </span>
        <button className="btn-ghost" onClick={async () => { await flush(); setTplName(name); setTplOpen(true); }}>Save as template</button>
      </header>
      <nav className="flex flex-none gap-1 overflow-x-auto border-b border-sand-200 bg-white px-4" aria-label="Steps">
        {STEPS.map((label, i) => (
          <button key={label} onClick={() => go(i + 1)} aria-current={s === i + 1 ? "step" : undefined}
            className={`flex items-center gap-2 whitespace-nowrap border-b-2 px-3 py-2.5 text-sm transition ${s === i + 1 ? "border-brand-500 font-semibold text-brand-700" : "border-transparent text-sand-500 hover:text-ink"}`}>
            <span className={`flex h-5 w-5 items-center justify-center rounded-full text-[11px] ${s === i + 1 ? "bg-brand-500 text-white" : "bg-sand-200 text-ink"}`}>{i + 1}</span>
            {label}
          </button>
        ))}
      </nav>
      <div className="flex min-h-0 flex-1">
        {!wide && (
          <div className="flex w-[480px] flex-none flex-col border-r border-sand-200">
            <div className="min-h-0 flex-1 overflow-y-auto p-5">
              <h2 className="section-title mb-4">{s}. {STEPS[s - 1]}</h2>
              {s === 1 && <StepType {...props} />}
              {s === 2 && <StepCalendar {...props} />}
              {s === 3 && <StepOutput {...props} />}
              {s === 4 && <StepTheme {...props} />}
              {s === 5 && <StepSections {...props} />}
              {s === 6 && <StepPersonal {...props} />}
              {s === 8 && <StepExport cfg={cfg} set={set} projectId={project.id} saveNow={flush} />}
            </div>
            <div className="flex flex-none justify-between border-t border-sand-200 bg-white px-5 py-3">
              <button className="btn-ghost" disabled={s === 1} onClick={() => go(s - 1)}>← Back</button>
              {s < 8 && <button className="btn-primary" onClick={() => go(s + 1)}>Next: {STEPS[s]} →</button>}
            </div>
          </div>
        )}
        <div className="flex min-w-0 flex-1 flex-col bg-white">
          <Preview config={cfg} large={wide} />
          {wide && (
            <div className="flex flex-none justify-between border-t border-sand-200 px-5 py-3">
              <button className="btn-ghost" onClick={() => go(6)}>← Back</button>
              <button className="btn-primary" onClick={() => go(8)}>Next: Export →</button>
            </div>
          )}
        </div>
      </div>

      <Modal open={tplOpen} title="Save as template" onClose={() => setTplOpen(false)}>
        <div className="space-y-3">
          <Field label="Template name"><input className="input" value={tplName} onChange={(e) => setTplName(e.target.value)} autoFocus /></Field>
          <Field label="Tags" hint="Comma separated, e.g. pastel, daily, 2027"><input className="input" value={tplTags} onChange={(e) => setTplTags(e.target.value)} /></Field>
          <div className="flex justify-end gap-2 pt-2">
            <button className="btn-ghost" onClick={() => setTplOpen(false)}>Cancel</button>
            <button className="btn-primary" onClick={async () => {
              try {
                await api.post("/api/templates", { project_id: project.id, name: tplName, tags: tplTags });
                toast("Saved to the Template Library");
                setTplOpen(false);
              } catch (e: any) { toast(e.message, "error"); }
            }}>Save template</button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
