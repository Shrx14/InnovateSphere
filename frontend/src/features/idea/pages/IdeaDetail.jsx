import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import api from '../../../lib/api';
import SourcesList from '../../novelty/components/SourcesList';

const StarRating = ({ value, onChange, disabled }) => {
  const [hover, setHover] = useState(0);
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          disabled={disabled}
          onClick={() => onChange(star)}
          onMouseEnter={() => setHover(star)}
          onMouseLeave={() => setHover(0)}
          className={`text-2xl transition ${
            star <= (hover || value) ? 'text-yellow-400' : 'text-neutral-600'
          } ${disabled ? 'cursor-not-allowed' : 'cursor-pointer hover:scale-110'}`}
        >
          ★
        </button>
      ))}
    </div>
  );
};

const IdeaDetail = () => {
  const { id } = useParams();
  const { user } = useAuth();
  const [idea, setIdea] = useState(null);
  const [loading, setLoading] = useState(true);
  const [feedbackType, setFeedbackType] = useState('');
  const [feedbackComment, setFeedbackComment] = useState('');
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState('');
  const [noveltyBreakdown, setNoveltyBreakdown] = useState(null);
  const [rating, setRating] = useState(0);
  const [reviewComment, setReviewComment] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewMessage, setReviewMessage] = useState('');

  useEffect(() => {
    const endpoint = user ? `/ideas/${id}` : `/public/ideas/${id}`;
    api.get(endpoint)
      .then(res => {
        setIdea(res.data.idea || res.data);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, [id, user]);

  // Fetch novelty breakdown for authenticated users
  useEffect(() => {
    if (user && id) {
      api.get(`/ideas/${id}/novelty-explanation`)
        .then(res => setNoveltyBreakdown(res.data))
        .catch(() => {}); // Silently fail — non-critical
    }
  }, [id, user]);

  const handleFeedbackSubmit = async () => {
    if (!feedbackType) return;
    
    setSubmittingFeedback(true);
    try {
      await api.post(`/ideas/${id}/feedback`, {
        feedback_type: feedbackType,
        comment: feedbackComment || null
      });
      setFeedbackMessage('✓ Thank you! Feedback submitted successfully.');
      setFeedbackType('');
      setFeedbackComment('');
      setTimeout(() => setFeedbackMessage(''), 3000);
    } catch (err) {
      setFeedbackMessage(`✕ Error: ${err.response?.data?.error || 'Submission failed'}`);
      setTimeout(() => setFeedbackMessage(''), 3000);
    } finally {
      setSubmittingFeedback(false);
    }
  };

  const handleReviewSubmit = async () => {
    if (!rating) return;
    setSubmittingReview(true);
    try {
      await api.post(`/ideas/${id}/review`, {
        rating,
        comment: reviewComment || null
      });
      setReviewMessage('✓ Review submitted!');
      setTimeout(() => setReviewMessage(''), 3000);
    } catch (err) {
      setReviewMessage(`✕ Error: ${err.response?.data?.error || 'Submission failed'}`);
      setTimeout(() => setReviewMessage(''), 3000);
    } finally {
      setSubmittingReview(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-neutral-950 via-neutral-950 to-neutral-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-neutral-400">Loading idea...</p>
        </div>
      </div>
    );
  }

  if (!idea) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-neutral-950 via-neutral-950 to-neutral-900 flex items-center justify-center px-6">
        <div className="text-center max-w-md">
          <h2 className="text-3xl font-light text-white mb-3">Idea not found</h2>
          <p className="text-neutral-400 mb-6">The idea you're looking for doesn't exist or has been removed.</p>
          <Link to="/explore" className="text-indigo-400 hover:text-indigo-300 font-medium transition">
            Back to explore →
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-neutral-950 via-neutral-950 to-neutral-900">
      {/* Background decorations */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-600 rounded-full opacity-10 blur-3xl" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-purple-600 rounded-full opacity-10 blur-3xl" />
      </div>

      <div className="max-w-4xl mx-auto px-6 py-12 md:py-20 relative z-10">
        {/* Back Button */}
        <Link
          to="/explore"
          className="inline-flex items-center gap-2 text-indigo-400 hover:text-indigo-300 font-medium mb-8 transition group"
        >
          <span className="group-hover:-translate-x-1 transition-transform">←</span>
          <span>Back</span>
        </Link>

        {/* Header Section */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <span className="inline-block px-3 py-1 bg-gradient-to-r from-indigo-500/20 to-purple-500/20 rounded-full text-xs font-semibold text-indigo-300 border border-indigo-500/30">
              {idea.domain}
            </span>
            <span className="text-sm text-neutral-400">{idea.view_count || 0} views</span>
          </div>
          <h1 className="text-5xl md:text-6xl font-light text-white mb-4 leading-tight">
            {idea.title}
          </h1>
        </div>

        {/* Main Content */}
        <div className="space-y-12">
          {/* Problem Statement */}
          <section className="glass-card-lg p-8 border border-white/10">
            <h2 className="text-sm font-semibold text-indigo-400 uppercase tracking-widest mb-4">
              Problem Statement
            </h2>
            <p className="text-lg text-neutral-200 leading-relaxed">
              {idea.problem_statement}
            </p>
          </section>

          {/* Tech Stack */}
          <section className="glass-card-lg p-8 border border-white/10">
            <h2 className="text-sm font-semibold text-purple-400 uppercase tracking-widest mb-4">
              Suggested Tech Stack
            </h2>
            <p className="text-base text-neutral-300 leading-relaxed">
              {idea.tech_stack}
            </p>
          </section>

          {/* Evidence Sources — full SourcesList component */}
          <section className="glass-card-lg p-8 border border-white/10">
            <h2 className="text-sm font-semibold text-pink-400 uppercase tracking-widest mb-4">
              Evidence Sources
            </h2>
            {idea.sources && idea.sources.length > 0 ? (
              <SourcesList sources={idea.sources} evidenceBreakdown={null} />
            ) : (
              <span className="text-neutral-400">No sources available</span>
            )}
          </section>

          {/* Metrics Cards */}
          <div className="grid md:grid-cols-3 gap-6">
            <div className="glass-card-lg p-6 border border-white/10">
              <div className="text-xs text-indigo-400 uppercase tracking-widest font-semibold mb-3">
                Novelty Score
              </div>
              <div className="text-4xl font-bold text-indigo-300">
                {typeof idea.novelty_score === 'number' ? (idea.novelty_score / 10).toFixed(1) : 'N/A'}
              </div>
              <div className="text-sm text-neutral-400 mt-2">
                How novel and original
              </div>
            </div>
            <div className="glass-card-lg p-6 border border-white/10">
              <div className="text-xs text-purple-400 uppercase tracking-widest font-semibold mb-3">
                Quality Score
              </div>
              <div className="text-4xl font-bold text-purple-300">
                {typeof idea.quality_score === 'number' ? (idea.quality_score / 10).toFixed(1) : 'N/A'}
              </div>
              <div className="text-sm text-neutral-400 mt-2">
                Overall quality & viability
              </div>
            </div>
            <div className="glass-card-lg p-6 border border-white/10">
              <div className="text-xs text-pink-400 uppercase tracking-widest font-semibold mb-3">
                Trust Signal
              </div>
              <div className="text-4xl font-bold text-pink-300">
                {idea.evidence_strength ? (idea.evidence_strength.length > 0 ? '✓' : '?') : '✓'}
              </div>
              <div className="text-sm text-neutral-400 mt-2">
                Backed by research
              </div>
            </div>
          </div>

          {/* Logged-in User Sections */}
          {user && (
            <>
              {/* Novelty Breakdown Panel */}
              {noveltyBreakdown && (
                <section className="glass-card-lg p-8 border border-indigo-500/30 bg-indigo-500/5">
                  <h2 className="text-sm font-semibold text-indigo-400 uppercase tracking-widest mb-4">
                    Novelty Breakdown
                  </h2>
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <p className="text-neutral-300 leading-relaxed mb-4">
                        {noveltyBreakdown.explanation}
                      </p>
                      <div className="space-y-2">
                        {noveltyBreakdown.signal_breakdown?.signals &&
                          Object.entries(noveltyBreakdown.signal_breakdown.signals).map(([key, value]) => (
                            <div key={key} className="flex justify-between items-center text-sm">
                              <span className="text-neutral-400">{key.replace(/_/g, ' ')}</span>
                              <span className={`font-mono font-bold ${value >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                {value >= 0 ? '+' : ''}{value.toFixed(1)}
                              </span>
                            </div>
                          ))}
                      </div>
                    </div>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-neutral-400">Evidence Strength</span>
                        <span className="font-semibold text-neutral-200">{noveltyBreakdown.evidence_strength}</span>
                      </div>
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-neutral-400">Sources Analyzed</span>
                        <span className="font-semibold text-neutral-200">{noveltyBreakdown.sources_analyzed}</span>
                      </div>
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-neutral-400">Hallucination Risk</span>
                        <span className={`font-semibold ${
                          noveltyBreakdown.hallucination_risk === 'low' ? 'text-emerald-400' :
                          noveltyBreakdown.hallucination_risk === 'medium' ? 'text-yellow-400' : 'text-red-400'
                        }`}>{noveltyBreakdown.hallucination_risk}</span>
                      </div>
                    </div>
                  </div>
                </section>
              )}

              {/* Star Rating Widget */}
              <section className="glass-card-lg p-8 border border-white/10">
                <h2 className="text-sm font-semibold text-yellow-400 uppercase tracking-widest mb-4">
                  Rate This Idea
                </h2>
                <div className="flex items-center gap-6">
                  <StarRating value={rating} onChange={setRating} disabled={submittingReview} />
                  <span className="text-neutral-400 text-sm">{rating ? `${rating}/5` : 'Select a rating'}</span>
                </div>
                <textarea
                  value={reviewComment}
                  onChange={(e) => setReviewComment(e.target.value.slice(0, 1000))}
                  placeholder="Optional comment about this idea..."
                  className="glass-input w-full h-20 resize-none mt-4"
                />
                {reviewMessage && (
                  <div className={`mt-3 p-3 rounded-lg border ${
                    reviewMessage.startsWith('✓')
                      ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-200'
                      : 'bg-red-500/20 border-red-500/50 text-red-200'
                  }`}>{reviewMessage}</div>
                )}
                <button
                  onClick={handleReviewSubmit}
                  disabled={!rating || submittingReview}
                  className="btn-primary mt-4"
                >
                  {submittingReview ? 'Submitting...' : 'Submit Rating'}
                </button>
              </section>

              {/* Novelty Explanation */}
              {idea.novelty_explanation && !noveltyBreakdown && (
                <section className="glass-card-lg p-8 border border-indigo-500/30 bg-indigo-500/5">
                  <h2 className="text-sm font-semibold text-indigo-400 uppercase tracking-widest mb-4">
                    Why This Is Novel
                  </h2>
                  <p className="text-base text-neutral-300 leading-relaxed">
                    {idea.novelty_explanation}
                  </p>
                </section>
              )}

              {/* Hallucination Risk */}
              {idea.hallucination_risk_level && (
                <section className="glass-card-lg p-8 border border-yellow-500/30 bg-yellow-500/5">
                  <h2 className="text-sm font-semibold text-yellow-400 uppercase tracking-widest mb-4">
                    Quality Indicators
                  </h2>
                  <div className="space-y-3">
                    {idea.hallucination_risk_level && (
                      <div className="flex justify-between items-center">
                        <span className="text-neutral-400">Hallucination Risk:</span>
                        <span className="font-medium text-neutral-300">{idea.hallucination_risk_level}</span>
                      </div>
                    )}
                    {idea.evidence_strength && (
                      <div className="flex justify-between items-center">
                        <span className="text-neutral-400">Evidence Strength:</span>
                        <span className="font-medium text-neutral-300">{idea.evidence_strength}</span>
                      </div>
                    )}
                  </div>
                </section>
              )}

              {/* Feedback Section */}
              <section className="glass-card-lg p-8 border border-white/10">
                <h2 className="text-sm font-semibold text-neutral-300 uppercase tracking-widest mb-6">
                  Share Your Feedback
                </h2>
                <p className="text-neutral-400 mb-6">
                  Help improve the system by providing feedback on this idea. Your insights help us maintain research integrity.
                </p>

                <div className="space-y-4">
                  {/* Feedback Type Select */}
                  <div>
                    <label className="block text-sm font-medium text-neutral-300 mb-3">
                      Feedback Type
                    </label>
                    <select
                      value={feedbackType}
                      onChange={(e) => setFeedbackType(e.target.value)}
                      className="glass-input w-full"
                    >
                      <option value="">Select feedback type...</option>
                      <option value="factual_error">Report factual error</option>
                      <option value="hallucinated_source">Report hallucinated source</option>
                      <option value="weak_novelty">Weak novelty</option>
                      <option value="poor_justification">Poor justification</option>
                      <option value="unclear_scope">Unclear scope</option>
                      <option value="high_quality">High quality</option>
                    </select>
                  </div>

                  {/* Comment Textarea */}
                  <div>
                    <label className="block text-sm font-medium text-neutral-300 mb-3">
                      Comment (Optional)
                    </label>
                    <textarea
                      value={feedbackComment}
                      onChange={(e) => setFeedbackComment(e.target.value.slice(0, 1000))}
                      placeholder="Add context, references, or additional insights..."
                      className="glass-input w-full h-24 resize-none"
                    />
                    <p className="text-xs text-neutral-500 mt-1">{feedbackComment.length}/1000</p>
                  </div>

                  {/* Feedback Message */}
                  {feedbackMessage && (
                    <div
                      className={`p-4 rounded-lg border ${
                        feedbackMessage.startsWith('✓')
                          ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-200'
                          : 'bg-red-500/20 border-red-500/50 text-red-200'
                      }`}
                    >
                      {feedbackMessage}
                    </div>
                  )}

                  {/* Submit Button */}
                  <button
                    onClick={handleFeedbackSubmit}
                    disabled={!feedbackType || submittingFeedback}
                    className="btn-primary w-full"
                  >
                    {submittingFeedback ? 'Submitting...' : 'Submit Feedback'}
                  </button>
                </div>
              </section>
            </>
          )}

          {/* Not logged in */}
          {!user && (
            <section className="glass-card-lg p-8 border border-indigo-500/30 bg-indigo-500/5 text-center">
              <p className="text-neutral-300 mb-4">
                Sign in to provide feedback and see detailed analysis.
              </p>
              <Link
                to="/login"
                className="btn-primary inline-flex items-center justify-center gap-2"
              >
                <span>Sign in</span>
                <span>→</span>
              </Link>
            </section>
          )}
        </div>
      </div>
    </div>
  );
};

export default IdeaDetail;
