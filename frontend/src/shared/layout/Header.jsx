import React from 'react';
import { Link } from 'react-router-dom';

const Header = () => {
  return (
    <header className="sticky top-0 z-50 bg-neutral-950/80 backdrop-blur border-b border-neutral-800">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="text-sm font-semibold tracking-wide">
          InnovateSphere
        </div>

        <nav className="flex items-center gap-6 text-sm text-neutral-400">
          <Link to="/" className="hover:text-neutral-200 transition">
            Explore
          </Link>
          <Link to="/login" className="hover:text-neutral-200 transition">
            Sign in
          </Link>
          <Link
            to="/register"
            className="px-4 py-2 rounded-md border border-neutral-700 hover:border-neutral-500 text-neutral-200 transition"
          >
            Get started
          </Link>
        </nav>
      </div>
    </header>
  );
};

export default Header;
