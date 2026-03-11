import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { User, LayoutDashboard, Sparkles, Search, Lightbulb, LogOut } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

const ProfileDropdown = () => {
    const { user, logout } = useAuth();
    const [open, setOpen] = useState(false);
    const dropdownRef = useRef(null);
    const navigate = useNavigate();

    // Close on click outside
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
                setOpen(false);
            }
        };
        if (open) {
            document.addEventListener('mousedown', handleClickOutside);
        }
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [open]);

    // Close on route change
    useEffect(() => {
        setOpen(false);
    }, [navigate]);

    const initial = user?.email ? user.email.charAt(0).toUpperCase() : '?';

    const menuItems = [
        { to: '/user/dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { to: '/user/generate', label: 'Generate', icon: Sparkles },
        { to: '/user/novelty', label: 'Novelty', icon: Search },
        { to: '/user/my-ideas', label: 'My Ideas', icon: Lightbulb },
    ];

    return (
        <div className="relative" ref={dropdownRef}>
            {/* Avatar trigger */}
            <button
                onClick={() => setOpen((prev) => !prev)}
                className="flex items-center justify-center w-9 h-9 rounded-full text-white text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:ring-offset-2 dark:focus:ring-offset-neutral-950 focus:ring-offset-white transition-transform duration-200 hover:scale-105"
                style={{
                    background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%)',
                }}
                aria-haspopup="true"
                aria-expanded={open}
                aria-label="Profile menu"
            >
                {initial}
            </button>

            {/* Dropdown menu */}
            <AnimatePresence>
                {open && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: -4 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: -4 }}
                        transition={{ duration: 0.15, ease: 'easeOut' }}
                        className="absolute right-0 mt-2 w-64 rounded-xl overflow-hidden shadow-xl shadow-black/40 border border-neutral-800 dark:bg-neutral-900 bg-white z-[100]"
                    >
                        {/* User info header */}
                        <div className="px-4 py-3 border-b border-neutral-800
                            <div className="flex items-center gap-3">
                                <div
                                    className="flex items-center justify-center w-10 h-10 rounded-full text-white text-sm font-semibold shrink-0"
                                    style={{
                                        background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%)',
                                    }}
                                >
                                    {initial}
                                </div>
                                <div className="min-w-0">
                                    <p className="text-sm font-medium text-neutral-100 truncate">
                                        {user?.email || 'User'}
                                    </p>
                                    <p className="text-xs text-neutral-500 capitalize">
                                        {user?.role || 'member'}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Navigation items */}
                        <div className="py-1.5">
                            {menuItems.map(({ to, label, icon: Icon }) => (
                                <Link
                                    key={to}
                                    to={to}
                                    onClick={() => setOpen(false)}
                                    className="flex items-center gap-3 px-4 py-2.5 text-sm text-neutral-300 hover:text-white hover:bg-white/5 transition-colors duration-150"
                                >
                                    <Icon className="w-4 h-4 text-neutral-500 />
                                    {label}
                                </Link>
                            ))}
                        </div>

                        {/* Logout */}
                        <div className="border-t border-neutral-800 py-1.5">
                            <button
                                onClick={() => {
                                    setOpen(false);
                                    logout();
                                }}
                                className="flex items-center gap-3 w-full px-4 py-2.5 text-sm text-red-400 hover:text-red-300 hover:bg-white/5 transition-colors duration-150"
                            >
                                <LogOut className="w-4 h-4" />
                                Logout
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default ProfileDropdown;
