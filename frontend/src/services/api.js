import axios from "axios";

// ── Axios instance with shared config ────────────────────────────────
const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
  timeout: 15_000,
});

// ── Dashboard ────────────────────────────────────────────────────────
/** Fetch aggregate dashboard statistics. */
export const getDashboardStats = () =>
  api.get("/dashboard/stats").then((r) => r.data);

/** Fetch the most recent tickets for the dashboard feed. */
export const getRecentTickets = () =>
  api.get("/dashboard/recent").then((r) => r.data);

// ── Tickets CRUD ─────────────────────────────────────────────────────
/**
 * List tickets with optional filters.
 * @param {Object} [filters] - { status, category, priority, page, limit }
 */
export const getTickets = (filters = {}) => {
  // Strip undefined/null/empty values so the query string stays clean
  const params = Object.fromEntries(
    Object.entries(filters).filter(([, v]) => v != null && v !== "")
  );
  return api.get("/tickets", { params }).then((r) => r.data);
};

/** Get a single ticket by its ID. */
export const getTicket = (id) =>
  api.get(`/tickets/${id}`).then((r) => r.data);

/** Create a new ticket. Returns the created ticket (with AI analysis). */
export const createTicket = (data) =>
  api.post("/tickets", data).then((r) => r.data);

/**
 * Partially update a ticket (status, assigned_team, priority, …).
 * @param {number|string} id
 * @param {Object} data - Fields to patch
 */
export const updateTicket = (id, data) =>
  api.patch(`/tickets/${id}`, data).then((r) => r.data);

/** Re-run the AI analysis pipeline on an existing ticket. */
export const reanalyzeTicket = (id) =>
  api.post(`/tickets/${id}/reanalyze`).then((r) => r.data);

/** Fetch the full audit / activity log for a ticket. */
export const getTicketAudit = (id) =>
  api.get(`/tickets/${id}/audit`).then((r) => r.data);
