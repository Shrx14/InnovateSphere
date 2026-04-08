import * as React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { progressSpring } from '@/lib/motion';

/**
 * Animated progress bar with spring physics.
 * @param {number} value - Progress 0–100
 * @param {string} label - Optional text label for current phase
 */
export function ProgressBar({ value = 0, label, className }) {
  return (
    <div className={cn('w-full', className)}>
      {label && (
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-neutral-400">{label}</span>
          <span className="text-xs font-medium text-neutral-300">{Math.round(value)}%</span>
        </div>
      )}
      <div className="h-2 w-full rounded-full bg-neutral-800 overflow-hidden">
        <motion.div
          className="h-full rounded-full bg-indigo-500"
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(100, Math.max(0, value))}%` }}
          transition={progressSpring}
        />
      </div>
    </div>
  );
}
