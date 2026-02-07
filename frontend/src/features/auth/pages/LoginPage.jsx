// src/features/auth/pages/LoginPage.jsx
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import api from '../../../lib/api';

const LoginPage = () => {
  const { login } = useAuth();
  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) =>
    setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await api.post('/login', form);
      login(res.data.access_token);
    } catch (err) {
      setError(err.response?.data?.error || 'Unable to sign in');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-950 px-6">
      <div className="w-full max-w-md border border-neutral-800 bg-neutral-900 rounded-xl p-8">
        <h1 className="text-2xl font-medium text-neutral-100">
          Sign in
        </h1>
        <p className="mt-2 text-sm text-neutral-400">
          Access your ideas and analysis.
        </p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          <div>
            <label className="block text-sm text-neutral-400 mb-2">
              Email
            </label>
            <input
              name="email"
              type="email"
              required
              value={form.email}
              onChange={handleChange}
              className="w-full rounded-md bg-neutral-950 border border-neutral-800 px-3 py-2 text-neutral-200 focus:outline-none focus:border-neutral-600"
            />
          </div>

          <div>
            <label className="block text-sm text-neutral-400 mb-2">
              Password
            </label>
            <input
              name="password"
              type="password"
              required
              value={form.password}
              onChange={handleChange}
              className="w-full rounded-md bg-neutral-950 border border-neutral-800 px-3 py-2 text-neutral-200 focus:outline-none focus:border-neutral-600"
            />
          </div>

          {error && (
            <div className="text-sm text-red-400">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-neutral-100 text-neutral-900 py-2 font-medium hover:bg-white transition disabled:opacity-50"
          >
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <p className="mt-6 text-sm text-neutral-400 text-center">
          New here?{' '}
          <Link to="/register" className="text-neutral-200 hover:underline">
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
