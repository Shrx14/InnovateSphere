import { cn } from '@/lib/utils';
import { formatScore, scoreColor, scoreBgColor } from '@/lib/formatScore';

function scoreInterpretation(raw) {
  if (raw == null || isNaN(raw)) return 'No score available';
  const n = Number(raw);
  if (n >= 80) return 'Excellent — highly novel or high quality';
  if (n >= 70) return 'Very good — strong originality';
  if (n >= 50) return 'Moderate — some existing overlap';
  if (n >= 30) return 'Low — significant overlap with existing work';
  return 'Very low — closely resembles existing solutions';
}

/**
 * Reusable score display badge.
 * @param {number} value - Raw score (0–100 scale)
 * @param {string} label - e.g. "Novelty", "Quality"
 * @param {'sm'|'md'|'lg'} size
 */
export function ScoreDisplay({ value, label, size = 'md', className }) {
  const sizeClasses = {
    sm: { wrapper: 'px-2 py-1', score: 'text-xs', label: 'text-[10px]' },
    md: { wrapper: 'px-3 py-1.5', score: 'text-sm', label: 'text-xs' },
    lg: { wrapper: 'px-4 py-3', score: 'text-3xl', label: 'text-sm' },
  };
  const s = sizeClasses[size] || sizeClasses.md;

  return (
    <div
      className={cn(
        'flex items-center gap-2 rounded-lg',
        s.wrapper,
        scoreBgColor(value),
        className
      )}
      title={scoreInterpretation(value)}
    >
      {label && (
        <span className={cn('text-neutral-400', s.label)}>{label}</span>
      )}
      <span className={cn('font-semibold', s.score, scoreColor(value))}>
        {formatScore(value)}
      </span>
    </div>
  );
}
