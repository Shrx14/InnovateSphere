import { Toaster as SonnerToaster } from 'sonner';

/**
 * Global toast container. Mount once in App.jsx.
 * Uses Sonner under the hood — call `toast()` from anywhere.
 */
export function Toaster() {
  return (
    <SonnerToaster
      position="bottom-right"
      toastOptions={{
        duration: 4000,
        style: {
          background: '#171717',
          border: '1px solid #262626',
          color: '#e5e5e5',
          fontSize: '14px',
        },
        classNames: {
          success: 'border-emerald-500/20',
          error: 'border-red-500/20',
          info: 'border-indigo-500/20',
        },
      }}
      closeButton
      richColors
    />
  );
}
