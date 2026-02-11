// src/features/auth/pages/RegisterPage.jsx
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import api from '../../../lib/api';

const RegisterPage = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', username: '', password: '', confirmPassword: '', skillLevel: 'beginner' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const handleChange = (e) =>
    setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    // Validate passwords match
    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);

    try {
      const res = await api.post('/register', {
        email: form.email,
        username: form.username,
        password: form.password,
        skill_level: form.skillLevel
      });
      login(res.data.access_token);
      navigate('/user/dashboard');
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden bg-neutral-950">
      {/* Animated Gradient Background with Blobs */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 opacity-20" />
        
        {/* Animated blobs */}
        <div className="absolute top-0 -left-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob" />
        <div className="absolute top-0 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob-delay-2" />
        <div className="absolute -bottom-8 left-20 w-80 h-80 bg-pink-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob-delay-4" />
      </div>

      {/* Content */}
      <div className="relative z-10 flex items-center justify-center min-h-screen px-4 py-8">
        <div className="w-full max-w-md">
          {/* Glass Card Container */}
          <div className="glass-card-lg p-8 space-y-6 max-w-md">
            {/* Header */}
            <div className="space-y-2">
              <h1 className="text-4xl font-bold text-white">
                Create account
              </h1>
              <p className="text-base text-neutral-300">
                Join InnovateSphere to start generating ideas
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Email Input */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-neutral-300">
                  Email
                </label>
                <input
                  name="email"
                  type="email"
                  required
                  value={form.email}
                  onChange={handleChange}
                  placeholder="your@email.com"
                  className="glass-input w-full"
                />
              </div>

              {/* Username Input */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-neutral-300">
                  Username
                </label>
                <input
                  name="username"
                  type="text"
                  required
                  value={form.username}
                  onChange={handleChange}
                  placeholder="your_username"
                  className="glass-input w-full"
                />
              </div>

              {/* Skill Level Select */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-neutral-300">
                  Skill Level
                </label>
                <select
                  name="skillLevel"
                  value={form.skillLevel}
                  onChange={handleChange}
                  className="glass-input w-full"
                >
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="advanced">Advanced</option>
                  <option value="expert">Expert</option>
                </select>
              </div>

              {/* Password Input */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-neutral-300">
                  Password
                </label>
                <div className="relative">
                  <input
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={form.password}
                    onChange={handleChange}
                    placeholder="••••••••"
                    className="glass-input w-full pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-300 transition"
                  >
                    {showPassword ? '✕' : '•••'}
                  </button>
                </div>
              </div>

              {/* Confirm Password Input */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-neutral-300">
                  Confirm Password
                </label>
                <div className="relative">
                  <input
                    name="confirmPassword"
                    type={showConfirm ? 'text' : 'password'}
                    required
                    value={form.confirmPassword}
                    onChange={handleChange}
                    placeholder="••••••••"
                    className="glass-input w-full pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirm(!showConfirm)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-300 transition"
                  >
                    {showConfirm ? '✕' : '•••'}
                  </button>
                </div>
              </div>

              {/* Error Message */}
              {error && (
                <div className="p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-200 text-sm animate-shake">
                  {error}
                </div>
              )}

              {/* Sign Up Button */}
              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full mt-6"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Creating account...
                  </span>
                ) : (
                  'Create account'
                )}
              </button>
            </form>

            {/* Divider */}
            <div className="flex items-center gap-4">
              <div className="flex-1 h-px bg-white/10" />
              <span className="text-sm text-neutral-400">or</span>
              <div className="flex-1 h-px bg-white/10" />
            </div>

            {/* Sign In Link */}
            <p className="text-center text-neutral-400">
              Already have an account?{' '}
              <Link
                to="/login"
                className="text-indigo-400 hover:text-indigo-300 font-semibold transition"
              >
                Sign in
              </Link>
            </p>
          </div>

          {/* Footer */}
          <div className="text-center mt-8 text-neutral-500 text-sm">
            <p>© 2026 InnovateSphere. All rights reserved.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
