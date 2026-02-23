import { Link } from "react-router-dom";

const Footer = () => {
    return (
        <footer className="border-t border-neutral-800/50 bg-neutral-950/50 backdrop-blur-sm">
            <div className="max-w-7xl mx-auto px-6 py-12">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
                    {/* Brand */}
                    <div>
                        <Link to="/" className="text-lg font-semibold text-white hover:text-indigo-300 transition">
                            InnovateSphere
                        </Link>
                        <p className="mt-3 text-sm text-neutral-400 leading-relaxed max-w-xs">
                            AI-powered project ideas evaluated with research evidence and real-time novelty scoring.
                        </p>
                    </div>

                    {/* Platform */}
                    <div>
                        <h4 className="text-xs font-semibold uppercase tracking-widest text-neutral-500 mb-4">
                            Platform
                        </h4>
                        <ul className="space-y-2 text-sm">
                            <li>
                                <Link to="/explore" className="text-neutral-400 hover:text-white transition">
                                    Explore Ideas
                                </Link>
                            </li>
                            <li>
                                <Link to="/register" className="text-neutral-400 hover:text-white transition">
                                    Get Started
                                </Link>
                            </li>
                            <li>
                                <Link to="/login" className="text-neutral-400 hover:text-white transition">
                                    Sign In
                                </Link>
                            </li>
                        </ul>
                    </div>

                    {/* About */}
                    <div>
                        <h4 className="text-xs font-semibold uppercase tracking-widest text-neutral-500 mb-4">
                            About
                        </h4>
                        <ul className="space-y-2 text-sm">
                            <li>
                                <span className="text-neutral-400">Research-backed evaluation</span>
                            </li>
                            <li>
                                <span className="text-neutral-400">Novelty & quality scoring</span>
                            </li>
                            <li>
                                <span className="text-neutral-400">Evidence-driven insights</span>
                            </li>
                        </ul>
                    </div>
                </div>

                {/* Bottom bar */}
                <div className="pt-8 border-t border-neutral-800/50 flex flex-col md:flex-row items-center justify-between gap-4">
                    <p className="text-xs text-neutral-500">
                        © {new Date().getFullYear()} InnovateSphere. All rights reserved.
                    </p>
                    <div className="flex items-center gap-1">
                        <span className="text-xs text-neutral-600">Built with</span>
                        <span className="text-xs text-red-400">♥</span>
                        <span className="text-xs text-neutral-600">for researchers</span>
                    </div>
                </div>
            </div>
        </footer>
    );
};

export default Footer;
