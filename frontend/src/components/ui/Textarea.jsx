import * as React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

const Textarea = React.forwardRef(({ className, label, ...props }, ref) => {
  const [focused, setFocused] = React.useState(false);

  return (
    <div className="relative group">
      {/* Animated border gradient */}
      <div className={cn(
        'absolute -inset-[1px] rounded-xl transition-opacity duration-300',
        focused
          ? 'opacity-100 bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-500 blur-[1px]'
          : 'opacity-0'
      )} />

      <div className="relative">
        <textarea
          ref={ref}
          onFocus={(e) => { setFocused(true); props.onFocus?.(e); }}
          onBlur={(e) => { setFocused(false); props.onBlur?.(e); }}
          className={cn(
            'relative w-full rounded-xl dark:bg-neutral-900/80 bg-white/80 backdrop-blur-sm text-sm dark:text-white text-neutral-900',
            'border dark:border-neutral-700/50 border-neutral-200 outline-none',
            'transition-all duration-300 min-h-[120px]',
            'placeholder:dark:text-neutral-500 text-neutral-400',
            'focus:border-indigo-500/50 focus:bg-neutral-900',
            'focus:shadow-[0_0_20px_rgba(99,102,241,0.1)]',
            'px-4 py-3',
            className,
          )}
          {...props}
        />

        {/* Focus indicator line */}
        <motion.div
          initial={false}
          animate={{ scaleX: focused ? 1 : 0 }}
          transition={{ duration: 0.3 }}
          className="absolute bottom-0 left-4 right-4 h-[2px] bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full origin-left"
        />
      </div>
    </div>
  );
});
Textarea.displayName = 'Textarea';

export { Textarea };
