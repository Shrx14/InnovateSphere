import React from 'react';
import { Link } from 'react-router-dom';

const AdminNav = () => {
  return (
    <header className="sticky top-0 z-50 bg-neutral-950/70 backdrop-blur border-b border-neutral-800">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link
          to="/admin"
          className="text-sm font-semibold tracking-wide text-neutral-200 hover:text-neutral-100 transition"
        >
          Admin Panel
        </Link>

        <nav aria-label="Admin navigation">
          <ul className="flex items-center gap-6 text-sm text-neutral-400">
            <li>
              <Link to="/admin/review" className="hover:text-neutral-200 transition">
                Review Queue
              </Link>
            </li>
            <li>
              <Link to="/" className="hover:text-neutral-200 transition">
                Back to Site
              </Link>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  );
};

export default AdminNav;
