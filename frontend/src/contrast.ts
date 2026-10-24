// WCAG 2.x contrast helpers – mirror backend/app/services/themes.py (luminance, contrast, fix_contrast).
import type { Config, Meta } from "./api";

export const ROLES = [
  { key: "background", theme: "background", label: "Background" },
  { key: "heading", theme: "primary", label: "Headings" },
  { key: "body", theme: "ink", label: "Body text" },
  { key: "accent", theme: "accent", label: "Accent" },
] as const;

export const PAGE_GROUP_LABELS: Record<string, string> = {
  cover: "Cover & dividers", month: "Monthly pages", week: "Weekly pages", day: "Daily pages", habits: "Habit tracker", notes: "Notes",
};

const isHex = (v: unknown): v is string => typeof v === "string" && /^#[0-9a-fA-F]{6}$/.test(v);

export function luminance(hex: string) {
  const ch = (c: number) => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
  return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b);
}

export function contrast(fg: string, bg: string) {
  const [a, b] = [luminance(fg), luminance(bg)].sort((x, y) => y - x);
  return Math.round(((a + 0.05) / (b + 0.05)) * 100) / 100;
}

function mix(a: string, b: string, t: number) {
  const pa = [1, 3, 5].map((i) => parseInt(a.slice(i, i + 2), 16));
  const pb = [1, 3, 5].map((i) => parseInt(b.slice(i, i + 2), 16));
  return "#" + pa.map((x, i) => Math.round(x + (pb[i] - x) * t).toString(16).padStart(2, "0")).join("").toUpperCase();
}

/** Darken (light background) or lighten (dark background) just enough to reach `min`. */
export function fixContrast(fg: string, bg: string, min: number) {
  if (contrast(fg, bg) >= min) return fg.toUpperCase();
  const target = luminance(bg) > 0.18 ? "#000000" : "#FFFFFF";
  for (let s = 1; s <= 50; s++) {
    const c = mix(fg, target, s / 50);
    if (contrast(c, bg) >= min) return c;
  }
  return target;
}

/** The colours a page type actually uses: page override → project override → theme preset. */
export function effectiveColors(cfg: Config, meta: Meta, group?: string): Record<string, string> {
  const t = cfg.theme;
  const preset = meta.themes[t.preset] || meta.themes[meta.featured_templates[0]];
  const over = (group && t.pages?.[group]) || {};
  const out: Record<string, string> = {};
  for (const r of ROLES) {
    const g = t[r.theme];
    out[r.key] = isHex(over[r.key]) ? over[r.key] : isHex(g) ? g : preset[r.theme];
  }
  return out;
}

export interface ContrastIssue { group: string | null; role: string; color: string; background: string; ratio: number; min: number; fix: string }

export function contrastIssues(cfg: Config, meta: Meta): ContrastIssue[] {
  const out: ContrastIssue[] = [];
  const groups: (string | null)[] = [null, ...meta.page_groups.filter((g) => Object.values(cfg.theme.pages?.[g] || {}).some(isHex))];
  for (const group of groups) {
    const c = effectiveColors(cfg, meta, group ?? undefined);
    // a template can mark its accent as purely decorative (e.g. Ink & Gold's gold rules) – then only text is checked
    const decorative = meta.themes[cfg.theme.preset]?.accent_role === "decorative";
    for (const role of decorative ? ["heading", "body"] : ["heading", "body", "accent"]) {
      const min = role === "accent" ? meta.contrast.accent : meta.contrast.text;
      const ratio = contrast(c[role], c.background);
      if (ratio < min) out.push({ group, role, color: c[role], background: c.background, ratio, min, fix: fixContrast(c[role], c.background, min) });
    }
  }
  return out;
}

export { isHex };
