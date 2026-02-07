// src/features/auth/pages/RegisterPage.jsx
import React from 'react';
import { Link } from 'react-router-dom';

const RegisterPage = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-950 px-6">
      <div className="w-full max-w-md border border-neutral-800 bg-neutral-900 rounded-xl p-8 text-center">
        <h1 className="text-2xl font-medium text-neutral-100">
          Create an account
        </h1>

        <p className="mt-4 text-sm text-neutral-400">
          Account creation is currently limited while we finalize
          quality and review safeguards.
        </p>

        <div className="mt-8">
          <Link
            to="/login"
            className="inline-block rounded-md bg-neutral-100 text-neutral-900 px-6 py-2 font-medium hover:bg-white transition"
          >
            Sign in instead
          </Link>
        </div>

        <p className="mt-6 text-xs text-neutral-500">
          This helps maintain research integrity and output quality.
        </p>
      </div>
    </div>
  );
};

export default RegisterPage;
