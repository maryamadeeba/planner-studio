// Tiny API client for the FastAPI backend (same origin).
export type Config = any; // project configuration (see backend/app/services/catalog.py DEFAULT_CONFIG)

export interface Meta {
  modules: Record<string, { group: string; label: string; calendar?: boolean; sections: { key: string; label: string }[] }>;
  planner_types: Record<string, { label: string; group: string; modules: string[]; period?: string }>;
  period_rules: Record<string, { label: string; on: string[]; off: string[] }>;
  undated_modules: string[];
  brand: Record<string, string>;
  page_groups: string[];
  featured_templates: string[];
  contrast: { text: number; accent: number };
  quote_categories: string[];
  labels: Record<string, string>;
  sizes: Record<string, { label: string; w: number; h: number }>;
  themes: Record<string, any>;
  fonts: { english: string[]; arabic: string[] };
  label_prefix: Record<string, string[]>;
  hijri: { min: [number, number]; max: [number, number]; months: string[] };
  etsy_limit: number;
  default_config: Config;
}

export interface Project { id: number; name: string; config: Config; created: string; updated: string }
export interface PageInfo { i: number; id: string; kind: string; title: string }

async function handle(r: Response) {
  if (!r.ok) {
    let msg = `${r.status} ${r.statusText}`;
    try {
      const j = await r.json();
      msg = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch { /* ignore */ }
    throw new Error(msg);
  }
  const ct = r.headers.get("content-type") || "";
  return ct.includes("application/json") ? r.json() : r.text();
}

export const api = {
  get: (url: string) => fetch(url).then(handle),
  post: (url: string, body?: unknown) =>
    fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body ?? {}) }).then(handle),
  put: (url: string, body?: unknown) =>
    fetch(url, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body ?? {}) }).then(handle),
  del: (url: string) => fetch(url, { method: "DELETE" }).then(handle),
  upload: (url: string, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return fetch(url, { method: "POST", body: fd }).then(handle);
  },
};

export function fmtBytes(b: number) {
  if (b > 1048576) return `${(b / 1048576).toFixed(1)} MB`;
  return `${Math.max(1, Math.round(b / 1024))} KB`;
}

export function fmtDate(iso: string) {
  try {
    return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
  } catch {
    return iso;
  }
}

export function setIn(obj: any, path: string, value: unknown) {
  const copy = structuredClone(obj);
  // "\u0000" stands for a literal dot inside a key (label keys such as "week.title")
  const keys = path.split(".").map((k) => k.replace(/\u0000/g, "."));
  let cur = copy;
  for (const k of keys.slice(0, -1)) {
    if (cur[k] === undefined || cur[k] === null) cur[k] = {};
    cur = cur[k];
  }
  cur[keys[keys.length - 1]] = value;
  return copy;
}

export const GREG_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
