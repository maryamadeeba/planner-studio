import React, { createContext, useContext, useEffect, useState } from "react";
import type { Meta } from "../api";

export const MetaContext = createContext<Meta | null>(null);
export const useMeta = () => useContext(MetaContext)!;

type ToastFn = (msg: string, kind?: "ok" | "error") => void;
export const ToastContext = createContext<ToastFn>(() => {});
export const useToast = () => useContext(ToastContext);

export function ToastHost({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<{ id: number; msg: string; kind: string }[]>([]);
  const push: ToastFn = (msg, kind = "ok") => {
    const id = Date.now() + Math.random();
    setItems((x) => [...x, { id, msg, kind }]);
    setTimeout(() => setItems((x) => x.filter((i) => i.id !== id)), kind === "error" ? 9000 : 3500);
  };
  return (
    <ToastContext.Provider value={push}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex max-w-md flex-col gap-2">
        {items.map((t) => (
          <div key={t.id} role="status"
            className={`rounded-lg px-4 py-3 text-sm shadow-lg ${t.kind === "error" ? "bg-rose-500 text-white" : "bg-ink text-white"}`}>
            {t.msg}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function Toggle({ checked, onChange, label, hint, disabled = false }: { checked: boolean; onChange: (v: boolean) => void; label: string; hint?: string; disabled?: boolean }) {
  return (
    <label className={`flex items-start gap-3 py-1.5 ${disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}>
      <input type="checkbox" className="peer sr-only" checked={checked} disabled={disabled} onChange={(e) => onChange(e.target.checked)} />
      <span className={`mt-0.5 inline-flex h-5 w-9 flex-none items-center rounded-full p-0.5 transition peer-focus-visible:ring-2 peer-focus-visible:ring-brand-500 ${checked ? "bg-brand-500" : "bg-sand-300"}`}>
        <span className={`h-4 w-4 rounded-full bg-white shadow transition ${checked ? "translate-x-4" : ""}`} />
      </span>
      <span className="text-sm">
        {label}
        {hint && <span className="block text-xs text-sand-500">{hint}</span>}
      </span>
    </label>
  );
}

export function Field({ label, children, hint }: { label: string; children: React.ReactNode; hint?: string }) {
  return (
    <div>
      <span className="label">{label}</span>
      {children}
      {hint && <p className="mt-1 text-xs text-sand-500">{hint}</p>}
    </div>
  );
}

export function Modal({ open, title, children, onClose }: { open: boolean; title: string; children: React.ReactNode; onClose: () => void }) {
  useEffect(() => {
    const h = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    if (open) window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30 p-4" onClick={onClose}>
      <div className="card w-full max-w-md p-6 shadow-xl" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <h3 className="section-title mb-3">{title}</h3>
        {children}
      </div>
    </div>
  );
}

export function useConfirm() {
  const [state, setState] = useState<{ msg: string; resolve: (v: boolean) => void } | null>(null);
  const confirm = (msg: string) => new Promise<boolean>((resolve) => setState({ msg, resolve }));
  const dialog = (
    <Modal open={!!state} title="Are you sure?" onClose={() => { state?.resolve(false); setState(null); }}>
      <p className="mb-5 text-sm text-sand-500">{state?.msg}</p>
      <div className="flex justify-end gap-2">
        <button className="btn-ghost" onClick={() => { state?.resolve(false); setState(null); }}>Cancel</button>
        <button className="btn bg-rose-500 text-white hover:opacity-90" onClick={() => { state?.resolve(true); setState(null); }}>Delete</button>
      </div>
    </Modal>
  );
  return { confirm, dialog };
}

export function ErrorBox({ error }: { error: string | null }) {
  if (!error) return null;
  return <div className="rounded-lg border border-rose-500/30 bg-rose-50 px-4 py-3 text-sm text-rose-500" role="alert">{error}</div>;
}

export function PageHeader({ title, sub, children }: { title: string; sub?: string; children?: React.ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="font-display text-3xl font-semibold">{title}</h1>
        {sub && <p className="mt-1 text-sm text-sand-500">{sub}</p>}
      </div>
      <div className="flex flex-wrap gap-2">{children}</div>
    </div>
  );
}

export const Icon = {
  dash: "M3 12l9-8 9 8M5 10v10h5v-6h4v6h5V10",
  plus: "M12 5v14M5 12h14",
  lib: "M4 5h6v14H4zM14 5h6v6h-6zM14 15h6v4h-6z",
  dua: "M12 3c4 3 6 6 6 9a6 6 0 0 1-12 0c0-3 2-6 6-9z",
  quote: "M7 7h4v4c0 3-1.5 5-4 6M15 7h4v4c0 3-1.5 5-4 6",
  help: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.6v.6M12 17h.01",
  gear: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-2.7 1.1V21a2 2 0 1 1-4 0v-.1a1.6 1.6 0 0 0-2.7-1.1l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1A1.6 1.6 0 0 0 3.6 15H3a2 2 0 1 1 0-4h.1a1.6 1.6 0 0 0 1.1-2.7l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1A1.6 1.6 0 0 0 9.7 4.4V4a2 2 0 1 1 4 0v.1a1.6 1.6 0 0 0 2.7 1.1l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0 1.1 2.7H21a2 2 0 1 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1z",
  hist: "M3 12a9 9 0 1 0 3-6.7L3 8M3 3v5h5M12 7v5l3 3",
  folder: "M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z",
  download: "M12 4v12m0 0l-5-5m5 5l5-5M4 20h16",
  copy: "M8 8h12v12H8zM4 16V4h12",
  trash: "M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3",
  zoomIn: "M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zM21 21l-5-5M11 8v6M8 11h6",
  zoomOut: "M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zM21 21l-5-5M8 11h6",
  left: "M15 5l-7 7 7 7",
  right: "M9 5l7 7-7 7",
};

/** Productivity Shop by M bow mark (fallback when no logo PNG is uploaded). */
export function Bow({ className = "h-8 w-auto" }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 44" className={className} aria-hidden="true">
      <g fill="#93E2F0" stroke="#2A93B3" strokeWidth={1.8} strokeLinejoin="round">
        <path d="M30 23 L21 41 L27 38 L30 43 L33 25 Z" /><path d="M34 23 L43 41 L37 38 L34 43 L31 25 Z" />
        <path d="M32 20 C24 5 5 3 5 15 C5 27 22 27 32 20 Z" /><path d="M32 20 C40 5 59 3 59 15 C59 27 42 27 32 20 Z" />
        <ellipse cx="32" cy="20" rx="5" ry="5.6" />
      </g>
    </svg>
  );
}

/** The shop logo from Settings, or the bow.  Re-loads when Settings fires "shop-logo-changed". */
export function ShopLogo({ className = "h-10 w-auto" }: { className?: string }) {
  const [v, setV] = useState(0);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    const h = () => { setFailed(false); setV((x) => x + 1); };
    window.addEventListener("shop-logo-changed", h);
    return () => window.removeEventListener("shop-logo-changed", h);
  }, []);
  if (failed) return <Bow className={className} />;
  return <img src={`/api/settings/logo?v=${v}`} alt="" className={`${className} object-contain`} onError={() => setFailed(true)} />;
}

export function Svg({ d, className = "h-4 w-4" }: { d: string; className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      <path d={d} />
    </svg>
  );
}
