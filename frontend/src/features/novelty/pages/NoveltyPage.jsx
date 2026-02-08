import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import api from '../../../lib/api';

const NoveltyPage = () => {
  const { user } = useAuth();
  const [ideas, setIdeas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sortBy, setSortBy] = useState('novelty_desc');

  const handleLoadIdeas = async () => {
    if (!user) {
      alert('Please sign in to analyze idea novelty');
      return;
    }

    setLoading(true);
    try {
      const res = await api.get('/ideas/mine');
      const sortedIdeas = sortIdeas(res.data, sortBy);
      setIdeas(sortedIdeas);
    } catch (err) {
      console.error('Failed to load ideas:', err);
    } finally {
      setLoading(false);
    }
  };

  const sortIdeas = (ideas, sortType) => {
    const sorted = [...ideas];
    switch (sortType) {
      case 'novelty_desc':
        return sorted.sort((a, b) => (b.novelty_score || 0) - (a.novelty_score || 0));
      case 'novelty_asc':
        return sorted.sort((a, b) => (a.novelty_score || 0) - (b.novelty_score || 0));
      case 'quality_desc':
        return sorted.sort((a, b) => (b.quality_score || 0) - (a.quality_score || 0));
      case 'quality_asc':
        return sorted.sort((a, b) => (a.quality_score || 0) - (b.quality_score || 0));
      case 'recent':
        return sorted.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      default:
        return sorted;
    }
  };

  const handleSortChange = (newSort) => {
    setSortBy(newSort);
    setIdeas(sortIdeas(ideas, newSort));
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-neutral-950 via-neutral-950 to-neutral-900">
      {/* Background decorations */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-600 rounded-full opacity-10 blur-3xl" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-purple-600 rounded-full opacity-10 blur-3xl" />
      </div>

      <div className="max-w-6xl mx-auto px-6 py-12 md:py-20 relative z-10">
        {/* Header */}
        <div className="mb-8">
          <Link to="/user/dashboard" className="text-indigo-400 hover:text-indigo-300 font-medium mb-4 inline-flex items-center gap-2 transition group">
            <span className="group-hover:-translate-x-1 transition-transform">←</span>
            Back to dashboard
          </Link>
          <h1 className="text-5xl font-light text-white mb-3">Novelty Analysis</h1>
          <p className="text-neutral-300">Examine and compare the novelty of your ideas</p>
        </div>

        {/* Controls */}
        <div className="glass-card-lg p-6 border border-white/10 mb-8">
          <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
            <div className="flex-1">
              <label className="block text-sm font-medium text-neutral-300 mb-2">
                Sort by
              </label>
              <select
                value={sortBy}
                onChange={(e) => handleSortChange(e.target.value)}
                className="glass-input w-full md:w-48"
              >
                <option value="novelty_desc">Novelty (Highest)</option>
                <option value="novelty_asc">Novelty (Lowest)</option>
                <option value="quality_desc">Quality (Highest)</option>
                <option value="quality_asc">Quality (Lowest)</option>
                <option value="recent">Most Recent</option>
              </select>
            </div>

            <button
              onClick={handleLoadIdeas}
              disabled={loading || !user}
              className="btn-primary w-full md:w-auto"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Loading...
                </span>
              ) : (
                'Load My Ideas'
              )}
            </button>
          </div>

          {!user && (
            <div className="mt-4 p-3 bg-indigo-500/20 border border-indigo-500/50 rounded-lg text-indigo-200 text-sm">
              Sign in to analyze your ideas' novelty
            </div>
          )}
        </div>

        {/* Ideas Grid */}
        {ideas.length > 0 ? (
          <div className="space-y-4">
            {ideas.map((idea) => (
              <div key={idea.id} className="glass-card-lg p-6 border border-white/10 hover:border-indigo-500/50 transition group">
                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6">
                  {/* Left: Title & Description */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-xl font-semibold text-white truncate group-hover:text-indigo-300 transition">
                        {idea.title}
                      </h3>
                      <span className="inline-block px-2 py-1 bg-gradient-to-r from-indigo-500/20 to-purple-500/20 rounded text-xs font-semibold text-indigo-300 border border-indigo-500/30 flex-shrink-0">
                        {idea.domain}
                      </span>
                    </div>
                    <p className="text-neutral-400 text-sm line-clamp-2">
                      {idea.problem_statement}
                    </p>
                  </div>

                  {/* Right: Metrics */}
                  <div className="flex flex-col gap-3 md:items-end flex-shrink-0">
                    <div className="glass-card p-3 border border-white/10">
                      <div className="text-xs text-indigo-400 font-semibold uppercase tracking-widest mb-1">
                        Novelty Score
                      </div>
                      <div className="text-3xl font-bold text-indigo-300">
                        {typeof idea.novelty_score === 'number' ? (idea.novelty_score / 10).toFixed(1) : 'N/A'}
                      </div>
                      <div className="text-xs text-neutral-400 mt-1">
                        {idea.novelty_confidence || 'N/A'}
                      </div>
                    </div>

                    <div className="glass-card p-3 border border-white/10">
                      <div className="text-xs text-purple-400 font-semibold uppercase tracking-widest mb-1">
                        Quality Score
                      </div>
                      <div className="text-3xl font-bold text-purple-300">
                        {typeof idea.quality_score === 'number' ? (idea.quality_score / 10).toFixed(1) : 'N/A'}
                      </div>
                    </div>

                    {/* View Details Button */}
                    <Link
                      to={`/idea/${idea.id}`}
                      className="text-indigo-400 hover:text-indigo-300 font-medium text-sm transition inline-flex items-center gap-1"
                    >
                      View details →
                    </Link>
                  </div>
                </div>

                {/* Novelty Explanation */}
                {idea.novelty_explanation && (
                  <div className="mt-4 pt-4 border-t border-white/10">
                    <p className="text-sm text-neutral-300">
                      <span className="text-indigo-400 font-medium">Why novel: </span>
                      {idea.novelty_explanation}
                    </p>
                  </div>
                )}

                {/* Hallucination Risk */}
                {idea.hallucination_risk_level && (
                  <div className="mt-3 p-3 bg-yellow-500/5 border border-yellow-500/20 rounded">
                    <p className="text-xs text-yellow-300">
                      <span className="font-semibold">Hallucination Risk:</span> {idea.hallucination_risk_level}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <div className="inline-block mb-4">
              <div className="w-16 h-16 rounded-full bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-2xl">
                📊
              </div>
            </div>
            <h3 className="text-2xl font-light text-white mb-2">No ideas to analyze</h3>
            <p className="text-neutral-400 mb-6">
              {user
                ? 'Click "Load My Ideas" to see the novelty analysis of your generated ideas'
                : 'Sign in to analyze the novelty of your ideas'}
            </p>
            {!user && (
              <Link to="/login" className="btn-primary inline-flex">
                Sign in
              </Link>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default NoveltyPage;
