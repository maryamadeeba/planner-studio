import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, fmtDate } from "../api";
import { Icon, PageHeader, Svg, useConfirm, useMeta, useToast } from "../components/ui";

export default function Dashboard() {
  const meta = useMeta();
  const nav = useNavigate();
  const toast = useToast();
  const { confirm, dialog } = useConfirm();
  const [projects, setProjects] = useState<any[]>([]);
  const [exports, setExports] = useState<any[]>([]);
  const [chromium, setChromium] = useState<{ ok: boolean; message: string } | null>(null);

  const load = () => {
    api.get("/api/projects").then(setProjects);
    api.get("/api/exports").then((x) => setExports(x.slice(0, 5)));
  };
  useEffect(() => {
    load();
    api.get("/api/health?check_chromium=true").then((h) => setChromium(h.chromium)).catch(() => {});
  }, []);

  const groups = Object.entries(meta.planner_types).reduce<Record<string, [string, any][]>>((acc, [k, v]) => {
    (acc[v.group] ||= []).push([k, v]);
    return acc;
  }, {});

  return (
    <div className="mx-auto max-w-6xl p-8">
      {dialog}
      <PageHeader title="Assalamu alaikum, Maryam" sub="Create, preview and export planners for your Etsy shop.">
        <Link to="/new" className="btn-primary"><Svg d={Icon.plus} /> New planner</Link>
      </PageHeader>

      {chromium && !chromium.ok && (
        <div className="mb-6 rounded-xl border border-rose-500/30 bg-rose-50 p-4 text-sm text-rose-500" role="alert">
          <b>PDF engine problem.</b> {chromium.message}
        </div>
      )}

      <section className="mb-10">
        <h2 className="section-title mb-3">Start something new</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {Object.entries(groups).map(([g, items]) => (
            <div key={g} className="card p-4">
              <div className="label mb-2">{g}</div>
              <div className="flex flex-wrap gap-2">
                {items.map(([k, v]) => (
                  <button key={k} className="chip hover:border-brand-500" onClick={() => nav(`/new?type=${k}`)}>{v.label}</button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      <div className="grid gap-8 lg:grid-cols-3">
        <section className="lg:col-span-2">
          <h2 className="section-title mb-3">Your projects</h2>
          {projects.length === 0 && <div className="card p-6 text-sm text-sand-500">No projects yet – start one above.</div>}
          <div className="card divide-y divide-sand-200">
            {projects.map((p) => (
              <div key={p.id} className="flex items-center gap-3 px-4 py-3">
                <Link to={`/project/${p.id}/1`} className="min-w-0 flex-1">
                  <div className="truncate font-medium">{p.name}</div>
                  <div className="text-xs text-sand-500">{meta.planner_types[p.planner_type]?.label} · edited {fmtDate(p.updated)}</div>
                </Link>
                <Link to={`/project/${p.id}/7`} className="btn-ghost">Open</Link>
                <button className="btn-ghost" aria-label="Duplicate" title="Duplicate"
                  onClick={async () => { await api.post(`/api/projects/${p.id}/duplicate`); toast("Project duplicated"); load(); }}>
                  <Svg d={Icon.copy} />
                </button>
                <button className="btn-danger" aria-label="Delete" title="Delete"
                  onClick={async () => { if (await confirm(`Delete the project “${p.name}”? Exported files are not deleted.`)) { await api.del(`/api/projects/${p.id}`); load(); } }}>
                  <Svg d={Icon.trash} />
                </button>
              </div>
            ))}
          </div>
        </section>
        <section>
          <h2 className="section-title mb-3">Recent exports</h2>
          <div className="card divide-y divide-sand-200">
            {exports.length === 0 && <div className="p-4 text-sm text-sand-500">Nothing exported yet.</div>}
            {exports.map((e) => (
              <div key={e.id} className="px-4 py-3 text-sm">
                <div className="font-medium">{e.project_name}</div>
                <div className="text-xs text-sand-500">{fmtDate(e.created)}</div>
                <button className="mt-1 text-xs font-semibold text-brand-600 hover:underline"
                  onClick={() => api.post(`/api/exports/${e.id}/open`).catch((x) => toast(x.message, "error"))}>Open folder</button>
              </div>
            ))}
          </div>
          {exports.length > 0 && <Link to="/exports" className="mt-2 inline-block text-sm text-brand-600 hover:underline">All exports →</Link>}
        </section>
      </div>
    </div>
  );
}
