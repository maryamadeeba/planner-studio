import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, fmtBytes, fmtDate } from "../api";
import { Icon, PageHeader, Svg, useConfirm, useToast } from "../components/ui";

export default function Exports() {
  const toast = useToast();
  const { confirm, dialog } = useConfirm();
  const [items, setItems] = useState<any[]>([]);
  const load = () => api.get("/api/exports").then(setItems);
  useEffect(() => { load(); }, []);
  return (
    <div className="mx-auto max-w-5xl p-8">
      {dialog}
      <PageHeader title="Export History" sub="Every export with its settings. Files stay in your export folder." />
      {items.length === 0 && <div className="card p-8 text-center text-sm text-sand-500">No exports yet.</div>}
      <div className="space-y-3">
        {items.map((e) => (
          <div key={e.id} className="card p-4">
            <div className="flex flex-wrap items-start gap-3">
              <div className="min-w-0 flex-1">
                <div className="font-semibold">{e.project_name} <span className="font-normal text-sand-500">· {fmtDate(e.created)}</span></div>
                <div className="text-xs text-sand-500">{e.summary}</div>
                <div className="mt-1 text-xs text-sand-500">
                  {(e.result?.files || []).map((f: any) => `${f.name} (${fmtBytes(f.bytes)})`).join(" · ")}
                </div>
                {e.warnings?.length > 0 && <div className="mt-1 text-xs text-amber-700">⚠ {e.warnings.length} warning(s): {e.warnings[0]}</div>}
                {!e.exists && <div className="mt-1 text-xs text-rose-500">Folder no longer exists.</div>}
              </div>
              <div className="flex gap-2">
                {e.project_id && <Link className="btn-ghost" to={`/project/${e.project_id}/8`}>Project</Link>}
                <button className="btn-ghost" disabled={!e.exists} onClick={() => api.post(`/api/exports/${e.id}/open`).catch((x) => toast(x.message, "error"))}><Svg d={Icon.folder} /> Open folder</button>
                {e.exists && e.result?.zip && <a className="btn-ghost" href={`/api/exports/${e.id}/file?path=${encodeURIComponent(e.result.zip)}`}><Svg d={Icon.download} /> Zip</a>}
                <button className="btn-danger px-2" aria-label="Remove from history" onClick={async () => {
                  if (await confirm("Remove this entry from the history? The files in the export folder are NOT deleted.")) { await api.del(`/api/exports/${e.id}`); load(); }
                }}><Svg d={Icon.trash} /></button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
