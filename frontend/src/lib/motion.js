/**
 * Shared Framer Motion animation variants.
 * Import these in components for consistent animation behavior.
 */

/** Fade in with upward slide — default page/card entrance */
export const fadeIn = {
  hidden: { opacity: 0, y: 12 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3, ease: 'easeOut' },
  },
  exit: {
    opacity: 0,
    y: -8,
    transition: { duration: 0.2, ease: 'easeIn' },
  },
};

/** Container that staggers its children's entry */
export const staggerContainer = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.06,
      delayChildren: 0.04,
    },
  },
};

/** Slide in from the right — panels, drawers */
export const slideInRight = {
  hidden: { opacity: 0, x: 24 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.3, ease: 'easeOut' },
  },
  exit: {
    opacity: 0,
    x: 24,
    transition: { duration: 0.2, ease: 'easeIn' },
  },
};

/** Scale + fade — modals, toasts, popovers */
export const scaleFade = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.2, ease: 'easeOut' },
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    transition: { duration: 0.15, ease: 'easeIn' },
  },
};

/** Skeleton loading pulse */
export const skeletonPulse = {
  initial: { opacity: 0.4 },
  animate: {
    opacity: [0.4, 1, 0.4],
    transition: {
      duration: 1.5,
      repeat: Infinity,
      ease: 'easeInOut',
    },
  },
};

/** Page transition wrapper */
export const pageTransition = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: 0.2, ease: 'easeOut' } },
  exit: { opacity: 0, transition: { duration: 0.15, ease: 'easeIn' } },
};

/** Progress bar spring animation */
export const progressSpring = {
  type: 'spring',
  stiffness: 100,
  damping: 20,
  mass: 0.5,
};

/** Gentle floating animation for cards/elements */
export const floatAnimation = {
  y: [0, -10, 0],
  transition: {
    duration: 6,
    repeat: Infinity,
    ease: 'easeInOut',
  },
};

/** Card hover effect — lift with glow shadow */
export const cardHover = {
  scale: 1.02,
  y: -4,
  transition: { duration: 0.25, ease: 'easeOut' },
};

/** Card tap effect — subtle press */
export const cardTap = {
  scale: 0.98,
  transition: { duration: 0.1 },
};

/** Glow pulse for featured elements */
export const glowPulse = {
  boxShadow: [
    '0 0 5px rgba(99,102,241,0.15), 0 0 20px rgba(99,102,241,0.05)',
    '0 0 10px rgba(99,102,241,0.3), 0 0 40px rgba(99,102,241,0.1)',
    '0 0 5px rgba(99,102,241,0.15), 0 0 20px rgba(99,102,241,0.05)',
  ],
  transition: {
    duration: 3,
    repeat: Infinity,
    ease: 'easeInOut',
  },
};

/** Slide in from bottom — sections on scroll */
export const slideUp = {
  hidden: { opacity: 0, y: 40 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: 'easeOut' },
  },
};
