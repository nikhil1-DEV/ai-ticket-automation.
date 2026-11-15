import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Send,
  Loader2,
  CheckCircle2,
  BrainCircuit,
  AlertCircle,
} from "lucide-react";
import { createTicket } from "../services/api";

const SOURCES = ["web_form", "email", "api"];

/**
 * New ticket submission form.
 * On success, displays AI analysis results and a link to the created ticket.
 */
export default function TicketForm() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    subject: "",
    description: "",
    sender_name: "",
    sender_email: "",
    source: "web_form",
  });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [created, setCreated] = useState(null); // holds the created ticket

  /** Two-way binding helper. */
  const set = (key) => (e) => {
    setForm((prev) => ({ ...prev, [key]: e.target.value }));
    // Clear field-level error on edit
    if (errors[key]) setErrors((prev) => ({ ...prev, [key]: null }));
  };

  /** Validate required fields. */
  const validate = () => {
    const errs = {};
    if (!form.subject.trim()) errs.subject = "Subject is required";
    if (!form.description.trim()) errs.description = "Description is required";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  /** Submit handler. */
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setSubmitting(true);
    try {
      const ticket = await createTicket({
        subject: form.subject.trim(),
        description: form.description.trim(),
        sender_name: form.sender_name.trim() || undefined,
        sender_email: form.sender_email.trim() || undefined,
        source: form.source,
      });
      setCreated(ticket);
    } catch (err) {
      console.error("Create ticket failed:", err);
      setErrors({ _server: "Something went wrong. Please try again." });
    } finally {
      setSubmitting(false);
    }
  };

  /* ── Success view ───────────────────────────────────────────────── */
  if (created) {
    const confidencePct = Math.round((created.ai_confidence ?? 0) * 100);

    return (
      <div className="mx-auto max-w-2xl animate-fade-in space-y-6">
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-6 text-center shadow-lg">
          <CheckCircle2 className="mx-auto h-12 w-12 text-emerald-400" />
          <h2 className="mt-3 text-xl font-bold text-white">
            Ticket Created Successfully!
          </h2>
          <p className="mt-1 text-sm text-slate-400">
            Your ticket has been analyzed by AI and routed automatically.
          </p>
        </div>

        {/* AI Analysis Results */}
        <div className="rounded-xl border border-indigo-500/20 bg-slate-800/60 p-6 shadow-lg">
          <div className="mb-4 flex items-center gap-2">
            <BrainCircuit className="h-5 w-5 text-indigo-400" />
            <h3 className="font-semibold text-white">AI Analysis Results</h3>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <p className="text-xs text-slate-500">Category</p>
              <p className="mt-1 text-sm font-medium capitalize text-slate-200">
                {created.category?.replace("_", " ")}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Priority</p>
              <p className="mt-1 text-sm font-medium capitalize text-slate-200">
                {created.priority}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Confidence</p>
              <div className="mt-1 flex items-center gap-2">
                <div className="h-2 w-full rounded-full bg-slate-700">
                  <div
                    className="h-2 rounded-full bg-indigo-500"
                    style={{ width: `${confidencePct}%` }}
                  />
                </div>
                <span className="text-sm font-semibold text-indigo-400">
                  {confidencePct}%
                </span>
              </div>
            </div>
          </div>

          {created.ai_summary && (
            <div className="mt-4">
              <p className="text-xs text-slate-500">AI Summary</p>
              <p className="mt-1 text-sm text-slate-300">
                {created.ai_summary}
              </p>
            </div>
          )}
        </div>

        {/* Action links */}
        <div className="flex gap-3">
          <Link
            to={`/tickets/${created.id}`}
            className="flex-1 rounded-lg bg-indigo-600 px-4 py-2.5 text-center text-sm font-medium text-white transition-colors hover:bg-indigo-500"
          >
            View Ticket #{created.id}
          </Link>
          <button
            onClick={() => {
              setCreated(null);
              setForm({
                subject: "",
                description: "",
                sender_name: "",
                sender_email: "",
                source: "web_form",
              });
            }}
            className="flex-1 rounded-lg border border-slate-700 px-4 py-2.5 text-center text-sm font-medium text-slate-300 transition-colors hover:bg-slate-800"
          >
            Submit Another
          </button>
        </div>
      </div>
    );
  }

  /* ── Form view ──────────────────────────────────────────────────── */
  return (
    <div className="mx-auto max-w-2xl space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">Submit a Ticket</h1>
        <p className="mt-1 text-sm text-slate-400">
          Describe your issue — our AI will categorize and prioritize it
          automatically.
        </p>
      </div>

      {/* Server error */}
      {errors._server && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2.5 text-sm text-red-400">
          <AlertCircle className="h-4 w-4" />
          {errors._server}
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="space-y-5 rounded-xl border border-slate-700/50 bg-slate-800/60 p-6 shadow-lg"
      >
        {/* Subject */}
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-300">
            Subject <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            value={form.subject}
            onChange={set("subject")}
            placeholder="Brief summary of the issue"
            className={`w-full rounded-lg border bg-slate-900/80 px-4 py-2.5 text-sm text-slate-100 placeholder-slate-600 outline-none transition-colors ${
              errors.subject
                ? "border-red-500 focus:border-red-400"
                : "border-slate-700 focus:border-indigo-500"
            }`}
          />
          {errors.subject && (
            <p className="mt-1 text-xs text-red-400">{errors.subject}</p>
          )}
        </div>

        {/* Description */}
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-300">
            Description <span className="text-red-400">*</span>
          </label>
          <textarea
            rows={6}
            value={form.description}
            onChange={set("description")}
            placeholder="Provide as much detail as possible…"
            className={`w-full resize-y rounded-lg border bg-slate-900/80 px-4 py-2.5 text-sm text-slate-100 placeholder-slate-600 outline-none transition-colors ${
              errors.description
                ? "border-red-500 focus:border-red-400"
                : "border-slate-700 focus:border-indigo-500"
            }`}
          />
          {errors.description && (
            <p className="mt-1 text-xs text-red-400">{errors.description}</p>
          )}
        </div>

        {/* Sender name + email row */}
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-300">
              Your Name{" "}
              <span className="text-slate-600">(optional)</span>
            </label>
            <input
              type="text"
              value={form.sender_name}
              onChange={set("sender_name")}
              placeholder="Jane Doe"
              className="w-full rounded-lg border border-slate-700 bg-slate-900/80 px-4 py-2.5 text-sm text-slate-100 placeholder-slate-600 outline-none focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-300">
              Email{" "}
              <span className="text-slate-600">(optional)</span>
            </label>
            <input
              type="email"
              value={form.sender_email}
              onChange={set("sender_email")}
              placeholder="jane@example.com"
              className="w-full rounded-lg border border-slate-700 bg-slate-900/80 px-4 py-2.5 text-sm text-slate-100 placeholder-slate-600 outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        {/* Source */}
        <div>
          <label className="mb-1.5 block text-sm font-medium text-slate-300">
            Source
          </label>
          <select
            value={form.source}
            onChange={set("source")}
            className="rounded-lg border border-slate-700 bg-slate-900/80 px-4 py-2.5 text-sm text-slate-300 outline-none focus:border-indigo-500"
          >
            {SOURCES.map((s) => (
              <option key={s} value={s}>
                {s.replace("_", " ")}
              </option>
            ))}
          </select>
        </div>

        {/* Submit button */}
        <button
          type="submit"
          disabled={submitting}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 py-2.5 text-sm font-semibold text-white shadow-lg transition-colors hover:bg-indigo-500 disabled:opacity-50"
        >
          {submitting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
          {submitting ? "Submitting…" : "Submit Ticket"}
        </button>
      </form>
    </div>
  );
}
