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
          <span className="text-xs dark:text-neutral-400 text-neutral-500">{label}</span>
          <span className="text-xs font-medium dark:text-neutral-300 text-neutral-600">{Math.round(value)}%</span>
        </div>
      )}
      <div className="h-2 w-full rounded-full dark:bg-neutral-800 bg-neutral-100 overflow-hidden">
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
