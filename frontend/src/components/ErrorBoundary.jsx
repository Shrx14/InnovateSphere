import React from 'react';

/**
 * Error boundary — catches render errors and shows a recovery UI.
 */
export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[400px] flex items-center justify-center p-8">
          <div className="text-center max-w-md">
            <div className="text-4xl mb-4 text-neutral-600">⚠</div>
            <h2 className="text-xl font-medium dark:text-white text-neutral-900 mb-2">Something went wrong</h2>
            <p className="dark:text-neutral-400 text-neutral-500 text-sm mb-6">
              {this.state.error?.message || 'An unexpected error occurred.'}
            </p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="inline-flex items-center justify-center rounded-lg bg-indigo-600/90 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500/90 transition-colors"
            >
              Try again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
