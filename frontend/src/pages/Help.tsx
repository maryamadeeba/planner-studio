import { Link } from "react-router-dom";
import { PageHeader, useMeta } from "../components/ui";

const Section = ({ id, title, children }: { id: string; title: string; children: React.ReactNode }) => (
  <section id={id} className="card mb-4 scroll-mt-6 p-5">
    <h2 className="section-title mb-2">{title}</h2>
    <div className="space-y-2 text-sm leading-relaxed">{children}</div>
  </section>
);

const TOPICS = [
  ["templates", "Template styles"], ["periods", "Short periods"], ["undated", "Undated planners"], ["colours", "Colours & readability"],
  ["pictures", "Pictures"], ["quotes", "Quotes & affirmations"], ["export", "Exporting & checks"],
];

export default function Help() {
  const meta = useMeta();
  return (
    <div className="mx-auto max-w-3xl p-8">
      <PageHeader title="Help" sub="How the main features work. The README in the planner-studio folder has the full guide." />
      <nav className="mb-5 flex flex-wrap gap-1.5">{TOPICS.map(([id, l]) => <a key={id} href={`#${id}`} className="chip py-1 text-xs">{l}</a>)}</nav>

      <Section id="templates" title="Template styles">
        <p>Pick a template in <b>step 1</b> (or when you create a new planner). It sets the colours, fonts, card style, cover layout and decorations of every page:</p>
        <ul className="list-disc space-y-1 pl-5">
          {meta.featured_templates.map((k) => <li key={k}><b>{meta.themes[k].label}</b> – {meta.themes[k].description}</li>)}
        </ul>
        <p>Your custom colours, pictures and quotes are applied on top of any template, so you can switch templates without losing them. “Show more colour styles” lists the older presets (minimal, pastel, Islamic geometric, colourful).</p>
        <p>Islamic pages (prayer trackers, duas with Arabic, Ramadan, Quran) and the Hijri calendar work in every template; Arabic always uses the Amiri font, right-to-left.</p>
      </Section>

      <Section id="periods" title="Short periods: month, quarter, week or custom">
        <p>In <b>step 2 → Period</b> choose Full year, Single month, Quarter, Single week or a Custom date range (up to a year).</p>
        <p>Short planners never include year-level pages. The cover becomes a <b>start page</b> with links to every section, and the side tabs only show pages that exist (e.g. Nov · Goals · W1–W5 · Notes).</p>
        <p>A single month always has the month calendar and a goals & notes page; add weekly pages, daily pages, a habit tracker, a monthly review or notes in step 5. The <b>Compact monthly set</b> planner type is just three pages.</p>
      </Section>

      <Section id="undated" title="Undated planners">
        <p>In step 2 choose <b>Undated</b>. Pages get blank “Month: ____”, “Week of: ____” and “Date: ____” fields with weekday headings only, so one file can be reused every year. Each undated month has five “Week of” spreads with seven daily pages each.</p>
        <p>The toggle is hidden for planner types without dates (Manifestation, Dua, Quran).</p>
      </Section>

      <Section id="colours" title="Colours & readability">
        <p>In <b>step 4</b> set a background, heading, body-text and accent colour for all pages, then optionally override them for the cover, monthly, weekly, daily, habit-tracker or notes pages. The swatches are your template's and brand colours; the preview updates as you pick.</p>
        <p>The <b>readability check</b> warns when text is hard to read (WCAG contrast below {meta.contrast.text}:1, or {meta.contrast.accent}:1 for the accent used on bands and icons) and offers <b>Auto-fix</b>, which darkens or lightens the colour just enough. Exports repeat the warning.</p>
      </Section>

      <Section id="pictures" title="Pictures">
        <p>In <b>step 6 → Pictures</b> upload PNG or JPG pictures for the cover (framed or full-bleed), section divider pages and a small header picture on monthly pages. Each has placement, fit, opacity and shape (rounded, circle or square).</p>
        <p>Pictures are rotated upright, resized and compressed automatically, so PDFs stay well under Etsy's 20 MB limit.</p>
      </Section>

      <Section id="quotes" title="Quotes & affirmations">
        <p>The <Link to="/quotes" className="text-brand-600 hover:underline">Quotes Library</Link> has 70+ starter quotes and affirmations (goals, focus, habits, hope and faith-friendly). Add your own, edit or delete them. Only use quotes you wrote or that are in the public domain.</p>
        <p>In <b>step 6</b> choose no quotes, one per page type, or a different quote on every page, and where they show (cover, monthly, weekly, daily footer, dividers).</p>
      </Section>

      <Section id="export" title="Exporting & automatic checks">
        <p>Every export checks that each hyperlink lands on the right page, that no text is cut off, and that colours are readable. Problems are listed in the results. Listing images use your template and include a <b>“compare all templates”</b> image.</p>
      </Section>
    </div>
  );
}
