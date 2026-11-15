import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  TicketIcon,
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
  Loader2,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { getDashboardStats, getRecentTickets } from "../services/api";
import Stats from "./Stats";

/* ── Colour maps ──────────────────────────────────────────────────── */
const PRIORITY_COLORS = {
  critical: "#ef4444",
  high: "#f97316",
  medium: "#eab308",
  low: "#22c55e",
};

const STATUS_STYLES = {
  new: "bg-blue-500/15 text-blue-400",
  processing: "bg-purple-500/15 text-purple-400",
  assigned: "bg-indigo-500/15 text-indigo-400",
  in_progress: "bg-yellow-500/15 text-yellow-400",
  pending_approval: "bg-amber-500/15 text-amber-400",
  resolved: "bg-emerald-500/15 text-emerald-400",
  closed: "bg-slate-500/15 text-slate-400",
};

const PRIORITY_STYLES = {
  critical: "bg-red-500/15 text-red-400",
  high: "bg-orange-500/15 text-orange-400",
  medium: "bg-yellow-500/15 text-yellow-400",
  low: "bg-green-500/15 text-green-400",
};

const CATEGORY_COLORS = [
  "#6366f1",
  "#8b5cf6",
  "#06b6d4",
  "#14b8a6",
  "#f59e0b",
  "#ef4444",
];

/* ── Custom tooltip for recharts ──────────────────────────────────── */
const ChartTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs shadow-xl">
      <p className="font-medium text-slate-300">{label ?? payload[0].name}</p>
      <p className="text-white">{payload[0].value} tickets</p>
    </div>
  );
};

/**
 * Main dashboard view — stat cards, charts, and a recent-tickets table.
 * Auto-refreshes every 30 seconds.
 */
export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [s, r] = await Promise.all([
        getDashboardStats(),
        getRecentTickets(),
      ]);
      setStats(s);
      setRecent(Array.isArray(r) ? r : r?.tickets ?? []);
    } catch (err) {
      console.error("Dashboard fetch failed:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const id = setInterval(fetchData, 30_000);
    return () => clearInterval(id);
  }, [fetchData]);

  /* ── Loading state ──────────────────────────────────────────────── */
  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-400" />
      </div>
    );
  }

  /* ── Derived data ───────────────────────────────────────────────── */
  const criticalHigh =
    (stats?.by_priority?.critical ?? 0) + (stats?.by_priority?.high ?? 0);

  const categoryData = Object.entries(stats?.by_category ?? {}).map(
    ([name, value]) => ({ name, value })
  );

  const priorityData = Object.entries(stats?.by_priority ?? {}).map(
    ([name, value]) => ({ name, value })
  );

  const resolvedToday =
    stats?.by_status?.resolved ?? 0;

  return (
    <div className="mx-auto max-w-7xl space-y-8">
      {/* ── Header ─────────────────────────────────────────────── */}
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="mt-1 text-sm text-slate-400">
          Real-time overview of your AI-powered ticket pipeline.
        </p>
      </div>

      {/* ── Stat cards ─────────────────────────────────────────── */}
      <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
        <Stats
          title="Total Tickets"
          value={stats?.total_tickets ?? 0}
          icon={TicketIcon}
          color="bg-indigo-500/15"
          iconColor="text-indigo-400"
          subtitle="All time"
        />
        <Stats
          title="Critical / High"
          value={criticalHigh}
          icon={AlertTriangle}
          color="bg-red-500/15"
          iconColor="text-red-400"
          subtitle="Need attention"
        />
        <Stats
          title="Avg AI Confidence"
          value={`${Math.round((stats?.avg_confidence ?? 0) * 100)}%`}
          icon={BrainCircuit}
          color="bg-purple-500/15"
          iconColor="text-purple-400"
          subtitle="Model accuracy"
        />
        <Stats
          title="Resolved"
          value={resolvedToday}
          icon={CheckCircle2}
          color="bg-emerald-500/15"
          iconColor="text-emerald-400"
          subtitle="Resolved tickets"
        />
      </div>

      {/* ── Charts row ─────────────────────────────────────────── */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Bar chart – tickets by category */}
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/60 p-5 shadow-lg">
          <h2 className="mb-4 text-sm font-semibold text-slate-300">
            Tickets by Category
          </h2>
          {categoryData.length === 0 ? (
            <p className="py-12 text-center text-sm text-slate-500">
              No data yet
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={categoryData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="name"
                  tick={{ fill: "#94a3b8", fontSize: 12 }}
                  axisLine={{ stroke: "#475569" }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: "#94a3b8", fontSize: 12 }}
                  axisLine={false}
                  tickLine={false}
                  allowDecimals={false}
                />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                  {categoryData.map((_, i) => (
                    <Cell
                      key={i}
                      fill={CATEGORY_COLORS[i % CATEGORY_COLORS.length]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Pie chart – tickets by priority */}
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/60 p-5 shadow-lg">
          <h2 className="mb-4 text-sm font-semibold text-slate-300">
            Tickets by Priority
          </h2>
          {priorityData.length === 0 ? (
            <p className="py-12 text-center text-sm text-slate-500">
              No data yet
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={priorityData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={4}
                  stroke="none"
                  label={({ name, percent }) =>
                    `${name} ${(percent * 100).toFixed(0)}%`
                  }
                >
                  {priorityData.map((entry) => (
                    <Cell
                      key={entry.name}
                      fill={PRIORITY_COLORS[entry.name] ?? "#6366f1"}
                    />
                  ))}
                </Pie>
                <Tooltip content={<ChartTooltip />} />
                <Legend
                  wrapperStyle={{ fontSize: 12, color: "#94a3b8" }}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* ── Recent tickets table ───────────────────────────────── */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-800/60 shadow-lg">
        <div className="border-b border-slate-700/50 px-5 py-4">
          <h2 className="text-sm font-semibold text-slate-300">
            Recent Tickets
          </h2>
        </div>

        {recent.length === 0 ? (
          <p className="py-12 text-center text-sm text-slate-500">
            No tickets yet — submit one to get started!
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-700/40 text-xs uppercase text-slate-500">
                  <th className="px-5 py-3">ID</th>
                  <th className="px-5 py-3">Subject</th>
                  <th className="px-5 py-3">Category</th>
                  <th className="px-5 py-3">Priority</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Created</th>
                </tr>
              </thead>
              <tbody>
                {recent.slice(0, 10).map((t) => (
                  <tr
                    key={t.id}
                    className="border-b border-slate-700/20 transition-colors hover:bg-slate-700/20"
                  >
                    <td className="px-5 py-3 font-mono text-slate-400">
                      #{t.id}
                    </td>
                    <td className="max-w-xs truncate px-5 py-3">
                      <Link
                        to={`/tickets/${t.id}`}
                        className="text-indigo-400 hover:text-indigo-300 hover:underline"
                      >
                        {t.subject}
                      </Link>
                    </td>
                    <td className="px-5 py-3 capitalize text-slate-300">
                      {t.category?.replace("_", " ")}
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ${
                          PRIORITY_STYLES[t.priority] ?? ""
                        }`}
                      >
                        {t.priority}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ${
                          STATUS_STYLES[t.status] ?? ""
                        }`}
                      >
                        {t.status?.replace("_", " ")}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-5 py-3 text-slate-500">
                      {new Date(t.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
