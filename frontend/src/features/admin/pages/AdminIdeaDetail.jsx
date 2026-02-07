import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../../lib/api';

const AdminIdeaDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [idea, setIdea] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [verdict, setVerdict] = useState('');
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchIdea = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get(`/api/admin/ideas/${id}`);
      setIdea(response.data);
    } catch (err) {
      console.error('Failed to fetch idea:', err);
      setError('Failed to load idea details.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchIdea();
  }, [fetchIdea]);

  const handleVerdict = async () => {
    if (!verdict) return;
    if (verdict === 'rejected' && !reason.trim()) {
      setError('Reason is required for rejection.');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await api.post(`/api/admin/ideas/${id}/verdict`, { verdict, reason: reason.trim() });
      // Navigate back to review queue
      navigate('/admin');
    } catch (err) {
      console.error('Failed to submit verdict:', err);
      setError('Failed to submit verdict.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="text-center text-neutral-400">Loading idea details...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="text-center text-red-400">{error}</div>
      </div>
    );
  }

  if (!idea) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="text-center text-neutral-400">Idea not found.</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate('/admin')}
          className="text-neutral-400 hover:text-white mb-4 inline-flex items-center"
        >
          ← Back to review queue
        </button>
        <h1 className="text-4xl font-light text-white">{idea.title}</h1>
        <p className="mt-2 text-neutral-400">
          Domain: {idea.domain} • Created: {new Date(idea.created_at).toLocaleDateString()}
        </p>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column - Idea Details */}
        <div className="lg:col-span-2 space-y-8">
          {/* Problem Statement */}
          <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-6">
            <h2 className="text-xl font-medium text-white mb-4">Problem Statement</h2>
            <p className="text-neutral-300 leading-relaxed">{idea.problem_statement}</p>
          </div>

          {/* Tech Stack */}
          <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-6">
            <h2 className="text-xl font-medium text-white mb-4">Tech Stack</h2>
            <p className="text-neutral-300">{idea.tech_stack}</p>
          </div>

          {/* Full Evidence List */}
          <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-6">
            <h2 className="text-xl font-medium text-white mb-4">Evidence Sources ({idea.sources.length})</h2>
            {idea.sources.length > 0 ? (
              <div className="space-y-4">
                {idea.sources.map((source, index) => (
                  <div key={index} className="border border-neutral-700 rounded p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="text-white font-medium">{source.title}</h3>
                        <p className="text-neutral-400 text-sm mt-1">{source.source_type}</p>
                        {source.summary && (
                          <p className="text-neutral-300 text-sm mt-2">{source.summary}</p>
                        )}
                      </div>
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 text-sm ml-4"
                      >
                        View →
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-neutral-400">No sources available.</p>
            )}
          </div>

          {/* Feedback History */}
          <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-6">
            <h2 className="text-xl font-medium text-white mb-4">Feedback History ({idea.feedback_history.length})</h2>
            {idea.feedback_history.length > 0 ? (
              <div className="space-y-3">
                {idea.feedback_history.map((feedback) => (
                  <div key={feedback.id} className="border border-neutral-700 rounded p-3">
                    <div className="flex items-center justify-between">
                      <span className="text-white font-medium capitalize">
                        {feedback.feedback_type.replace('_', ' ')}
                      </span>
                      <span className="text-neutral-400 text-sm">
                        {new Date(feedback.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    {feedback.comment && (
                      <p className="text-neutral-300 text-sm mt-2">{feedback.comment}</p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-neutral-400">No feedback yet.</p>
            )}
          </div>
        </div>

        {/* Right Column - Trust Signals & Verdict Panel */}
        <div className="space-y-6">
          {/* Trust Signals */}
          <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-6">
            <h2 className="text-xl font-medium text-white mb-4">Trust Signals</h2>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-neutral-300">Quality Score</span>
                <span className="text-white font-medium">{idea.quality_score}/100</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral-300">Novelty Confidence</span>
                <span className="text-white font-medium capitalize">{idea.novelty_confidence}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral-300">Evidence Strength</span>
                <span className="text-white font-medium capitalize">{idea.evidence_strength}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral-300">Hallucination Risk</span>
                <span className={`font-medium capitalize ${
                  idea.hallucination_risk_level === 'high' ? 'text-red-400' :
                  idea.hallucination_risk_level === 'medium' ? 'text-yellow-400' : 'text-green-400'
                }`}>
                  {idea.hallucination_risk_level}
                </span>
              </div>
              {idea.admin_verdict && (
                <div className="flex justify-between">
                  <span className="text-neutral-300">Current Verdict</span>
                  <span className={`font-medium capitalize ${
                    idea.admin_verdict === 'validated' ? 'text-green-400' :
                    idea.admin_verdict === 'rejected' ? 'text-red-400' : 'text-yellow-400'
                  }`}>
                    {idea.admin_verdict}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Verdict Action Panel */}
          {!idea.admin_verdict && (
            <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-6">
              <h2 className="text-xl font-medium text-white mb-4">Admin Verdict</h2>

              {error && (
                <div className="mb-4 text-sm text-red-400">
                  {error}
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-neutral-300 mb-2">
                    Verdict <span className="text-red-400">*</span>
                  </label>
                  <div className="space-y-2">
                    <button
                      onClick={() => setVerdict('validated')}
                      className={`w-full p-3 rounded border text-left transition-colors ${
                        verdict === 'validated'
                          ? 'border-green-500 bg-green-500/10 text-green-400'
                          : 'border-neutral-600 hover:border-green-500 text-neutral-300'
                      }`}
                    >
                      ✅ Validate - Publish this idea
                    </button>
                    <button
                      onClick={() => setVerdict('downgraded')}
                      className={`w-full p-3 rounded border text-left transition-colors ${
                        verdict === 'downgraded'
                          ? 'border-yellow-500 bg-yellow-500/10 text-yellow-400'
                          : 'border-neutral-600 hover:border-yellow-500 text-neutral-300'
                      }`}
                    >
                      ⚠️ Downgrade - Keep but flag for improvement
                    </button>
                    <button
                      onClick={() => setVerdict('rejected')}
                      className={`w-full p-3 rounded border text-left transition-colors ${
                        verdict === 'rejected'
                          ? 'border-red-500 bg-red-500/10 text-red-400'
                          : 'border-neutral-600 hover:border-red-500 text-neutral-300'
                      }`}
                    >
                      ❌ Reject - Remove from platform
                    </button>
                  </div>
                </div>

                {verdict === 'rejected' && (
                  <div>
                    <label className="block text-sm font-medium text-neutral-300 mb-2">
                      Reason for Rejection <span className="text-red-400">*</span>
                    </label>
                    <textarea
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                      placeholder="Please provide a detailed reason for rejection..."
                      className="w-full h-24 bg-neutral-800 border border-neutral-600 rounded px-3 py-2 text-white placeholder-neutral-400 focus:border-red-500 focus:outline-none"
                      required
                    />
                  </div>
                )}

                <button
                  onClick={handleVerdict}
                  disabled={submitting || !verdict}
                  className="w-full bg-white text-black font-medium py-3 px-4 rounded hover:bg-neutral-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {submitting ? 'Submitting...' : 'Submit Verdict'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminIdeaDetail;
