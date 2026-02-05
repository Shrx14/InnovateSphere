// src/app/dashboard/UserDashboard.jsx
import React, { useEffect, useState } from 'react';
import api from '../../shared/api';

const UserDashboard = () => {
  const [ideas, setIdeas] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/ideas/mine')
      .then(res => setIdeas(res.data.ideas || []))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-6 py-16">
      <h1 className="text-3xl font-light">
        Your ideas
      </h1>

      <p className="mt-2 text-sm text-neutral-400">
        Generated ideas and their review status.
      </p>

      {loading ? (
        <p className="mt-12 text-neutral-500 text-sm">
          Loading ideas…
        </p>
      ) : ideas.length === 0 ? (
        <p className="mt-12 text-neutral-500 text-sm">
          No ideas generated yet.
        </p>
      ) : (
        <div className="mt-12 space-y-6">
          {ideas.map((idea) => (
            <div
              key={idea.id}
              className="border border-neutral-800 rounded-xl p-6 bg-neutral-900"
            >
              <div className="flex justify-between items-start">
                <h2 className="text-lg font-medium text-neutral-100">
                  {idea.title}
                </h2>
                <span className="text-xs text-neutral-500">
                  {idea.admin_verdict || 'pending'}
                </span>
              </div>

              <p className="mt-3 text-sm text-neutral-400">
                Novelty score: {idea.novelty_score}%
              </p>

              <p className="mt-2 text-xs text-neutral-500">
                Domain: {idea.domain}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default UserDashboard;
