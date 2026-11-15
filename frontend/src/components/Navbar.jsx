import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Ticket,
  PlusCircle,
  Bot,
  Sparkles,
} from "lucide-react";

/** Navigation links rendered in the sidebar. */
const links = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/tickets", label: "All Tickets", icon: Ticket },
  { to: "/tickets/new", label: "Submit Ticket", icon: PlusCircle },
];

/**
 * Dark sidebar navigation component.
 * Fixed width (260 px), full viewport height, with app branding at top
 * and a "Powered by AI" badge at the bottom.
 */
export default function Navbar() {
  return (
    <aside className="flex w-[260px] shrink-0 flex-col border-r border-slate-700/60 bg-slate-950">
      {/* ── Brand / logo ───────────────────────────────────────── */}
      <div className="flex items-center gap-2.5 px-5 py-6">
        <Bot className="h-7 w-7 text-indigo-400" />
        <span className="text-lg font-bold tracking-tight text-white">
          AI Ticket<span className="text-indigo-400"> Auto</span>
        </span>
      </div>

      {/* ── Nav links ──────────────────────────────────────────── */}
      <nav className="mt-2 flex flex-1 flex-col gap-1 px-3">
        {links.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-indigo-600/20 text-indigo-300"
                  : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              }`
            }
          >
            <Icon className="h-[18px] w-[18px]" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* ── Footer badge ───────────────────────────────────────── */}
      <div className="border-t border-slate-800 px-5 py-4">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Sparkles className="h-3.5 w-3.5 text-indigo-500" />
          <span>Powered by AI</span>
        </div>
      </div>
    </aside>
  );
}
