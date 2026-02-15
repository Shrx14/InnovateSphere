/**
 * Format a raw score (0–100 internal) to display scale (0.0–10.0).
 * Single source of truth — replaces all inline `(score / 10).toFixed(1)`.
 */
export function formatScore(raw, decimals = 1) {
  if (raw == null || isNaN(raw)) return '—';
  return (Number(raw) / 10).toFixed(decimals);
}

/**
 * Get color class for a score value (0–100 internal scale).
 * green > 70, yellow 50–70, red < 50
 */
export function scoreColor(raw) {
  if (raw == null || isNaN(raw)) return 'text-neutral-400';
  const n = Number(raw);
  if (n >= 70) return 'text-emerald-400';
  if (n >= 50) return 'text-yellow-400';
  return 'text-red-400';
}

/**
 * Get background color class for a score badge.
 */
export function scoreBgColor(raw) {
  if (raw == null || isNaN(raw)) return 'bg-neutral-800';
  const n = Number(raw);
  if (n >= 70) return 'bg-emerald-500/10';
  if (n >= 50) return 'bg-yellow-500/10';
  return 'bg-red-500/10';
}
