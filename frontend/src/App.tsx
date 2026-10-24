import { useEffect, useState } from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import { api, type Meta } from "./api";
import { Icon, MetaContext, ShopLogo, Svg, ToastHost } from "./components/ui";
import Dashboard from "./pages/Dashboard";
import NewPlanner from "./pages/NewPlanner";
import Editor from "./pages/Editor";
import Templates from "./pages/Templates";
import Duas from "./pages/Duas";
import Quotes from "./pages/Quotes";
import Help from "./pages/Help";
import Settings from "./pages/Settings";
import Exports from "./pages/Exports";

const NAV = [
  { to: "/", label: "Dashboard", icon: Icon.dash, end: true },
  { to: "/new", label: "New Planner", icon: Icon.plus },
  { to: "/templates", label: "Template Library", icon: Icon.lib },
  { to: "/duas", label: "Dua Library", icon: Icon.dua },
  { to: "/quotes", label: "Quotes Library", icon: Icon.quote },
  { to: "/settings", label: "Settings", icon: Icon.gear },
  { to: "/exports", label: "Export History", icon: Icon.hist },
  { to: "/help", label: "Help", icon: Icon.help },
];

export default function App() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => {
    api.get("/api/meta").then(setMeta).catch((e) => setErr(String(e.message || e)));
  }, []);

  return (
    <ToastHost>
      <div className="flex h-screen overflow-hidden">
        <aside className="flex w-60 flex-none flex-col border-r border-sand-200 bg-white">
          <div className="px-5 pb-5 pt-6">
            <ShopLogo className="mb-3 h-11 w-auto max-w-[9rem]" />
            <div className="font-display text-xl font-semibold leading-tight text-ink">Maryam's<br />Planner Studio</div>
            <div className="mt-1 font-hand text-lg leading-tight text-sky-deep">for Productivity Shop by M</div>
          </div>
          <nav className="flex flex-col gap-0.5 px-3">
            {NAV.map((n) => (
              <NavLink key={n.to} to={n.to} end={n.end}
                className={({ isActive }) => `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition ${isActive ? "bg-brand-50 font-semibold text-brand-700" : "text-ink hover:bg-sand-100"}`}>
                <Svg d={n.icon} className="h-[18px] w-[18px]" />
                {n.label}
              </NavLink>
            ))}
          </nav>
          <div className="mt-auto px-5 py-4 text-[11px] leading-relaxed text-sand-500">
            Runs locally on this PC.<br />Your files never leave your computer.
          </div>
        </aside>
        <main className="min-w-0 flex-1 overflow-auto">
          {err && (
            <div className="m-8 rounded-lg border border-rose-500/30 bg-rose-50 p-4 text-sm text-rose-500">
              Could not reach the Planner Studio server: {err}. Make sure the black start.bat window is still open.
            </div>
          )}
          {meta && (
            <MetaContext.Provider value={meta}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/new" element={<NewPlanner />} />
                <Route path="/project/:id/:step?" element={<Editor />} />
                <Route path="/templates" element={<Templates />} />
                <Route path="/duas" element={<Duas />} />
                <Route path="/quotes" element={<Quotes />} />
                <Route path="/help" element={<Help />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/exports" element={<Exports />} />
              </Routes>
            </MetaContext.Provider>
          )}
          {!meta && !err && <div className="p-10 text-sm text-sand-500">Loading…</div>}
        </main>
      </div>
    </ToastHost>
  );
}
