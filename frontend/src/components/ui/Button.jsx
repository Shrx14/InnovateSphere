import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-neutral-950 focus-visible:ring-offset-white disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-indigo-600/90 text-white hover:bg-indigo-500/90',
        secondary: 'border dark:border-neutral-700 border-neutral-300 dark:text-neutral-200 text-neutral-700 dark:hover:bg-neutral-800 hover:bg-neutral-100 hover:text-neutral-900 dark:hover:text-white text-neutral-900',
        ghost: 'dark:text-neutral-400 text-neutral-600 dark:hover:bg-neutral-800 hover:bg-neutral-100 dark:hover:text-white text-neutral-900 hover:text-neutral-900',
        destructive: 'bg-red-600/90 text-white hover:bg-red-500/90',
        outline: 'border dark:border-neutral-700 border-neutral-300 bg-transparent dark:text-neutral-200 text-neutral-700 dark:hover:bg-neutral-800 hover:bg-neutral-100',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-8 rounded-md px-3 text-xs',
        lg: 'h-12 rounded-lg px-8 text-base',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

const Button = React.forwardRef(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button';
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';

export { Button, buttonVariants };
