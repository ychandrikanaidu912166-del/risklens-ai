import { NavLink } from "react-router-dom";
import clsx from "clsx";
import { Activity, LayoutDashboard, ListChecks, ScanLine, ShieldCheck } from "lucide-react";

const NAV = [
  { to: "/", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/investigations", label: "Investigations", icon: ListChecks },
  { to: "/model-monitoring", label: "Model Monitoring", icon: Activity },
  { to: "/audit", label: "Audit Trail", icon: ScanLine },
];

export function Sidebar() {
  return (
    <aside className="hidden w-56 shrink-0 flex-col border-r border-ink-800 bg-ink-950/70 lg:flex">
      <div className="flex items-center gap-2 px-4 py-4">
        <div className="rounded-md bg-brand-600/20 p-1.5 text-brand-500 ring-1 ring-inset ring-brand-500/40">
          <ShieldCheck className="h-4 w-4" />
        </div>
        <div>
          <div className="text-sm font-semibold tracking-tight text-ink-100">RiskLens AI</div>
          <div className="text-2xs text-ink-400">Payment Risk Intelligence</div>
        </div>
      </div>
      <nav className="flex-1 space-y-0.5 px-2 pt-2">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-ink-800 text-ink-100"
                  : "text-ink-300 hover:bg-ink-800/70 hover:text-ink-100",
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="px-3 pb-4 text-2xs text-ink-500">
        Synthetic data · v0.2.0
      </div>
    </aside>
  );
}
