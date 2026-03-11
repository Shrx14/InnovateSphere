import * as React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

const Input = React.forwardRef(({ className, type, label, icon: Icon, ...props }, ref) => {
  const [focused, setFocused] = React.useState(false);
  const hasValue = props.value !== undefined ? Boolean(props.value) : false;
  const showFloating = focused || hasValue;

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
        {Icon && (
          <Icon className={cn(
            'absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 transition-colors duration-200 z-10',
            focused ? 'text-indigo-400' : 'text-neutral-500
          )} />
        )}

        <input
          type={type}
          ref={ref}
          onFocus={(e) => { setFocused(true); props.onFocus?.(e); }}
          onBlur={(e) => { setFocused(false); props.onBlur?.(e); }}
          className={cn(
            'relative w-full rounded-xl bg-neutral-900/80 backdrop-blur-sm text-sm text-white
            'border border-neutral-700/50 outline-none',
            'transition-all duration-300',
            'placeholder:text-neutral-500
            'focus:border-indigo-500/50 focus:bg-neutral-900',
            'focus:shadow-[0_0_20px_rgba(99,102,241,0.1)]',
            Icon ? 'pl-10 pr-4' : 'px-4',
            label ? 'pt-5 pb-2 h-14' : 'py-3 h-12',
            className,
          )}
          {...props}
        />

        {/* Floating label */}
        {label && (
          <motion.label
            initial={false}
            animate={{
              y: showFloating ? -8 : 0,
              scale: showFloating ? 0.75 : 1,
              color: focused ? 'rgb(129,140,248)' : 'rgb(115,115,115)',
            }}
            className={cn(
              'absolute top-1/2 -translate-y-1/2 text-sm origin-left pointer-events-none z-10',
              Icon ? 'left-10' : 'left-4',
            )}
          >
            {label}
          </motion.label>
        )}
      </div>
    </div>
  );
});
Input.displayName = 'Input';

export { Input };
