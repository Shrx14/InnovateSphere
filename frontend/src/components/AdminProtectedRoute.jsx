import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * Route wrapper that ensures user is both authenticated AND has admin role.
 * Redirects to home page if not authorized.
 */
const AdminProtectedRoute = ({ children }) => {
  const { isAuthenticated, isAdmin, isLoading } = useAuth();

  // Show loading spinner while auth state is being hydrated
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-neutral-950 via-neutral-950 to-neutral-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="dark:text-neutral-400 text-neutral-500">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Not logged in → redirect to home
    return <Navigate to="/" replace />;
  }

  if (!isAdmin) {
    // Logged in but not admin → redirect to home
    return <Navigate to="/" replace />;
  }

  // User is authenticated AND admin → allow access
  return children;
};

export default AdminProtectedRoute;
