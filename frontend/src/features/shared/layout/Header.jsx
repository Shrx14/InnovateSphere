import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';

const Header = () => {
  const { isAuthenticated, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 bg-neutral-950/70 backdrop-blur border-b border-neutral-800">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link
          to="/"
          className="text-sm font-semibold tracking-wide text-neutral-200 hover:text-neutral-100 transition"
        >
          InnovateSphere
        </Link>

        {/* Mobile hamburger */}
        <button
          className="md:hidden text-neutral-400 hover:text-neutral-200 transition"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle navigation"
          aria-expanded={mobileOpen}
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            {mobileOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>

        {/* Desktop nav */}
        <nav aria-label="Primary navigation" className="hidden md:block">
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
                  <Link to="/user/generate" className="hover:text-neutral-200 transition">
                    Generate
                  </Link>
                </li>
                <li>
                  <Link to="/user/novelty" className="hover:text-neutral-200 transition">
                    Novelty
                  </Link>
                </li>
                <li>
                  <Link to="/user/my-ideas" className="hover:text-neutral-200 transition">
                    My Ideas
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

      {/* Mobile nav dropdown */}
      {mobileOpen && (
        <nav className="md:hidden border-t border-neutral-800 bg-neutral-950/95 backdrop-blur" aria-label="Mobile navigation">
          <ul className="flex flex-col gap-2 px-6 py-4 text-sm text-neutral-400">
            <li><Link to="/explore" onClick={() => setMobileOpen(false)} className="block py-2 hover:text-neutral-200 transition">Explore</Link></li>
            {isAuthenticated ? (
              <>
                <li><Link to="/user/dashboard" onClick={() => setMobileOpen(false)} className="block py-2 hover:text-neutral-200 transition">Dashboard</Link></li>
                <li><Link to="/user/generate" onClick={() => setMobileOpen(false)} className="block py-2 hover:text-neutral-200 transition">Generate</Link></li>
                <li><Link to="/user/novelty" onClick={() => setMobileOpen(false)} className="block py-2 hover:text-neutral-200 transition">Novelty</Link></li>
                <li><Link to="/user/my-ideas" onClick={() => setMobileOpen(false)} className="block py-2 hover:text-neutral-200 transition">My Ideas</Link></li>
                <li><button onClick={() => { logout(); setMobileOpen(false); }} className="block py-2 hover:text-neutral-200 transition w-full text-left">Sign out</button></li>
              </>
            ) : (
              <>
                <li><Link to="/login" onClick={() => setMobileOpen(false)} className="block py-2 hover:text-neutral-200 transition">Sign in</Link></li>
                <li><Link to="/register" onClick={() => setMobileOpen(false)} className="block py-2 hover:text-neutral-200 transition">Get started</Link></li>
              </>
            )}
          </ul>
        </nav>
      )}
    </header>
  );
};

export default Header;
