import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Mail, Lock, Eye, EyeOff, ArrowRight, Sparkles } from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';
import api from '../../../lib/api';

const LoginPage = () => {
  const { login } = useAuth();
  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (e) =>
    setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await api.post('/login', form);
      login(res.data.access_token, res.data.refresh_token);
    } catch (err) {
      setError(err.response?.data?.error || 'Unable to sign in. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-950/0 relative">
      <div className="relative z-10 flex items-center justify-center min-h-screen px-4">
        <div className="w-full max-w-md">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          >
            {/* Logo + Brand */}
            <div className="text-center mb-8">
              <Link to="/" className="inline-flex items-center gap-2 group mb-6">
                <motion.div
                  className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{
                    background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%)',
                  }}
                  whileHover={{ scale: 1.05, rotate: 5 }}
                >
                  <Sparkles className="w-5 h-5 text-white" />
                </motion.div>
                <span className="text-lg font-display font-semibold bg-gradient-to-r from-neutral-100 to-neutral-400 bg-clip-text text-transparent">
                  InnovateSphere
                </span>
              </Link>
              <h1 className="text-3xl md:text-4xl font-display font-bold text-white mb-2">
                Welcome back
              </h1>
              <p className="text-neutral-400">
                Sign in to continue building the future
              </p>
            </div>

            {/* Card */}
            <div className="relative">
              <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500/20 via-purple-500/20 to-indigo-500/20 rounded-2xl blur-xl" />
              <div className="relative bg-neutral-900/80 backdrop-blur-xl border border-neutral-800/50 rounded-2xl p-8 space-y-6">
                <form onSubmit={handleSubmit} className="space-y-5">
                  {/* Email */}
                  <div className="space-y-2">
                    <label className="block text-xs font-medium text-neutral-400 uppercase tracking-wider">
                      Email
                    </label>
                    <div className="relative group">
                      <div className="absolute -inset-[1px] rounded-xl opacity-0 group-focus-within:opacity-100 bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-500 blur-[1px] transition-opacity duration-300" />
                      <div className="relative">
                        <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500 group-focus-within:text-indigo-400 transition-colors z-10" />
                        <input
                          name="email"
                          type="email"
                          required
                          autoComplete="email"
                          value={form.email}
                          onChange={handleChange}
                          placeholder="you@example.com"
                          className="relative w-full rounded-xl bg-neutral-900/80 backdrop-blur-sm text-sm text-white border border-neutral-700/50 outline-none transition-all duration-300 placeholder:text-neutral-500 focus:border-indigo-500/50 focus:bg-neutral-900 focus:shadow-[0_0_20px_rgba(99,102,241,0.1)] pl-10 pr-4 py-3 h-12"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Password */}
                  <div className="space-y-2">
                    <label className="block text-xs font-medium text-neutral-400 uppercase tracking-wider">
                      Password
                    </label>
                    <div className="relative group">
                      <div className="absolute -inset-[1px] rounded-xl opacity-0 group-focus-within:opacity-100 bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-500 blur-[1px] transition-opacity duration-300" />
                      <div className="relative">
                        <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500 group-focus-within:text-indigo-400 transition-colors z-10" />
                        <input
                          name="password"
                          type={showPassword ? 'text' : 'password'}
                          required
                          autoComplete="current-password"
                          value={form.password}
                          onChange={handleChange}
                          placeholder="••••••••"
                          className="relative w-full rounded-xl bg-neutral-900/80 backdrop-blur-sm text-sm text-white border border-neutral-700/50 outline-none transition-all duration-300 placeholder:text-neutral-500 focus:border-indigo-500/50 focus:bg-neutral-900 focus:shadow-[0_0_20px_rgba(99,102,241,0.1)] pl-10 pr-12 py-3 h-12"
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-3.5 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-neutral-300 transition z-10"
                        >
                          {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Error */}
                  <AnimatePresence>
                    {error && (
                      <motion.div
                        initial={{ opacity: 0, y: -8, height: 0 }}
                        animate={{ opacity: 1, y: 0, height: 'auto' }}
                        exit={{ opacity: 0, y: -8, height: 0 }}
                        className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-300 text-sm"
                      >
                        {error}
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Submit */}
                  <motion.button
                    type="submit"
                    disabled={loading}
                    whileHover={{ scale: 1.01 }}
                    whileTap={{ scale: 0.99 }}
                    className="w-full h-12 rounded-xl text-sm font-semibold text-white relative overflow-hidden group transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    style={{
                      background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%)',
                    }}
                  >
                    <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity bg-gradient-to-r from-indigo-400 via-purple-400 to-indigo-400" />
                    <span className="relative flex items-center justify-center gap-2">
                      {loading ? (
                        <>
                          <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          Signing in...
                        </>
                      ) : (
                        <>
                          Sign in
                          <ArrowRight className="w-4 h-4" />
                        </>
                      )}
                    </span>
                  </motion.button>
                </form>

                {/* Divider */}
                <div className="flex items-center gap-4">
                  <div className="flex-1 h-px bg-gradient-to-r from-transparent via-neutral-700 to-transparent" />
                  <span className="text-xs text-neutral-500 uppercase tracking-wider">or</span>
                  <div className="flex-1 h-px bg-gradient-to-r from-transparent via-neutral-700 to-transparent" />
                </div>

                {/* Register Link */}
                <p className="text-center text-sm text-neutral-400">
                  Don't have an account?{' '}
                  <Link
                    to="/register"
                    className="text-indigo-400 hover:text-indigo-300 font-semibold transition"
                  >
                    Create one
                  </Link>
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
