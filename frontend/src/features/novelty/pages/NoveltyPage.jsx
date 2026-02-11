import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import api from '../../../lib/api';

const NoveltyPage = () => {
  const { user } = useAuth();
  const [description, setDescription] = useState('');
  const [domain, setDomain] = useState('Software');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const domains = ['Software', 'Business', 'Social', 'Generic'];

  const handleCheckNovelty = async (e) => {
    e.preventDefault();
    
    if (!description.trim()) {
      setError('Please enter an idea description');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await api.post('/novelty/analyze', {
        description: description.trim(),
        domain: domain,
      });

      setResult(res.data);
    } catch (err) {
      console.error('Failed to analyze novelty:', err);
      setError(err.response?.data?.error || 'Failed to analyze novelty. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getNoveltyStyling = (level) => {
    const levelLower = level?.toLowerCase();
    switch (levelLower) {
      case 'very high':
        return 'bg-green-500/20 border-green-500/50 text-green-300';
      case 'high':
        return 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300';
      case 'medium':
        return 'bg-yellow-500/20 border-yellow-500/50 text-yellow-300';
      case 'low':
        return 'bg-orange-500/20 border-orange-500/50 text-orange-300';
      case 'very low':
        return 'bg-red-500/20 border-red-500/50 text-red-300';
      default:
        return 'bg-neutral-500/20 border-neutral-500/50 text-neutral-300';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-neutral-950 via-neutral-950 to-neutral-900">
      {/* Background decorations */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-600 rounded-full opacity-10 blur-3xl" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-purple-600 rounded-full opacity-10 blur-3xl" />
      </div>

      <div className="max-w-4xl mx-auto px-6 py-12 md:py-20 relative z-10">
        {/* Header */}
        <div className="mb-8">
          {user && (
            <Link to="/user/dashboard" className="text-indigo-400 hover:text-indigo-300 font-medium mb-4 inline-flex items-center gap-2 transition group">
              <span className="group-hover:-translate-x-1 transition-transform">←</span>
              Back to dashboard
            </Link>
          )}
          <h1 className="text-5xl font-light text-white mb-3">Check Novelty</h1>
          <p className="text-neutral-300">Analyze the novelty of any project idea with research-backed scoring</p>
        </div>

        {/* Main Container */}
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left: Form */}
          <div className="glass-card-lg p-8 border border-white/10">
            <form onSubmit={handleCheckNovelty} className="space-y-6">
              {/* Description Field */}
              <div>
                <label className="block text-sm font-medium text-white mb-3">
                  Idea Description
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe your project idea in detail. Be specific about what problem it solves and how it approaches the solution..."
                  rows={8}
                  className="glass-input w-full resize-none text-sm"
                />
                <p className="text-xs text-neutral-500 mt-2">
                  {description.length} characters
                </p>
              </div>

              {/* Domain Field */}
              <div>
                <label className="block text-sm font-medium text-white mb-3">
                  Domain
                </label>
                <select
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  className="glass-input w-full"
                >
                  {domains.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </div>

              {/* Error Message */}
              {error && (
                <div className="p-4 bg-red-500/20 border border-red-500/50 rounded-lg text-red-300 text-sm">
                  {error}
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Analyzing...
                  </span>
                ) : (
                  'Check Novelty'
                )}
              </button>
            </form>
          </div>

          {/* Right: Results */}
          <div className="space-y-6">
            {!result && !loading && !error && (
              <div className="glass-card-lg p-8 border border-white/10 text-center py-16">
                <div className="inline-block mb-4">
                  <div className="w-16 h-16 rounded-full bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-3xl">
                    🔍
                  </div>
                </div>
                <h3 className="text-lg font-light text-white mb-2">
                  Enter an idea to get started
                </h3>
                <p className="text-neutral-400 text-sm">
                  Fill in the form on the left to analyze your project's novelty with research-backed scoring
                </p>
              </div>
            )}

            {loading && (
              <div className="glass-card-lg p-8 border border-white/10 text-center py-16">
                <div className="inline-block mb-4">
                  <div className="w-12 h-12 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin" />
                </div>
                <p className="text-neutral-300">Analyzing novelty...</p>
              </div>
            )}

            {result && (
              <div className="space-y-4">
                {/* Novelty Score Card */}
                <div className="glass-card-lg p-6 border border-white/10">
                  <p className="text-xs text-neutral-400 uppercase tracking-widest font-semibold mb-3">
                    Novelty Score
                  </p>
                  <div className="flex items-end gap-4 mb-4">
                    <div className="text-5xl font-bold text-indigo-300">
                      {typeof result.novelty_score === 'number' ? result.novelty_score.toFixed(1) : 'N/A'}
                    </div>
                    <div className="flex-1">
                      <div className={`inline-block px-3 py-1 rounded-full border text-sm font-semibold ${getNoveltyStyling(result.novelty_level)}`}>
                        {result.novelty_level || 'N/A'}
                      </div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-neutral-500 text-xs">Confidence</p>
                      <p className="text-white font-medium capitalize">{result.confidence || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-neutral-500 text-xs">Domain Intent</p>
                      <p className="text-white font-medium capitalize">{result.domain_intent || 'N/A'}</p>
                    </div>
                  </div>
                </div>

                {/* Evidence Score */}
                <div className="glass-card-lg p-6 border border-white/10">
                  <p className="text-xs text-neutral-400 uppercase tracking-widest font-semibold mb-3">
                    Evidence Score
                  </p>
                  <div className="text-3xl font-bold text-purple-300">
                    {typeof result.evidence_score === 'number' ? (result.evidence_score * 100).toFixed(0) : 'N/A'}%
                  </div>
                  <p className="text-xs text-neutral-400 mt-2">
                    How well supported the idea is by evidence
                  </p>
                </div>

                {/* Explanation */}
                {result.insights && (
                  <div className="glass-card-lg p-6 border border-white/10">
                    <p className="text-xs text-neutral-400 uppercase tracking-widest font-semibold mb-3">
                      Key Insights
                    </p>
                    <div className="space-y-2 text-sm text-neutral-300">
                      {Object.entries(result.insights).map(([key, value]) => (
                        <div key={key}>
                          <p className="font-medium text-indigo-300 capitalize">{key.replace(/_/g, ' ')}:</p>
                          <p className="text-neutral-400 ml-2">{value}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Research Sources */}
                {result.sources && result.sources.length > 0 && (
                  <div className="glass-card-lg p-6 border border-white/10">
                    <p className="text-xs text-neutral-400 uppercase tracking-widest font-semibold mb-4">
                      Research Sources
                    </p>
                    <div className="space-y-4">
                      {/* arXiv Papers Section */}
                      {result.sources.filter(s => s.source_type === 'arxiv').slice(0, 5).length > 0 && (
                        <div>
                          <p className="text-xs font-semibold text-indigo-300 mb-2">📄 Research Papers</p>
                          <div className="space-y-2">
                            {result.sources.filter(s => s.source_type === 'arxiv').slice(0, 5).map((src, idx) => (
                              <div key={`arxiv-${idx}`} className="p-3 bg-indigo-500/10 rounded border border-indigo-500/20">
                                <a 
                                  href={src.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-indigo-300 hover:text-indigo-200 font-medium text-sm underline break-words"
                                >
                                  {src.title}
                                </a>
                                <span className="ml-2 text-xs px-2 py-0.5 bg-indigo-600/40 text-indigo-200 rounded font-semibold">
                                  ARXIV
                                </span>
                                {src.summary && (
                                  <p className="text-xs text-neutral-400 mt-2 line-clamp-2 leading-relaxed">
                                    {src.summary}
                                  </p>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* GitHub Repos Section */}
                      {result.sources.filter(s => s.source_type === 'github').slice(0, 5).length > 0 && (
                        <div>
                          <p className="text-xs font-semibold text-purple-300 mb-2">🔗 GitHub Repositories</p>
                          <div className="space-y-2">
                            {result.sources.filter(s => s.source_type === 'github').slice(0, 5).map((src, idx) => (
                              <div key={`github-${idx}`} className="p-3 bg-purple-500/10 rounded border border-purple-500/20">
                                <a 
                                  href={src.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-purple-300 hover:text-purple-200 font-medium text-sm underline break-words"
                                >
                                  {src.title}
                                </a>
                                <span className="ml-2 text-xs px-2 py-0.5 bg-purple-600/40 text-purple-200 rounded font-semibold">
                                  GITHUB
                                </span>
                                {src.summary && (
                                  <p className="text-xs text-neutral-400 mt-2 line-clamp-2 leading-relaxed">
                                    {src.summary}
                                  </p>
                                )}
                                {src.confidence && (
                                  <p className="text-xs text-neutral-500 mt-1">
                                    Confidence: {(src.confidence * 100).toFixed(0)}%
                                  </p>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Similar Projects */}
                {result.similar_projects && result.similar_projects.length > 0 && (
                  <div className="glass-card-lg p-6 border border-white/10">
                    <p className="text-xs text-neutral-400 uppercase tracking-widest font-semibold mb-4">
                      Similar Projects Found
                    </p>
                    <div className="space-y-3">
                      {result.similar_projects.slice(0, 5).map((proj, idx) => (
                        <div key={idx} className="p-3 bg-white/5 rounded border border-white/5">
                          <p className="text-sm text-white font-medium line-clamp-2">
                            {proj.title || proj.name || 'Untitled'}
                          </p>
                          {proj.similarity && (
                            <p className="text-xs text-neutral-400 mt-1">
                              Similarity: {(proj.similarity * 100).toFixed(0)}%
                            </p>
                          )}
                          {proj.source && (
                            <p className="text-xs text-indigo-400 mt-1">
                              Source: {proj.source}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Quick Links */}
        {user && (
          <div className="mt-12 pt-8 border-t border-white/10">
            <p className="text-sm text-neutral-400 mb-4">Explore more:</p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Link to="/user/my-ideas" className="text-indigo-400 hover:text-indigo-300 inline-flex items-center gap-2 transition">
                → View My Ideas
              </Link>
              <Link to="/user/generate" className="text-purple-400 hover:text-purple-300 inline-flex items-center gap-2 transition">
                → Generate New Idea
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default NoveltyPage;
