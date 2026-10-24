import { useEffect, useRef, useState } from "react";
import { api, fmtBytes, type Config } from "../api";
import { ErrorBox, Field, Icon, Svg, useMeta, useToast } from "../components/ui";

export default function StepExport({ cfg, set, projectId, saveNow }: {
  cfg: Config; set: (p: string, v: unknown) => void; projectId: number; saveNow: () => Promise<void>;
}) {
  const meta = useMeta();
  const toast = useToast();
  const [est, setEst] = useState<any>(null);
  const [estErr, setEstErr] = useState<string | null>(null);
  const [duas, setDuas] = useState<any[]>([]);
  const [job, setJob] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);
  const timer = useRef<number | null>(null);

  useEffect(() => {
    const t = setTimeout(() => {
      api.post("/api/estimate", { config: cfg }).then((e) => { setEst(e); setEstErr(null); }).catch((e) => setEstErr(e.message));
    }, 400);
    return () => clearTimeout(t);
  }, [JSON.stringify(cfg)]);
  useEffect(() => { api.get("/api/duas").then(setDuas); }, []);
  useEffect(() => () => { if (timer.current) clearInterval(timer.current); }, []);

  const included = cfg.modules.dua_list ? duas.filter((d) => !cfg.dua_ids?.length || cfg.dua_ids.includes(d.id)) : [];
  const unverified = included.filter((d) => !d.verified);

  const start = async () => {
    setErr(null);
    try {
      await saveNow();
      const { job_id } = await api.post(`/api/projects/${projectId}/export`);
      setJob({ status: "queued", progress: 0, stage: "Queued" });
      timer.current = window.setInterval(async () => {
        try {
          const j = await api.get(`/api/jobs/${job_id}`);
          setJob({ ...j, id: job_id });
          if (!["queued", "running"].includes(j.status)) {
            clearInterval(timer.current!);
            if (j.status === "done") toast("Export finished");
          }
        } catch (e: any) {
          clearInterval(timer.current!);
          setErr(e.message);
        }
      }, 1000);
    } catch (e: any) {
      setErr(e.message);
    }
  };
  const running = job && ["queued", "running"].includes(job.status);
  const r = job?.result;
  const L = cfg.listing;

  return (
    <>
      <section className="card mb-4 p-5">
        <h3 className="font-semibold">What will be exported</h3>
        <ErrorBox error={estErr} />
        {est && (
          <table className="mt-3 w-full text-sm">
            <thead><tr className="text-left text-xs uppercase tracking-wide text-sand-500"><th className="py-1">File</th><th>Pages</th><th className="text-right">Est. size</th></tr></thead>
            <tbody>
              {est.files.map((f: any, i: number) => (
                <tr key={i} className="border-t border-sand-100">
                  <td className="py-1.5">{meta.sizes[f.size]?.label.split(" (")[0]} · {f.variant}{f.part ? ` · ${f.part}` : ""}</td>
                  <td>{f.pages}</td>
                  <td className={`text-right ${f.over_limit ? "font-semibold text-rose-500" : ""}`}>~{fmtBytes(f.bytes)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {est?.any_over && (
          <div className="mt-3 rounded-lg bg-rose-50 p-3 text-sm text-rose-500" role="alert">
            At least one file may be over Etsy's 20 MB limit.
            <div className="mt-2 flex flex-wrap gap-2">
              {!cfg.output.compress_images && <button className="btn-ghost" onClick={() => set("output.compress_images", true)}>Compress images</button>}
              <button className="btn-ghost" onClick={() => set("output.split", "year")}>Split per year</button>
              <button className="btn-ghost" onClick={() => set("output.split", "half")}>Split per half-year</button>
            </div>
          </div>
        )}
        {unverified.length > 0 && (
          <div className="mt-3 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800" role="alert">
            <b>{unverified.length} unverified dua(s)</b> are included: {unverified.map((d) => d.title).join(", ")}. Paste verified Arabic text in the Dua Library and tick “verified” before selling.
          </div>
        )}
      </section>

      {cfg.output.listing_images && (
        <section className="card mb-4 p-5">
          <h3 className="mb-3 font-semibold">Listing image text</h3>
          <div className="grid gap-3">
            <Field label="Headline" hint="Empty = “<year> <planner title>”"><input className="input" value={L.headline} onChange={(e) => set("listing.headline", e.target.value)} /></Field>
            <div className="grid grid-cols-2 gap-3">
              {[["subheadline", "Small heading"], ["inside_title", "“What's inside” title"], ["sizes_title", "Sizes title"], ["colors_title", "Colours title"], ["links_title", "Hyperlink title"], ["shop_line", "Shop line"]].map(([k, l]) => (
                <Field key={k} label={l}><input className="input" value={L[k]} onChange={(e) => set(`listing.${k}`, e.target.value)} /></Field>
              ))}
            </div>
            <Field label="Hyperlink description"><input className="input" value={L.links_text} onChange={(e) => set("listing.links_text", e.target.value)} /></Field>
          </div>
        </section>
      )}

      <section className="card mb-4 p-5">
        <div className="flex items-center justify-between gap-3">
          <h3 className="font-semibold">Export</h3>
          {!running && <button className="btn-primary" onClick={start} disabled={!cfg.output.sizes.length || !cfg.output.variants.length}><Svg d={Icon.download} /> Export now</button>}
          {running && <button className="btn-danger" onClick={() => api.post(`/api/jobs/${job.id}/cancel`)}>Cancel</button>}
        </div>
        <ErrorBox error={err} />
        {job && (
          <div className="mt-4">
            <div className="h-3 overflow-hidden rounded-full bg-sand-200" role="progressbar" aria-valuenow={Math.round(job.progress * 100)} aria-valuemin={0} aria-valuemax={100}>
              <div className={`h-full transition-all ${job.status === "error" ? "bg-rose-500" : "bg-brand-500"}`} style={{ width: `${Math.round((job.progress || 0) * 100)}%` }} />
            </div>
            <div className="mt-1 flex justify-between text-xs text-sand-500"><span>{job.stage}</span><span>{Math.round((job.progress || 0) * 100)}%</span></div>
            {job.status === "error" && <div className="mt-3"><ErrorBox error={job.message} /></div>}
            {job.status === "cancelled" && <p className="mt-2 text-sm text-sand-500">{job.message}</p>}
          </div>
        )}
        {r && (
          <div className="mt-4 space-y-3">
            <table className="w-full text-sm">
              <tbody>
                {r.files.map((f: any) => (
                  <tr key={f.name} className="border-t border-sand-100">
                    <td className="py-1.5 pr-2">{f.name}</td>
                    <td className="text-xs text-sand-500">{f.pages} p.{f.verify ? ` · ${f.verify.resolved}/${f.verify.links} links ✓` : ""}</td>
                    <td className={`text-right ${f.over_limit ? "font-semibold text-rose-500" : ""}`}>{fmtBytes(f.bytes)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {r.arabic && <p className="text-xs text-sand-500">Arabic check: font {r.arabic.embedded ? "embedded ✓" : "NOT embedded ✗"} – see arabic-check.png in the export folder.</p>}
            {r.listing?.length > 0 && <p className="text-xs text-sand-500">{r.listing.length} listing images · {r.guide ? "buyer guide ✓" : ""}</p>}
            {r.warnings?.length > 0 && (
              <ul className="list-disc space-y-1 rounded-lg bg-amber-50 p-3 pl-6 text-sm text-amber-800">{r.warnings.map((w: string, i: number) => <li key={i}>{w}</li>)}</ul>
            )}
            <div className="flex flex-wrap gap-2">
              <button className="btn-primary" onClick={() => api.post(`/api/exports/${r.record_id}/open`).catch((e) => toast(e.message, "error"))}><Svg d={Icon.folder} /> Open export folder</button>
              <a className="btn-ghost" href={`/api/exports/${r.record_id}/file?path=${encodeURIComponent(r.zip)}`}><Svg d={Icon.download} /> Download bundle zip</a>
            </div>
            <p className="break-all text-xs text-sand-500">{r.folder}</p>
          </div>
        )}
      </section>
    </>
  );
}
