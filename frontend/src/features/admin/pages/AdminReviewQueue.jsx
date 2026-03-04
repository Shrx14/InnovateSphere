import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import api from '../../../lib/api';
import { formatScore } from '@/lib/formatScore';

const AdminReviewQueue = () => {
  const [ideas, setIdeas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(new Set()); // Track processing ideas by ID
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [meta, setMeta] = useState({ page: 1, pages: 1, total: 0, limit: 20 });

  const fetchIdeas = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get(`/admin/ideas/quality-review?page=${page}&limit=20`);
      const data = response.data;
      setIdeas(data.ideas || []);
      if (data.meta) setMeta(data.meta);
    } catch (error) {
      console.error('Failed to fetch review queue:', error);
      setError('Failed to load review queue. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    fetchIdeas();
  }, [fetchIdeas]);

  const handleVerdict = async (ideaId, verdict) => {
    let reason = 'Admin verdict';
    if (verdict === 'rejected') {
      reason = window.prompt('Please provide a reason for rejection:');
      if (!reason || !reason.trim()) return; // User cancelled or empty reason
      reason = reason.trim();
    }
    setProcessing(prev => new Set(prev).add(ideaId));
    try {
      setError(null);
      await api.post(`/admin/ideas/${ideaId}/verdict`, { verdict, reason });
      // Optimistically remove from list
      setIdeas(prev => prev.filter(idea => idea.id !== ideaId));
    } catch (err) {
      console.error('Failed to submit verdict:', err);
      setError('Failed to submit verdict. Please try again.');
    } finally {
      setProcessing(prev => {
        const newSet = new Set(prev);
        newSet.delete(ideaId);
        return newSet;
      });
    }
  };

  const formatFeedbackFlags = (feedback) => {
    if (!feedback || typeof feedback !== 'object') return 'None';
    const flags = Object.entries(feedback)
      .filter(([, count]) => count > 0)
      .map(([type, count]) => `${type.replace(/_/g, ' ')}: ${count}`);
    return flags.length > 0 ? flags.join(', ') : 'None';
  };

  const getRiskColor = (riskLevel) => {
    const riskColor = {
      Low: 'text-green-400',
      Medium: 'text-yellow-400',
      High: 'text-red-400'
    }[riskLevel] || 'dark:text-neutral-400 text-neutral-500';
    return riskColor;
  };

  const UI_STATE = loading
    ? 'loading'
    : ideas.length === 0
    ? 'empty'
    : 'populated';

  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      {/* Error Display */}
      {error && (
        <div className="mb-4 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-light dark:text-white text-neutral-900">Admin review queue</h1>
        <p className="mt-2 dark:text-neutral-400 text-neutral-500">
          Review generated ideas for quality and novelty before publication.
        </p>
      </div>

      {/* Loading */}
      {UI_STATE === 'loading' && (
        <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-8 text-center">
          <p className="dark:text-neutral-400 text-neutral-500">Loading review queue...</p>
        </div>
      )}

      {/* Empty */}
      {UI_STATE === 'empty' && (
        <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-8 text-center">
          <h2 className="text-xl font-medium dark:text-white text-neutral-900 mb-2">No ideas pending review</h2>
          <p className="dark:text-neutral-400 text-neutral-500">All ideas have been reviewed or none are available.</p>
        </div>
      )}

      {/* Populated */}
      {UI_STATE === 'populated' && (
        <div className="rounded-lg border border-neutral-800 bg-neutral-900 overflow-hidden">
          <table className="w-full">
            <thead className="dark:bg-neutral-800 bg-neutral-100">
              <tr>
                <th scope="col" className="px-6 py-4 text-left text-sm font-medium dark:text-neutral-300 text-neutral-600">Title</th>
                <th scope="col" className="px-6 py-4 text-left text-sm font-medium dark:text-neutral-300 text-neutral-600">Domain</th>
                <th scope="col" className="px-6 py-4 text-left text-sm font-medium dark:text-neutral-300 text-neutral-600">Novelty</th>
                <th scope="col" className="px-6 py-4 text-left text-sm font-medium dark:text-neutral-300 text-neutral-600">Quality</th>
                <th scope="col" className="px-6 py-4 text-left text-sm font-medium dark:text-neutral-300 text-neutral-600">Risk</th>
                <th scope="col" className="px-6 py-4 text-left text-sm font-medium dark:text-neutral-300 text-neutral-600">Flags</th>
                <th scope="col" className="px-6 py-4 text-left text-sm font-medium dark:text-neutral-300 text-neutral-600">Details</th>
                <th scope="col" className="px-6 py-4 text-left text-sm font-medium dark:text-neutral-300 text-neutral-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800">
              {ideas.map((idea) => (
                <tr key={idea.id} className="dark:hover:bg-neutral-800/50 bg-neutral-100">
                  <td className="px-6 py-4 text-sm dark:text-white text-neutral-900">{idea.title}</td>
                  <td className="px-6 py-4 text-sm dark:text-neutral-300 text-neutral-600">{idea.domain}</td>
                  <td className="px-6 py-4 text-sm dark:text-neutral-300 text-neutral-600">{formatScore(idea.novelty_score)}</td>
                  <td className="px-6 py-4 text-sm dark:text-neutral-300 text-neutral-600">{formatScore(idea.quality_score)}</td>
                  <td className={`px-6 py-4 text-sm ${getRiskColor(idea.hallucination_risk_level)}`}>{idea.hallucination_risk_level}</td>
                  <td className="px-6 py-4 text-sm dark:text-neutral-300 text-neutral-600">{formatFeedbackFlags(idea.feedback_summary)}</td>
                  <td className="px-6 py-4">
                    <Link
                      to={`/admin/idea/${idea.id}`}
                      className="text-blue-400 hover:text-blue-300 text-sm font-medium"
                    >
                      View Details →
                    </Link>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleVerdict(idea.id, 'validated')}
                        disabled={processing.has(idea.id)}
                        className="text-green-400 hover:text-green-300 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {processing.has(idea.id) ? 'Processing...' : 'Validate'}
                      </button>
                      <button
                        onClick={() => handleVerdict(idea.id, 'downgraded')}
                        disabled={processing.has(idea.id)}
                        className="text-yellow-400 hover:text-yellow-300 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {processing.has(idea.id) ? 'Processing...' : 'Downgrade'}
                      </button>
                      <button
                        onClick={() => handleVerdict(idea.id, 'rejected')}
                        disabled={processing.has(idea.id)}
                        className="text-red-400 hover:text-red-300 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {processing.has(idea.id) ? 'Processing...' : 'Reject'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination */}
          {meta.pages > 1 && (
            <div className="flex items-center justify-between px-6 py-4 border-t border-neutral-800 bg-neutral-900/50">
              <span className="text-sm dark:text-neutral-400 text-neutral-500">
                Showing {ideas.length} of {meta.total} ideas (Page {meta.page} of {meta.pages})
              </span>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1 text-sm rounded border border-neutral-700 dark:text-neutral-300 text-neutral-600 hover:border-white dark:hover:text-white text-neutral-900 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  ← Previous
                </button>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={page >= meta.pages}
                  className="px-3 py-1 text-sm rounded border border-neutral-700 dark:text-neutral-300 text-neutral-600 hover:border-white dark:hover:text-white text-neutral-900 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  Next →
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AdminReviewQueue;
