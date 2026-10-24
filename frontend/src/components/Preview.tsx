import { useEffect, useMemo, useRef, useState } from "react";
import { api, type Config, type PageInfo } from "../api";
import { Icon, Svg, useMeta } from "./ui";

function useDebounced<T>(value: T, ms: number) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}

const thumbCache = new Map<string, string>();

function Thumb({ cfgJson, size, variant, i, w, h, width, active, label, onClick }: {
  cfgJson: string; size: string; variant: string; i: number; w: number; h: number; width: number; active: boolean; label: string; onClick: () => void;
}) {
  const ref = useRef<HTMLButtonElement>(null);
  const key = `${size}|${variant}|${i}|${cfgJson}`;
  const [html, setHtml] = useState<string | null>(thumbCache.get(key) ?? null);
  useEffect(() => {
    setHtml(thumbCache.get(key) ?? null);
    const el = ref.current;
    if (!el) return;
    let cancelled = false;
    const io = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && !thumbCache.has(key)) {
        api.post("/api/preview/html", { config: JSON.parse(cfgJson), size, variant, index: i })
          .then((t: string) => { if (thumbCache.size > 400) thumbCache.clear(); thumbCache.set(key, t); if (!cancelled) setHtml(t); })
          .catch(() => {});
        io.disconnect();
      }
    }, { rootMargin: "200px" });
    io.observe(el);
    return () => { cancelled = true; io.disconnect(); };
  }, [key]);
  const scale = width / w;
  return (
    <button ref={ref} onClick={onClick} title={label} aria-label={`Page ${i + 1}: ${label}`}
      className={`flex-none overflow-hidden rounded border bg-white transition ${active ? "border-brand-500 ring-2 ring-brand-500" : "border-sand-300 hover:border-sand-500"}`}
      style={{ width, height: h * scale }}>
      {html ? (
        <iframe title={`thumb ${i}`} srcDoc={html} tabIndex={-1}
          style={{ width: w, height: h, transform: `scale(${scale})`, transformOrigin: "0 0", pointerEvents: "none", border: 0 }} />
      ) : <span className="flex h-full items-center justify-center text-[10px] text-sand-400">{i + 1}</span>}
    </button>
  );
}

export default function Preview({ config, large = false }: { config: Config; large?: boolean }) {
  const meta = useMeta();
  const sizes: string[] = config.output?.sizes?.length ? config.output.sizes : ["A4"];
  const variants: string[] = config.output?.variants?.length ? config.output.variants : ["digital"];
  const [size, setSize] = useState(sizes[0]);
  const [variant, setVariant] = useState(variants[0]);
  const [index, setIndex] = useState(0);
  const [zoom, setZoom] = useState(1);
  const [pages, setPages] = useState<PageInfo[]>([]);
  const [html, setHtml] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  const [boxSize, setBoxSize] = useState({ w: 400, h: 600 });

  useEffect(() => { if (!sizes.includes(size)) setSize(sizes[0]); }, [sizes.join()]);
  useEffect(() => { if (!variants.includes(variant)) setVariant(variants[0]); }, [variants.join()]);

  // short debounce: colour pickers and toggles show in the preview almost immediately
  const cfgJson = useDebounced(JSON.stringify(config), 120);
  const thumbJson = useDebounced(cfgJson, 700);  // thumbnails refresh once you stop dragging
  const dims = meta.sizes[size] || meta.sizes.A4;

  useEffect(() => {
    api.post("/api/preview/pages", { config: JSON.parse(cfgJson) })
      .then((r) => { setPages(r.pages); setErr(null); setIndex((i) => Math.min(i, r.count - 1)); })
      .catch((e) => setErr(e.message));
  }, [cfgJson]);

  useEffect(() => {
    setLoading(true);
    api.post("/api/preview/html", { config: JSON.parse(cfgJson), size, variant, index })
      .then((t) => { setHtml(t); setErr(null); })
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  }, [cfgJson, size, variant, index]);

  useEffect(() => {
    const onMsg = (e: MessageEvent) => {
      const id = e.data?.plannerGoto;
      if (!id) return;
      const p = pages.find((x) => x.id === id);
      if (p) setIndex(p.i);
    };
    window.addEventListener("message", onMsg);
    return () => window.removeEventListener("message", onMsg);
  }, [pages]);

  useEffect(() => {
    if (!box.current) return;
    const ro = new ResizeObserver(([e]) => setBoxSize({ w: e.contentRect.width, h: e.contentRect.height }));
    ro.observe(box.current);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
      if (e.key === "ArrowRight") setIndex((i) => Math.min(i + 1, pages.length - 1));
      if (e.key === "ArrowLeft") setIndex((i) => Math.max(i - 1, 0));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [pages.length]);

  const fit = Math.min((boxSize.w - 24) / dims.w, (boxSize.h - 24) / dims.h);
  const scale = Math.max(0.1, fit * zoom);
  const thumbW = large ? 92 : 58;
  const current = pages[index];

  const options = useMemo(() => pages.map((p) => <option key={p.i} value={p.i}>{p.i + 1}. {p.title}</option>), [pages]);

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex flex-wrap items-center gap-2 border-b border-sand-200 px-3 py-2 text-sm">
        <select className="input w-auto py-1" value={size} onChange={(e) => setSize(e.target.value)} aria-label="Preview size">
          {sizes.map((s) => <option key={s} value={s}>{meta.sizes[s]?.label.split(" (")[0] ?? s}</option>)}
        </select>
        <div className="flex overflow-hidden rounded-lg border border-sand-300" role="group" aria-label="PDF variant">
          {variants.map((v) => (
            <button key={v} className={`px-2.5 py-1 text-xs font-medium ${variant === v ? "bg-brand-600 text-white" : "bg-white"}`} onClick={() => setVariant(v)}>
              {v === "digital" ? "Digital" : "Printable"}
            </button>
          ))}
        </div>
        <span className="ml-auto text-xs text-sand-500">{pages.length} pages</span>
        <button className="btn-ghost px-2 py-1" aria-label="Zoom out" onClick={() => setZoom((z) => Math.max(0.5, +(z - 0.25).toFixed(2)))}><Svg d={Icon.zoomOut} /></button>
        <span className="w-10 text-center text-xs">{Math.round(zoom * 100)}%</span>
        <button className="btn-ghost px-2 py-1" aria-label="Zoom in" onClick={() => setZoom((z) => Math.min(4, +(z + 0.25).toFixed(2)))}><Svg d={Icon.zoomIn} /></button>
      </div>
      <div className="flex items-center gap-2 px-3 py-2 text-sm">
        <button className="btn-ghost px-2 py-1" aria-label="Previous page" disabled={index <= 0} onClick={() => setIndex(index - 1)}><Svg d={Icon.left} /></button>
        <select className="input min-w-0 flex-1 py-1" value={index} onChange={(e) => setIndex(+e.target.value)} aria-label="Jump to page">{options}</select>
        <button className="btn-ghost px-2 py-1" aria-label="Next page" disabled={index >= pages.length - 1} onClick={() => setIndex(index + 1)}><Svg d={Icon.right} /></button>
      </div>
      <div ref={box} className="relative min-h-0 flex-1 overflow-auto bg-sand-200/60">
        {err && <div className="m-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-500" role="alert">{err}</div>}
        {!err && html && (
          <div className="mx-auto my-3 shadow-lg" style={{ width: dims.w * scale, height: dims.h * scale }}>
            <iframe title={current ? `Preview: ${current.title}` : "Preview"} srcDoc={html}
              style={{ width: dims.w, height: dims.h, transform: `scale(${scale})`, transformOrigin: "0 0", border: 0, background: "white" }} />
          </div>
        )}
        {loading && <div className="absolute right-3 top-3 rounded bg-white/90 px-2 py-1 text-xs text-sand-500">Updating…</div>}
      </div>
      {variant === "digital" && <p className="px-3 pt-1 text-[11px] text-sand-500">Tip: links work in the preview – click a tab or date to jump.</p>}
      <div className="flex gap-2 overflow-x-auto px-3 py-2" aria-label="Page thumbnails">
        {pages.map((p) => (
          <Thumb key={p.i} cfgJson={thumbJson} size={size} variant={variant} i={p.i} w={dims.w} h={dims.h} width={thumbW}
            active={p.i === index} label={p.title} onClick={() => setIndex(p.i)} />
        ))}
      </div>
    </div>
  );
}
