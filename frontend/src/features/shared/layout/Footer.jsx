import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, ArrowUp, Github, Sun, Moon } from 'lucide-react';
import { useTheme } from '@/context/ThemeContext';

const footerLinks = {
    Product: [
        { label: 'Home', to: '/' },
        { label: 'Explore Ideas', to: '/explore' },
        { label: 'How It Works', to: '/how-it-works' },
        { label: 'Get Started', to: '/register' },
    ],
    Company: [
        { label: 'About Us', to: '/about' },
        { label: 'Contact', to: '/contact' },
    ],
    Legal: [
        { label: 'Privacy Policy', to: '/privacy' },
        { label: 'Terms of Service', to: '/terms' },
    ],
};

const teamGithubs = [
    { name: 'Shreyas S', url: 'https://github.com/Shrx14' },
    { name: 'Bethuel S', url: 'https://github.com/Bethuel-Shilesh' },
    { name: 'Vedant P', url: 'https://github.com/VedantPatil22' },
];

const Footer = ({ hideGetStarted = false }) => {
    const { theme, toggleTheme } = useTheme();
    const scrollToTop = () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    return (
        <footer className="relative z-10 border-t dark:border-neutral-800/60 border-neutral-200">
            <div className="max-w-7xl mx-auto px-6 pt-16 pb-8">
                {/* Main grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-12 mb-16">
                    {/* Brand column */}
                    <div className="lg:col-span-4">
                        <Link to="/" className="inline-flex items-center gap-2 group mb-4">
                            <div
                                className="w-8 h-8 rounded-lg flex items-center justify-center"
                                style={{
                                    background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%)',
                                }}
                            >
                                <Sparkles className="w-4 h-4 dark:text-white text-neutral-900" />
                            </div>
                            <span className="text-base font-display font-semibold bg-gradient-to-r dark:from-neutral-100 dark:to-neutral-400 from-neutral-800 to-neutral-500 bg-clip-text text-transparent">
                                InnovateSphere
                            </span>
                        </Link>
                        <p className="text-sm dark:text-neutral-400 text-neutral-500 leading-relaxed max-w-xs mb-6">
                            AI-powered research idea generation with real-time novelty scoring and evidence-based evaluation.
                        </p>

                        {/* Team GitHub links */}
                        <div className="flex items-center gap-3">
                            {teamGithubs.map((member) => (
                                <a
                                    key={member.name}
                                    href={member.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    title={member.name}
                                    className="w-8 h-8 rounded-lg dark:bg-neutral-800/60 bg-neutral-100 border dark:border-neutral-700/40 border-neutral-200 flex items-center justify-center dark:text-neutral-400 text-neutral-500 hover:text-indigo-500 dark:hover:text-white text-neutral-900 hover:border-indigo-500/40 dark:hover:bg-indigo-500/10 hover:bg-indigo-50 transition-all duration-200"
                                >
                                    <Github className="w-4 h-4" />
                                </a>
                            ))}
                        </div>
                    </div>

                    {/* Link columns */}
                    {Object.entries(footerLinks).map(([category, links]) => (
                        <div key={category} className="lg:col-span-2">
                            <h4 className="text-xs uppercase tracking-widest dark:text-neutral-300 text-neutral-600 font-semibold mb-4">
                                {category}
                            </h4>
                            <ul className="space-y-3">
                                {links
                                    .filter((link) => !(hideGetStarted && link.label === 'Get Started'))
                                    .map((link) => (
                                        <li key={link.to}>
                                            <Link
                                                to={link.to}
                                                className="text-sm dark:text-neutral-400 text-neutral-500 hover:text-indigo-500 dark:hover:text-indigo-300 transition-colors duration-200"
                                            >
                                                {link.label}
                                            </Link>
                                        </li>
                                    ))}
                            </ul>
                        </div>
                    ))}

                    {/* Actions */}
                    <div className="lg:col-span-2 flex lg:flex-col lg:items-end items-start gap-3">
                        {/* Theme toggle */}
                        <motion.button
                            onClick={toggleTheme}
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border dark:border-neutral-700/40 border-neutral-300 dark:bg-neutral-800/40 bg-neutral-100 dark:text-neutral-400 text-neutral-600 hover:text-indigo-500 dark:hover:text-white text-neutral-900 dark:hover:border-indigo-500/40 hover:border-indigo-400 dark:hover:bg-indigo-500/10 hover:bg-indigo-50 transition-all duration-200 text-sm"
                            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
                        >
                            {theme === 'dark' ? (
                                <><Sun className="w-4 h-4" /> Light mode</>
                            ) : (
                                <><Moon className="w-4 h-4" /> Dark mode</>
                            )}
                        </motion.button>

                        {/* Back to top */}
                        <motion.button
                            onClick={scrollToTop}
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border dark:border-neutral-700/40 border-neutral-300 dark:bg-neutral-800/40 bg-neutral-100 dark:text-neutral-400 text-neutral-600 hover:text-indigo-500 dark:hover:text-white text-neutral-900 dark:hover:border-indigo-500/40 hover:border-indigo-400 dark:hover:bg-indigo-500/10 hover:bg-indigo-50 transition-all duration-200 text-sm"
                        >
                            <ArrowUp className="w-4 h-4" />
                            Back to top
                        </motion.button>
                    </div>
                </div>

                {/* Bottom bar */}
                <div className="border-t dark:border-neutral-800/60 border-neutral-200 pt-6 flex flex-col md:flex-row justify-between items-center gap-4">
                    <p className="text-xs dark:text-neutral-500 text-neutral-400 text-neutral-500">
                        © {new Date().getFullYear()} InnovateSphere. All rights reserved.
                    </p>
                    <p className="text-xs dark:text-neutral-600 dark:text-neutral-400 text-neutral-500">
                        Built with purpose by Shreyas, Bethuel & Vedant
                    </p>
                </div>
            </div>
        </footer>
    );
};

export default Footer;
