import { cn } from '@/lib/utils';

const STATUS_STYLES = {
  validated: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  pending: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  rejected: 'bg-red-500/10 text-red-400 border-red-500/20',
  downgraded: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  queued: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  running: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
  completed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  failed: 'bg-red-500/10 text-red-400 border-red-500/20',
};

/**
 * Status pill badge for ideas or jobs.
 */
export function StatusBadge({ status, className }) {
  const style = STATUS_STYLES[status] || STATUS_STYLES.pending;
  const label = status ? status.charAt(0).toUpperCase() + status.slice(1) : 'Unknown';

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium',
        style,
        className
      )}
    >
      {label}
    </span>
  );
}
