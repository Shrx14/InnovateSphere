import { cn } from '@/lib/utils';

/**
 * Reusable empty state for lists/pages.
 * @param {string} icon - Emoji or Lucide icon component
 * @param {string} title - Heading text
 * @param {string} description - Body text
 * @param {React.ReactNode} action - Optional CTA button
 */
export function EmptyState({ icon, title, description, action, className }) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-16 px-6 text-center', className)}>
      {icon && (
        <div className="text-4xl mb-4 text-neutral-600">
          {typeof icon === 'string' ? icon : icon}
        </div>
      )}
      {title && (
        <h3 className="text-lg font-medium dark:text-neutral-300 text-neutral-600 mb-2">{title}</h3>
      )}
      {description && (
        <p className="text-sm dark:text-neutral-500 text-neutral-400 max-w-md mb-6">{description}</p>
      )}
      {action && <div>{action}</div>}
    </div>
  );
}
