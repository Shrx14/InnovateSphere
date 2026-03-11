import * as React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { skeletonPulse } from '@/lib/motion';

/** Base skeleton element with pulse animation */
const Skeleton = React.forwardRef(({ className, ...props }, ref) => (
  <motion.div
    ref={ref}
    variants={skeletonPulse}
    initial="initial"
    animate="animate"
    className={cn('rounded-lg bg-neutral-800 className)}
    aria-hidden="true"
    {...props}
  />
));
Skeleton.displayName = 'Skeleton';

/** Skeleton text line */
const SkeletonText = ({ className, lines = 3, ...props }) => (
  <div className={cn('space-y-2', className)} aria-busy="true" aria-label="Loading" {...props}>
    {Array.from({ length: lines }).map((_, i) => (
      <Skeleton
        key={i}
        className={cn('h-4', i === lines - 1 ? 'w-3/4' : 'w-full')}
      />
    ))}
  </div>
);

/** Skeleton card matching the app's card layout */
const SkeletonCard = ({ className, ...props }) => (
  <div
    className={cn(
      'rounded-2xl border border-neutral-800 bg-neutral-900 p-6 space-y-4',
      className
    )}
    aria-busy="true"
    aria-label="Loading"
    {...props}
  >
    <div className="flex items-center justify-between">
      <Skeleton className="h-5 w-20 rounded-full" />
      <Skeleton className="h-5 w-16 rounded-full" />
    </div>
    <Skeleton className="h-6 w-3/4" />
    <SkeletonText lines={2} />
    <div className="flex gap-3 pt-2">
      <Skeleton className="h-8 w-24 rounded-lg" />
      <Skeleton className="h-8 w-24 rounded-lg" />
    </div>
  </div>
);

/** Skeleton for metric/stat cards */
const SkeletonMetric = ({ className, ...props }) => (
  <div
    className={cn(
      'rounded-2xl border border-neutral-800 bg-neutral-900 p-6',
      className
    )}
    aria-busy="true"
    aria-label="Loading"
    {...props}
  >
    <Skeleton className="h-4 w-20 mb-3" />
    <Skeleton className="h-8 w-16" />
  </div>
);

export { Skeleton, SkeletonText, SkeletonCard, SkeletonMetric };
