import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Check } from 'lucide-react';
import { cn } from '@/lib/utils';

const Select = ({
    value,
    onChange,
    options = [],
    placeholder = 'Select an option',
    className = '',
    disabled = false,
}) => {
    const [open, setOpen] = useState(false);
    const ref = useRef(null);

    // Close on click outside
    useEffect(() => {
        const handleClick = (e) => {
            if (ref.current && !ref.current.contains(e.target)) {
                setOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClick);
        return () => document.removeEventListener('mousedown', handleClick);
    }, []);

    // Close on Escape
    useEffect(() => {
        const handleKey = (e) => {
            if (e.key === 'Escape') setOpen(false);
        };
        if (open) document.addEventListener('keydown', handleKey);
        return () => document.removeEventListener('keydown', handleKey);
    }, [open]);

    const selectedLabel = options.find((o) =>
        typeof o === 'string' ? o === value : o.value === value
    );
    const displayLabel = selectedLabel
        ? typeof selectedLabel === 'string'
            ? selectedLabel
            : selectedLabel.label
        : placeholder;

    return (
        <div ref={ref} className={cn('relative', className)}>
            {/* Trigger */}
            <button
                type="button"
                disabled={disabled}
                onClick={() => setOpen((prev) => !prev)}
                className={cn(
                    'w-full flex items-center justify-between gap-2 px-4 py-3 rounded-xl text-sm transition-all duration-200',
                    'bg-neutral-900/80 border backdrop-blur-sm',
                    'focus:outline-none',
                    open
                        ? 'border-indigo-500/50 shadow-[0_0_20px_rgba(99,102,241,0.15)]'
                        : 'border-neutral-700/50 hover:border-neutral-600',
                    disabled && 'opacity-50 cursor-not-allowed',
                    value ? 'text-white' : 'text-neutral-400'
                )}
            >
                <span className="truncate">{displayLabel}</span>
                <ChevronDown
                    className={cn(
                        'w-4 h-4 text-neutral-400 transition-transform duration-200 flex-shrink-0',
                        open && 'rotate-180'
                    )}
                />
            </button>

            {/* Dropdown */}
            <AnimatePresence>
                {open && (
                    <motion.div
                        initial={{ opacity: 0, y: -8, scale: 0.96 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -8, scale: 0.96 }}
                        transition={{ duration: 0.15, ease: 'easeOut' }}
                        className="absolute z-50 mt-2 w-full rounded-xl border border-neutral-700/50 bg-neutral-900/95 backdrop-blur-xl shadow-2xl shadow-black/40 overflow-hidden"
                    >
                        <div className="max-h-64 overflow-y-auto py-1 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-neutral-700">
                            {options.map((opt) => {
                                const optValue = typeof opt === 'string' ? opt : opt.value;
                                const optLabel = typeof opt === 'string' ? opt : opt.label;
                                const isSelected = optValue === value;

                                return (
                                    <button
                                        key={optValue}
                                        type="button"
                                        onClick={() => {
                                            onChange({ target: { value: optValue } });
                                            setOpen(false);
                                        }}
                                        className={cn(
                                            'w-full flex items-center gap-3 px-4 py-2.5 text-sm text-left transition-colors duration-100',
                                            isSelected
                                                ? 'bg-indigo-500/15 text-indigo-500 dark:text-indigo-300'
                                                : 'text-neutral-300 hover:bg-neutral-800/60 hover:text-white'
                                        )}
                                    >
                                        <span className="flex-1 truncate">{optLabel}</span>
                                        {isSelected && (
                                            <Check className="w-4 h-4 text-indigo-400 flex-shrink-0" />
                                        )}
                                    </button>
                                );
                            })}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export { Select };
