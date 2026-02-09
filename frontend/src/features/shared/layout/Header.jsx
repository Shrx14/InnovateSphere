import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';

const Header = () => {
  const { isAuthenticated, logout } = useAuth();

  return (
    <header className="sticky top-0 z-50 bg-neutral-950/70 backdrop-blur border-b border-neutral-800">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link
          to="/"
          className="text-sm font-semibold tracking-wide text-neutral-200 hover:text-neutral-100 transition"
        >
          InnovateSphere
        </Link>

        <nav aria-label="Primary navigation">
          <ul className="flex items-center gap-6 text-sm text-neutral-400">
            <li>
              <Link to="/explore" className="hover:text-neutral-200 transition">
                Explore
              </Link>
            </li>
            {isAuthenticated ? (
              <>
                <li>
                  <Link to="/user/dashboard" className="hover:text-neutral-200 transition">
                    Dashboard
                  </Link>
                </li>
                <li>
                  <button
                    onClick={logout}
                    className="hover:text-neutral-200 transition"
                  >
                    Sign out
                  </button>
                </li>
              </>
            ) : (
              <>
                <li>
                  <Link to="/login" className="hover:text-neutral-200 transition">
                    Sign in
                  </Link>
                </li>
                <li>
                  <Link
                    to="/register"
                    className="px-4 py-2 rounded-md border border-neutral-700 hover:border-neutral-500 text-neutral-200 transition"
                  >
                    Get started
                  </Link>
                </li>
              </>
            )}
          </ul>
        </nav>
      </div>
    </header>
  );
};

export default Header;
