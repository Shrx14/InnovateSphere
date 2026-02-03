import React, { useEffect, useState } from 'react';
import api from '../../shared/api';

const ReviewQueue = () => {
  const [ideas, setIdeas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(new Set()); // Track processing ideas by ID
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchIdeas();
  }, []);

  const fetchIdeas = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/api/admin/ideas/quality-review');
      setIdeas(response.data || []);
    } catch (error) {
      console.error('Failed to fetch review queue:', error);
      setError('Failed to load review queue. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerdict = async (ideaId, verdict) => {
    setProcessing(prev => new Set(prev).add(ideaId));
    try {
      setError(null);
      await api.post(`/api/admin/ideas/${ideaId}/verdict`, { verdict });
      // Optimistically remove from list
      setIdeas(prev => prev.filter(idea => idea.id !== ideaId));
    } catch (error) {
      console.error('Failed to submit verdict:', error);
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
    const flags = [];
    if (feedback.hallucinated_source > 0) flags.push(`Hallucinated source: ${feedback.hallucinated_source}`);
    if (feedback.weak_novelty > 0) flags.push(`Weak novelty: ${feedback.weak_novelty}`);
    if (feedback.hallucinated_source >= 3) flags.push('High hallucination risk');
    if (feedback.weak_novelty >= 2) flags.push('High novelty weakness'); // Assuming similar threshold
    return flags.length > 0 ? flags.join(', ') : 'None';
  };

  const getRiskColor = (riskLevel) => {
    const riskColor = {
      Low: 'text-green-400',
      Medium: 'text-yellow-400',
      High: 'text-red-400'
    }[riskLevel] || 'text-neutral-400';
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
        <h1 className="text-4xl font-light text-white">Admin review queue</h1>
        <p className="mt-2 text-neutral-400">
          Review generated ideas for quality and novelty before publication.
        </p>
      </div>

      {/* Loading */}
      {UI_STATE === 'loading' && (
        <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-8 text-center">
          <p className="text-neutral-400">Loading review queue...</p>
        </div>
      )}

      {/* Empty */}
      {UI_STATE === 'empty' && (
        <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-8 text-center">
          <h2 className="text-xl font-medium text-white mb-2">No ideas pending review</h2>
          <p className="text-neutral-400">All ideas have been reviewed or none are available.</p>
        </div>
      )}

      {/* Populated */}
      {UI_STATE === 'populated' && (
        <div className="rounded-lg border border-neutral-800 bg-neutral-900 overflow-hidden">
          <table className="w-full">
            <thead className="bg-neutral-800">
              <tr>
                <th className="px-6 py-4 text-left text-sm font-medium text-neutral-300">Title</th>
                <th className="px-6 py-4 text-left text-sm font-medium text-neutral-300">Domain</th>
                <th className="px-6 py-4 text-left text-sm font-medium text-neutral-300">Novelty %</th>
                <th className="px-6 py-4 text-left text-sm font-medium text-neutral-300">Quality score</th>
                <th className="px-6 py-4 text-left text-sm font-medium text-neutral-300">Hallucination risk</th>
                <th className="px-6 py-4 text-left text-sm font-medium text-neutral-300">Feedback flags</th>
                <th className="px-6 py-4 text-left text-sm font-medium text-neutral-300">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800">
              {ideas.map((idea) => (
                <tr key={idea.id} className="hover:bg-neutral-800/50">
                  <td className="px-6 py-4 text-sm text-white">{idea.title}</td>
                  <td className="px-6 py-4 text-sm text-neutral-300">{idea.domain}</td>
                  <td className="px-6 py-4 text-sm text-neutral-300">{idea.novelty_score.toFixed(1)}%</td>
                  <td className="px-6 py-4 text-sm text-neutral-300">{idea.quality_score}</td>
                  <td className={`px-6 py-4 text-sm ${getRiskColor(idea.hallucination_risk_level)}`}>{idea.hallucination_risk_level}</td>
                  <td className="px-6 py-4 text-sm text-neutral-300">{formatFeedbackFlags(idea.feedback_summary)}</td>
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
        </div>
      )}
    </div>
  );
};

export default ReviewQueue;
