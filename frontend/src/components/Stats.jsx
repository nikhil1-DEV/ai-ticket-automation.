/**
 * Reusable stat card for the dashboard.
 *
 * @param {string}  title    – Metric label (e.g. "Total Tickets")
 * @param {string}  value    – Metric value (e.g. "128")
 * @param {React.ElementType} icon – Lucide icon component
 * @param {string}  color    – Tailwind bg color class for the icon badge (e.g. "bg-indigo-500/15")
 * @param {string}  iconColor – Tailwind text color for the icon (e.g. "text-indigo-400")
 * @param {string}  [subtitle] – Small secondary text beneath the value
 */
export default function Stats({
  title,
  value,
  icon: Icon,
  color = "bg-indigo-500/15",
  iconColor = "text-indigo-400",
  subtitle,
}) {
  return (
    <div className="animate-fade-in rounded-xl border border-slate-700/50 bg-slate-800/60 p-5 shadow-lg backdrop-blur-sm">
      <div className="flex items-center justify-between">
        {/* Label */}
        <p className="text-sm font-medium text-slate-400">{title}</p>

        {/* Icon badge */}
        <div className={`rounded-lg p-2 ${color}`}>
          <Icon className={`h-5 w-5 ${iconColor}`} />
        </div>
      </div>

      {/* Value */}
      <p className="mt-3 text-3xl font-bold tracking-tight text-white">
        {value}
      </p>

      {/* Optional subtitle */}
      {subtitle && (
        <p className="mt-1 text-xs text-slate-500">{subtitle}</p>
      )}
    </div>
  );
}
