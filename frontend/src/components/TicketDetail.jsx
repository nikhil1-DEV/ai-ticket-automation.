import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  BrainCircuit,
  RefreshCcw,
  Save,
  Loader2,
  Clock,
  CheckCircle2,
  AlertCircle,
  MessageSquareText,
} from "lucide-react";
import {
  getTicket,
  updateTicket,
  reanalyzeTicket,
  getTicketAudit,
} from "../services/api";

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

const STATUSES = [
  "new",
  "processing",
  "assigned",
  "in_progress",
  "pending_approval",
  "resolved",
  "closed",
];

/**
 * Single ticket detail page.
 * Shows ticket info, AI analysis, status management, and audit log.
 */
export default function TicketDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [ticket, setTicket] = useState(null);
  const [audit, setAudit] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [reanalyzing, setReanalyzing] = useState(false);
  const [newStatus, setNewStatus] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  /* ── Fetch ticket + audit on mount ──────────────────────────────── */
  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [t, a] = await Promise.all([
          getTicket(id),
          getTicketAudit(id).catch(() => []),
        ]);
        setTicket(t);
        setNewStatus(t.status);
        setAudit(Array.isArray(a) ? a : a?.entries ?? []);
      } catch (err) {
        console.error("Failed to load ticket:", err);
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  /* ── Save status change ─────────────────────────────────────────── */
  const handleSave = async () => {
    if (!newStatus || newStatus === ticket.status) return;
    setSaving(true);
    try {
      const updated = await updateTicket(id, { status: newStatus });
      setTicket(updated);
      setSuccessMsg("Status updated!");
      // Refresh audit
      const a = await getTicketAudit(id).catch(() => []);
      setAudit(Array.isArray(a) ? a : a?.entries ?? []);
      setTimeout(() => setSuccessMsg(""), 3000);
    } catch (err) {
      console.error("Update failed:", err);
    } finally {
      setSaving(false);
    }
  };

  /* ── Re-analyze ─────────────────────────────────────────────────── */
  const handleReanalyze = async () => {
    setReanalyzing(true);
    try {
      const updated = await reanalyzeTicket(id);
      setTicket(updated);
      setSuccessMsg("AI analysis complete!");
      setTimeout(() => setSuccessMsg(""), 3000);
    } catch (err) {
      console.error("Reanalyze failed:", err);
    } finally {
      setReanalyzing(false);
    }
  };

  /* ── Loading / error states ─────────────────────────────────────── */
  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-400" />
      </div>
    );
  }

  if (!ticket) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 text-slate-400">
        <AlertCircle className="h-12 w-12" />
        <p>Ticket not found.</p>
        <button
          onClick={() => navigate("/tickets")}
          className="text-sm text-indigo-400 hover:underline"
        >
          Back to tickets
        </button>
      </div>
    );
  }

  const confidencePct = Math.round((ticket.ai_confidence ?? 0) * 100);

  return (
    <div className="mx-auto max-w-4xl space-y-6 animate-fade-in">
      {/* ── Back button ────────────────────────────────────────── */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-200"
      >
        <ArrowLeft className="h-4 w-4" />
        Back
      </button>

      {/* ── Success toast ──────────────────────────────────────── */}
      {successMsg && (
        <div className="flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-2.5 text-sm text-emerald-400">
          <CheckCircle2 className="h-4 w-4" />
          {successMsg}
        </div>
      )}

      {/* ── Ticket header card ─────────────────────────────────── */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-800/60 p-6 shadow-lg">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-medium text-slate-500">
              Ticket #{ticket.id}
            </p>
            <h1 className="mt-1 text-xl font-bold text-white">
              {ticket.subject}
            </h1>
          </div>
          <div className="flex flex-wrap gap-2">
            <span
              className={`rounded-full px-3 py-1 text-xs font-semibold capitalize ${
                PRIORITY_STYLES[ticket.priority] ?? ""
              }`}
            >
              {ticket.priority}
            </span>
            <span
              className={`rounded-full px-3 py-1 text-xs font-semibold capitalize ${
                STATUS_STYLES[ticket.status] ?? ""
              }`}
            >
              {ticket.status?.replace("_", " ")}
            </span>
          </div>
        </div>

        {/* Meta row */}
        <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-sm text-slate-400">
          {ticket.sender_name && <span>From: {ticket.sender_name}</span>}
          {ticket.sender_email && <span>Email: {ticket.sender_email}</span>}
          {ticket.assigned_team && (
            <span>Team: {ticket.assigned_team}</span>
          )}
          <span>Source: {ticket.source}</span>
          <span>
            Created:{" "}
            {new Date(ticket.created_at).toLocaleString()}
          </span>
        </div>

        {/* Description */}
        <div className="mt-5 rounded-lg border border-slate-700/40 bg-slate-900/50 p-4">
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-300">
            {ticket.description}
          </p>
        </div>
      </div>

      {/* ── AI Analysis section ────────────────────────────────── */}
      <div className="rounded-xl border border-indigo-500/20 bg-slate-800/60 p-6 shadow-lg">
        <div className="mb-4 flex items-center gap-2">
          <BrainCircuit className="h-5 w-5 text-indigo-400" />
          <h2 className="text-lg font-semibold text-white">AI Analysis</h2>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          {/* Category */}
          <div>
            <p className="text-xs text-slate-500">Category</p>
            <p className="mt-1 text-sm font-medium capitalize text-slate-200">
              {ticket.category?.replace("_", " ")}
            </p>
          </div>

          {/* Priority */}
          <div>
            <p className="text-xs text-slate-500">Priority</p>
            <p className="mt-1 text-sm font-medium capitalize text-slate-200">
              {ticket.priority}
            </p>
          </div>

          {/* Confidence */}
          <div>
            <p className="text-xs text-slate-500">Confidence</p>
            <div className="mt-1 flex items-center gap-2">
              <div className="h-2 w-full rounded-full bg-slate-700">
                <div
                  className="h-2 rounded-full bg-indigo-500 transition-all"
                  style={{ width: `${confidencePct}%` }}
                />
              </div>
              <span className="text-sm font-semibold text-indigo-400">
                {confidencePct}%
              </span>
            </div>
          </div>
        </div>

        {/* AI Summary */}
        {ticket.ai_summary && (
          <div className="mt-5">
            <p className="text-xs font-medium text-slate-500">AI Summary</p>
            <p className="mt-1 text-sm leading-relaxed text-slate-300">
              {ticket.ai_summary}
            </p>
          </div>
        )}

        {/* AI Draft Response */}
        {ticket.ai_draft_response && (
          <div className="mt-5">
            <p className="text-xs font-medium text-slate-500">
              AI Draft Response
            </p>
            <div className="mt-2 rounded-lg border border-indigo-500/20 bg-indigo-950/30 p-4">
              <div className="flex items-start gap-2">
                <MessageSquareText className="mt-0.5 h-4 w-4 shrink-0 text-indigo-400" />
                <p className="whitespace-pre-wrap text-sm leading-relaxed text-indigo-200">
                  {ticket.ai_draft_response}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Reanalyze button */}
        <button
          onClick={handleReanalyze}
          disabled={reanalyzing}
          className="mt-5 flex items-center gap-2 rounded-lg border border-indigo-500/30 bg-indigo-500/10 px-4 py-2 text-sm font-medium text-indigo-400 transition-colors hover:bg-indigo-500/20 disabled:opacity-50"
        >
          {reanalyzing ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCcw className="h-4 w-4" />
          )}
          {reanalyzing ? "Analyzing…" : "Re-analyze with AI"}
        </button>
      </div>

      {/* ── Status management ──────────────────────────────────── */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-800/60 p-6 shadow-lg">
        <h2 className="mb-4 text-sm font-semibold text-slate-300">
          Update Status
        </h2>
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={newStatus}
            onChange={(e) => setNewStatus(e.target.value)}
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-300 outline-none focus:border-indigo-500"
          >
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s.replace("_", " ")}
              </option>
            ))}
          </select>

          <button
            onClick={handleSave}
            disabled={saving || newStatus === ticket.status}
            className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 disabled:opacity-40"
          >
            {saving ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Save className="h-4 w-4" />
            )}
            Save
          </button>
        </div>
      </div>

      {/* ── Audit log timeline ─────────────────────────────────── */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-800/60 p-6 shadow-lg">
        <h2 className="mb-4 text-sm font-semibold text-slate-300">
          Activity Log
        </h2>

        {audit.length === 0 ? (
          <p className="text-sm text-slate-500">No activity recorded yet.</p>
        ) : (
          <div className="space-y-4">
            {audit.map((entry, i) => (
              <div key={i} className="flex gap-3">
                {/* Timeline dot + line */}
                <div className="flex flex-col items-center">
                  <div className="mt-1 h-2.5 w-2.5 rounded-full bg-indigo-500" />
                  {i < audit.length - 1 && (
                    <div className="w-px flex-1 bg-slate-700" />
                  )}
                </div>

                {/* Content */}
                <div className="pb-4">
                  <p className="text-sm text-slate-300">
                    {entry.action ?? entry.description ?? entry.message ?? JSON.stringify(entry)}
                  </p>
                  <div className="mt-1 flex items-center gap-1.5 text-xs text-slate-500">
                    <Clock className="h-3 w-3" />
                    {entry.timestamp || entry.created_at
                      ? new Date(
                          entry.timestamp ?? entry.created_at
                        ).toLocaleString()
                      : "—"}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
