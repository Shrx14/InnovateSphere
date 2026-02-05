import React, { useEffect, useState, useContext } from 'react';
import { useParams } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import api from '../../shared/api';

const IdeaDetail = () => {
  const { id } = useParams();
  const { user } = useContext(AuthContext);
  const [idea, setIdea] = useState(null);
  const [loading, setLoading] = useState(true);
  const [feedbackType, setFeedbackType] = useState('');
  const [feedbackComment, setFeedbackComment] = useState('');

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

  const handleFeedbackSubmit = () => {
    if (!feedbackType) return;
    api.post(`/ideas/${id}/feedback`, {
      feedback_type: feedbackType,
      comment: feedbackComment || null
    })
      .then(() => {
        setFeedbackType('');
        setFeedbackComment('');
        alert('Feedback submitted');
      })
      .catch(err => {
        alert('Feedback submission failed: ' + (err.response?.data?.error || 'Unknown error'));
      });
  };

  if (loading) {
    return (
      <div className="bg-neutral-950 min-h-screen flex items-center justify-center">
        <p className="text-neutral-400">Loading idea...</p>
      </div>
    );
  }

  if (!idea) {
    return (
      <div className="bg-neutral-950 min-h-screen flex items-center justify-center">
        <p className="text-neutral-400">Idea not found.</p>
      </div>
    );
  }

  return (
    <div className="bg-neutral-950 min-h-screen">
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="animate-fade-in-up">
          <h1 className="text-3xl font-normal text-white mb-2">{idea.title}</h1>
          <div className="flex items-center gap-4 mb-8">
            <span className="px-2 py-1 text-xs bg-neutral-800 text-neutral-300 rounded">{idea.domain}</span>
            <span className="text-xs text-neutral-500">{idea.view_count} views</span>
          </div>
        </div>

        {/* Problem statement */}
        <section className="animate-fade-in-up mb-20">
          <div className="text-xs uppercase tracking-widest text-neutral-400 mb-6">Problem statement</div>
          <p className="text-base text-neutral-300 leading-relaxed">{idea.problem_statement}</p>
        </section>

        {/* Tech stack */}
        <section className="animate-fade-in-up mb-20">
          <div className="text-xs uppercase tracking-widest text-neutral-400 mb-6">Tech stack</div>
          <p className="text-sm text-neutral-400">{idea.tech_stack}</p>
        </section>

        {/* Evidence sources */}
        <section className="animate-fade-in-up mb-20">
          <div className="text-xs uppercase tracking-widest text-neutral-400 mb-6">Evidence sources</div>
          <div className="flex flex-wrap gap-2">
            {idea.sources?.map((source, i) => (
              <span key={i} className="px-2 py-1 text-xs bg-neutral-800 text-neutral-300 rounded">
                {source.source_type}
              </span>
            )) || <span className="text-neutral-400">No sources available</span>}
          </div>
        </section>

        {/* Logged-in only sections */}
        {user && (
          <>
            {/* Novelty explanation */}
            {idea.novelty_explanation && (
              <section className="animate-fade-in-up mb-20">
                <div className="text-xs uppercase tracking-widest text-neutral-400 mb-6">Novelty explanation</div>
                <p className="text-sm text-neutral-400">{idea.novelty_explanation}</p>
              </section>
            )}

            {/* Quality score */}
            {idea.quality_score !== undefined && (
              <section className="animate-fade-in-up mb-20">
                <div className="text-xs uppercase tracking-widest text-neutral-400 mb-6">Trust signals</div>
                <span className="text-xs text-neutral-400">Quality score: {idea.quality_score}</span>
              </section>
            )}

            {/* Evidence strength */}
            {idea.evidence_strength && (
              <section className="animate-fade-in-up mb-20">
                <span className="text-xs text-neutral-400">Evidence strength: {idea.evidence_strength}</span>
              </section>
            )}

            {/* Hallucination risk */}
            {idea.hallucination_risk_level && (
              <section className="animate-fade-in-up mb-20">
                <span className="text-xs text-neutral-400">Hallucination risk: {idea.hallucination_risk_level}</span>
              </section>
            )}

            {/* Feedback actions */}
            <section className="animate-fade-in-up mb-20">
              <div className="text-xs uppercase tracking-widest text-neutral-400 mb-6">Feedback</div>
              <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-8 max-w-2xl">
                <p className="text-sm text-neutral-400 mb-6">
                  Help improve the system by providing feedback on this idea.
                </p>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-neutral-300 mb-2">Feedback type</label>
                    <select
                      value={feedbackType}
                      onChange={(e) => setFeedbackType(e.target.value)}
                      className="w-full bg-neutral-800 border border-neutral-700 text-neutral-300 rounded-lg px-4 py-2"
                    >
                      <option value="">Select feedback type</option>
                      <option value="factual_error">Report factual error</option>
                      <option value="hallucinated_source">Report hallucinated source</option>
                      <option value="weak_novelty">Weak novelty</option>
                      <option value="poor_justification">Poor justification</option>
                      <option value="unclear_scope">Unclear scope</option>
                      <option value="high_quality">High quality</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm text-neutral-300 mb-2">Comment (optional)</label>
                    <textarea
                      value={feedbackComment}
                      onChange={(e) => setFeedbackComment(e.target.value)}
                      className="w-full bg-neutral-800 border border-neutral-700 text-neutral-300 rounded-lg px-4 py-2 h-24"
                      placeholder="Add context or references..."
                    />
                  </div>
                  <button
                    onClick={handleFeedbackSubmit}
                    disabled={!feedbackType}
                    className="bg-indigo-600/90 hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg px-6 py-2 font-medium transition-colors"
                  >
                    Submit feedback
                  </button>
                </div>
              </div>
            </section>
          </>
        )}
      </div>
    </div>
  );
};

export default IdeaDetail;
