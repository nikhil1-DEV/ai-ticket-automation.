import { useEffect, useState, useCallback } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  Search,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Inbox,
} from "lucide-react";
import { getTickets } from "../services/api";

/* ── Badge style maps ─────────────────────────────────────────────── */
const PRIORITY_STYLES = {
  critical: "bg-red-500/15 text-red-400",
  high: "bg-orange-500/15 text-orange-400",
  medium: "bg-yellow-500/15 text-yellow-400",
  low: "bg-green-500/15 text-green-400",
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

const CATEGORY_STYLES = {
  billing: "bg-cyan-500/15 text-cyan-400",
  technical: "bg-violet-500/15 text-violet-400",
  account: "bg-blue-500/15 text-blue-400",
  general: "bg-slate-500/15 text-slate-300",
  bug_report: "bg-red-500/15 text-red-400",
  feature_request: "bg-emerald-500/15 text-emerald-400",
};

/** Dropdown options */
const STATUSES = [
  "",
  "new",
  "processing",
  "assigned",
  "in_progress",
  "pending_approval",
  "resolved",
  "closed",
];
const CATEGORIES = [
  "",
  "billing",
  "technical",
  "account",
  "general",
  "bug_report",
  "feature_request",
];
const PRIORITIES = ["", "critical", "high", "medium", "low"];

/**
 * Paginated, filterable ticket list view.
 */
export default function TicketList() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(Number(searchParams.get("page")) || 1);
  const [hasMore, setHasMore] = useState(false);

  // Filters stored in URL search-params for shareability
  const status = searchParams.get("status") ?? "";
  const category = searchParams.get("category") ?? "";
  const priority = searchParams.get("priority") ?? "";
  const LIMIT = 15;

  const fetchTickets = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getTickets({
        status: status || undefined,
        category: category || undefined,
        priority: priority || undefined,
        page,
        limit: LIMIT,
      });
      // Backend may return an array or { tickets: [], total: N }
      const list = Array.isArray(data) ? data : data?.tickets ?? [];
      setTickets(list);
      setHasMore(list.length === LIMIT);
    } catch (err) {
      console.error("Failed to load tickets:", err);
    } finally {
      setLoading(false);
    }
  }, [status, category, priority, page]);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  /** Update a filter and reset to page 1. */
  const setFilter = (key, value) => {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    next.set("page", "1");
    setSearchParams(next);
    setPage(1);
  };

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Tickets</h1>
          <p className="mt-1 text-sm text-slate-400">
            Browse, filter, and manage support tickets.
          </p>
        </div>
        <Link
          to="/tickets/new"
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-lg transition-colors hover:bg-indigo-500"
        >
          + New Ticket
        </Link>
      </div>

      {/* ── Filters ────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-3">
        <Search className="h-4 w-4 text-slate-500" />

        <select
          value={status}
          onChange={(e) => setFilter("status", e.target.value)}
          className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-300 outline-none focus:border-indigo-500"
        >
          <option value="">All Statuses</option>
          {STATUSES.filter(Boolean).map((s) => (
            <option key={s} value={s}>
              {s.replace("_", " ")}
            </option>
          ))}
        </select>

        <select
          value={category}
          onChange={(e) => setFilter("category", e.target.value)}
          className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-300 outline-none focus:border-indigo-500"
        >
          <option value="">All Categories</option>
          {CATEGORIES.filter(Boolean).map((c) => (
            <option key={c} value={c}>
              {c.replace("_", " ")}
            </option>
          ))}
        </select>

        <select
          value={priority}
          onChange={(e) => setFilter("priority", e.target.value)}
          className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-300 outline-none focus:border-indigo-500"
        >
          <option value="">All Priorities</option>
          {PRIORITIES.filter(Boolean).map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </div>

      {/* ── Table ──────────────────────────────────────────────── */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-800/60 shadow-lg">
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <Loader2 className="h-7 w-7 animate-spin text-indigo-400" />
          </div>
        ) : tickets.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-slate-500">
            <Inbox className="mb-3 h-10 w-10" />
            <p className="text-sm">No tickets found</p>
          </div>
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
                  <th className="px-5 py-3">Team</th>
                  <th className="px-5 py-3">Created</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map((t) => (
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
                    <td className="px-5 py-3">
                      <span
                        className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ${
                          CATEGORY_STYLES[t.category] ?? ""
                        }`}
                      >
                        {t.category?.replace("_", " ")}
                      </span>
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
                    <td className="px-5 py-3 text-slate-300">
                      {t.assigned_team ?? "—"}
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

        {/* ── Pagination ───────────────────────────────────────── */}
        {!loading && tickets.length > 0 && (
          <div className="flex items-center justify-between border-t border-slate-700/40 px-5 py-3">
            <span className="text-xs text-slate-500">Page {page}</span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => {
                  const p = page - 1;
                  setPage(p);
                  setSearchParams((prev) => {
                    prev.set("page", String(p));
                    return prev;
                  });
                }}
                className="rounded-lg border border-slate-700 p-1.5 text-slate-400 transition-colors hover:bg-slate-700 disabled:opacity-30"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                disabled={!hasMore}
                onClick={() => {
                  const p = page + 1;
                  setPage(p);
                  setSearchParams((prev) => {
                    prev.set("page", String(p));
                    return prev;
                  });
                }}
                className="rounded-lg border border-slate-700 p-1.5 text-slate-400 transition-colors hover:bg-slate-700 disabled:opacity-30"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
