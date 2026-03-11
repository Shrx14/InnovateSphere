import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { cn } from '@/lib/utils';
import ProfileDropdown from '@/components/ProfileDropdown';

const UserNav = () => {
  const { isAuthenticated, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const isActive = (path) => location.pathname === path;

  const navLinkClasses = (path) =>
    cn(
      'relative px-4 py-2 rounded-lg transition-all duration-200 text-sm',
      isActive(path)
        ? 'text-indigo-300 bg-indigo-500/10'
        : 'text-neutral-400 hover:text-neutral-100 hover:bg-white/5'
    );

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className={`sticky top-0 z-50 transition-all duration-300 ${scrolled
        ? 'bg-neutral-950/80 backdrop-blur-xl border-b border-neutral-800/60 shadow-lg shadow-black/20'
        : 'bg-transparent border-b border-transparent'
        }`}
    >
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        {/* Logo — same as public Header */}
        <Link to="/" className="group flex items-center gap-2">
          <motion.div
            className="w-7 h-7 rounded-lg flex items-center justify-center"
            style={{
              background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%)',
            }}
            whileHover={{ scale: 1.1, rotate: 5 }}
            transition={{ duration: 0.2 }}
          >
            <Sparkles className="w-4 h-4 text-white" />
          </motion.div>
          <span className="text-sm font-semibold tracking-wide bg-gradient-to-r from-neutral-100 to-neutral-400 bg-clip-text text-transparent group-hover:from-indigo-300 group-hover:to-purple-300 transition-all duration-300">
            InnovateSphere
          </span>
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
        <nav aria-label="User navigation" className="hidden md:block">
          <ul className="flex items-center gap-1 text-sm">
            <li>
              <Link to="/explore" className={navLinkClasses('/explore')}>
                Explore
                {isActive('/explore') && (
                  <motion.div
                    layoutId="user-nav-indicator"
                    className="absolute -bottom-[17px] left-2 right-2 h-[2px] bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                  />
                )}
              </Link>
            </li>
            {isAuthenticated ? (
              <>
                <li>
                  <Link to="/user/dashboard" className={navLinkClasses('/user/dashboard')}>
                    Dashboard
                    {isActive('/user/dashboard') && (
                      <motion.div
                        layoutId="user-nav-indicator"
                        className="absolute -bottom-[17px] left-2 right-2 h-[2px] bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                      />
                    )}
                  </Link>
                </li>
                <li>
                  <Link to="/user/generate" className={navLinkClasses('/user/generate')}>
                    Generate
                    {isActive('/user/generate') && (
                      <motion.div
                        layoutId="user-nav-indicator"
                        className="absolute -bottom-[17px] left-2 right-2 h-[2px] bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                      />
                    )}
                  </Link>
                </li>
                <li>
                  <Link to="/user/novelty" className={navLinkClasses('/user/novelty')}>
                    Novelty
                    {isActive('/user/novelty') && (
                      <motion.div
                        layoutId="user-nav-indicator"
                        className="absolute -bottom-[17px] left-2 right-2 h-[2px] bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                      />
                    )}
                  </Link>
                </li>
                <li>
                  <ProfileDropdown />
                </li>
              </>
            ) : (
              <>
                <li>
                  <Link to="/login" className={navLinkClasses('/login')}>Sign in</Link>
                </li>
                <li>
                  <Link
                    to="/register"
                    className="relative px-4 py-2 rounded-lg text-white font-medium overflow-hidden group transition-all duration-300"
                    style={{
                      background: 'linear-gradient(135deg, rgba(99,102,241,0.2) 0%, rgba(139,92,246,0.2) 100%)',
                      border: '1px solid rgba(99,102,241,0.3)',
                    }}
                  >
                    <span className="relative z-10">Get started</span>
                    <div
                      className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                      style={{
                        background: 'linear-gradient(135deg, rgba(99,102,241,0.35) 0%, rgba(139,92,246,0.35) 100%)',
                      }}
                    />
                  </Link>
                </li>
              </>
            )}
          </ul>
        </nav>
      </div>

      {/* Mobile nav dropdown */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.nav
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="md:hidden border-t border-neutral-800/60 bg-neutral-950/95 backdrop-blur-xl overflow-hidden"
            aria-label="Mobile user navigation"
          >
            <ul className="flex flex-col gap-1 px-6 py-4 text-sm">
              <li>
                <Link to="/explore" onClick={() => setMobileOpen(false)}
                  className={`block py-2.5 px-3 rounded-lg transition ${isActive('/explore') ? 'text-indigo-300 bg-indigo-500/10' : 'text-neutral-400 hover:text-neutral-200 hover:bg-white/5'}`}>
                  Explore
                </Link>
              </li>
              {isAuthenticated ? (
                <>
                  {[
                    { to: '/user/dashboard', label: 'Dashboard' },
                    { to: '/user/generate', label: 'Generate' },
                    { to: '/user/novelty', label: 'Novelty' },
                  ].map(({ to, label }) => (
                    <li key={to}>
                      <Link to={to} onClick={() => setMobileOpen(false)}
                        className={`block py-2.5 px-3 rounded-lg transition ${isActive(to) ? 'text-indigo-300 bg-indigo-500/10' : 'text-neutral-400 hover:text-neutral-200 hover:bg-white/5'}`}>
                        {label}
                      </Link>
                    </li>
                  ))}
                  <li>
                    <button onClick={() => { logout(); setMobileOpen(false); }}
                      className="block py-2.5 px-3 rounded-lg text-red-400 hover:text-red-300 hover:bg-white/5 transition w-full text-left">
                      Logout
                    </button>
                  </li>
                </>
              ) : (
                <>
                  <li><Link to="/login" onClick={() => setMobileOpen(false)} className="block py-2.5 px-3 rounded-lg text-neutral-400 hover:text-neutral-200 hover:bg-white/5 transition">Sign in</Link></li>
                  <li><Link to="/register" onClick={() => setMobileOpen(false)} className="block py-2.5 px-3 rounded-lg text-indigo-300 bg-indigo-500/10 transition">Get started</Link></li>
                </>
              )}
            </ul>
          </motion.nav>
        )}
      </AnimatePresence>
    </motion.header>
  );
};

export default UserNav;
