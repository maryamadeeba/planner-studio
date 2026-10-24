import { useMeta } from "../components/ui";

export const TYPE_INFO: Record<string, string> = {
  yearly: "Year at a glance, monthly calendars and notes.",
  quarterly: "Quarter plans, goals and quarter reviews.",
  monthly: "Month grids, monthly goals and habit trackers.",
  weekly: "Weekly spreads – vertical, horizontal or boxed.",
  daily: "Everything: year, quarters, months, weeks and daily pages.",
  compact: "3 pages: start page, month calendar and a goals & notes page.",
  goal: "Vision, SMART goals, milestones, action steps and reviews.",
  manifestation: "Affirmations, vision board, gratitude, scripting, 369.",
  namaz: "Five daily prayers + Sunnah/Tahajjud/Witr, monthly & weekly.",
  dua: "Dua collection (Arabic + English), journal and answered log.",
  ramadan: "30-day fasting tracker, daily Ramadan pages, Eid prep, meals.",
  quran: "30-juz tracker, 114-surah checklist, khatam and reflections.",
};

export default function TypePicker({ value, onChange }: { value: string; onChange: (k: string) => void }) {
  const meta = useMeta();
  const groups = Object.entries(meta.planner_types).reduce<Record<string, [string, any][]>>((acc, [k, v]) => {
    (acc[v.group] ||= []).push([k, v]);
    return acc;
  }, {});
  return (
    <div className="space-y-6">
      {Object.entries(groups).map(([g, items]) => (
        <div key={g}>
          <div className="label mb-2">{g}</div>
          <div className="grid gap-3 sm:grid-cols-2">
            {items.map(([k, v]) => (
              <button key={k} type="button" onClick={() => onChange(k)} aria-pressed={value === k}
                className={`card p-4 text-left transition hover:border-brand-500 ${value === k ? "border-brand-500 ring-2 ring-brand-100" : ""}`}>
                <div className="font-semibold">{v.label}</div>
                <div className="mt-1 text-xs text-sand-500">{TYPE_INFO[k]}</div>
              </button>
            ))}
          </div>
        </div>
      ))}
      <p className="text-xs text-sand-500">Any planner can be personalised with a name in step 6. You can switch pages on or off in step 5.</p>
    </div>
  );
}
