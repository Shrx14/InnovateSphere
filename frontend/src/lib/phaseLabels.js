/**
 * Generation phase labels — synced with backend/generation/job_queue.py.
 * Backend phases: 0=Retrieving, 1=Novelty, 2=Constraints, 3=LLM, 4=Complete
 */
export const PHASE_LABELS = {
  0: 'Retrieving sources',
  1: 'Analyzing novelty',
  2: 'Checking constraints',
  3: 'Generating with AI',
  4: 'Complete',
};

/**
 * Get a human-readable phase label.
 * Prefers the backend-supplied phase_name, falls back to local map.
 */
export function getPhaseLabel(phase, backendPhaseName) {
  if (backendPhaseName) return backendPhaseName;
  return PHASE_LABELS[phase] ?? 'Processing…';
}

/**
 * Calculate progress percentage from phase (if backend doesn't supply one).
 * Each phase = ~20% of total.
 */
export function estimateProgress(phase) {
  if (phase == null) return 0;
  return Math.min(100, (Number(phase) / 4) * 100);
}
