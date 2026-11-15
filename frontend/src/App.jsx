import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import Dashboard from "./components/Dashboard";
import TicketList from "./components/TicketList";
import TicketDetail from "./components/TicketDetail";
import TicketForm from "./components/TicketForm";

/**
 * Root application component.
 * Renders a fixed dark sidebar + scrollable main content area.
 */
export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-slate-900 text-slate-100">
        {/* ── Sidebar ──────────────────────────────────────────── */}
        <Navbar />

        {/* ── Main content area ────────────────────────────────── */}
        <main className="flex-1 overflow-y-auto bg-slate-900 p-6 lg:p-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/tickets" element={<TicketList />} />
            <Route path="/tickets/new" element={<TicketForm />} />
            <Route path="/tickets/:id" element={<TicketDetail />} />
            {/* Catch-all → redirect to dashboard */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
