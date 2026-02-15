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
  const [trace, setTrace] = useState(null);
  const [traceLoading, setTraceLoading] = useState(false);
  const [traceOpen, setTraceOpen] = useState(false);
  const [actionMsg, setActionMsg] = useState(null);

  const fetchIdea = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get(`/admin/ideas/${id}`);
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

  const fetchTrace = async () => {
    if (trace) { setTraceOpen(!traceOpen); return; }
    setTraceLoading(true);
    try {
      const res = await api.get(`/admin/ideas/${id}/generation-trace`);
      setTrace(res.data.generation_trace);
      setTraceOpen(true);
    } catch {
      setActionMsg({ type: 'error', text: 'No generation trace available for this idea.' });
    } finally {
      setTraceLoading(false);
    }
  };

  const handleVerdict = async () => {
    if (!verdict) return;
    if (verdict === 'rejected' && !reason.trim()) {
      setError('Reason is required for rejection.');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await api.post(`/admin/ideas/${id}/verdict`, { verdict, reason: reason.trim() || 'Admin verdict' });
      await fetchIdea();
      setActionMsg({ type: 'success', text: `Verdict "${verdict}" submitted.` });
      setVerdict('');
      setReason('');
    } catch (err) {
      console.error('Failed to submit verdict:', err);
      setError('Failed to submit verdict.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleHumanVerified = async () => {
    try {
      const newVal = !idea.is_human_verified;
      await api.post(`/admin/ideas/${id}/human-verified`, { is_human_verified: newVal });
      setIdea(prev => ({ ...prev, is_human_verified: newVal }));
      setActionMsg({ type: 'success', text: newVal ? 'Marked as human-verified.' : 'Removed human-verified flag.' });
    } catch {
      setActionMsg({ type: 'error', text: 'Failed to update human-verified status.' });
    }
  };

  const handleFlagHallucinated = async (sourceId, currentVal) => {
    try {
      await api.post(`/admin/ideas/${id}/sources/${sourceId}/hallucinated`, { is_hallucinated: !currentVal });
      setIdea(prev => ({
        ...prev,
        sources: prev.sources.map(s => s.id === sourceId ? { ...s, is_hallucinated: !currentVal } : s)
      }));
      setActionMsg({ type: 'success', text: !currentVal ? 'Source flagged as hallucinated.' : 'Hallucination flag removed.' });
    } catch {
      setActionMsg({ type: 'error', text: 'Failed to update hallucination flag.' });
    }
  };

  const handleRescore = async () => {
    try {
      setActionMsg({ type: 'info', text: 'Rescoring...' });
      const res = await api.post(`/admin/ideas/${id}/rescore`);
      setIdea(prev => ({
        ...prev,
        quality_score: res.data.new_quality_score,
        novelty_score_cached: res.data.new_novelty_score
      }));
      setActionMsg({ type: 'success', text: `Rescored: quality=${res.data.new_quality_score}, novelty=${res.data.new_novelty_score}` });
    } catch {
      setActionMsg({ type: 'error', text: 'Failed to rescore idea.' });
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="text-center text-neutral-400">Loading idea details...</div>
      </div>
    );
  }

  if (error && !idea) {
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
      {/* Action Messages */}
      {actionMsg && (
        <div className={`mb-4 p-3 rounded text-sm ${
          actionMsg.type === 'success' ? 'bg-green-500/10 text-green-400 border border-green-500/30' :
          actionMsg.type === 'error' ? 'bg-red-500/10 text-red-400 border border-red-500/30' :
          'bg-blue-500/10 text-blue-400 border border-blue-500/30'
        }`}>
          {actionMsg.text}
          <button onClick={() => setActionMsg(null)} className="ml-3 text-xs opacity-60 hover:opacity-100">✕</button>
        </div>
      )}

      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate('/admin')}
          className="text-neutral-400 hover:text-white mb-4 inline-flex items-center"
        >
          ← Back to review queue
        </button>
        <div className="flex items-center gap-3">
          <h1 className="text-4xl font-light text-white">{idea.title}</h1>
          {idea.is_human_verified && (
            <span className="px-2 py-1 text-xs bg-green-500/20 text-green-400 border border-green-500/30 rounded">
              Human Verified
            </span>
          )}
        </div>
        <p className="mt-2 text-neutral-400">
          Domain: {idea.domain} • Created: {new Date(idea.created_at).toLocaleDateString()}
          {idea.ai_pipeline_version && ` • Pipeline: ${idea.ai_pipeline_version}`}
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

          {/* Evidence Sources with hallucination flagging */}
          <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-6">
            <h2 className="text-xl font-medium text-white mb-4">Evidence Sources ({idea.sources.length})</h2>
            {idea.sources.length > 0 ? (
              <div className="space-y-4">
                {idea.sources.map((source, index) => (
                  <div key={source.id || index} className={`border rounded p-4 ${
                    source.is_hallucinated ? 'border-red-500/50 bg-red-500/5' : 'border-neutral-700'
                  }`}>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="text-white font-medium">{source.title}</h3>
                          {source.is_hallucinated && (
                            <span className="px-1.5 py-0.5 text-xs bg-red-500/20 text-red-400 rounded">
                              Hallucinated
                            </span>
                          )}
                        </div>
                        <p className="text-neutral-400 text-sm mt-1">{source.source_type}</p>
                        {source.summary && (
                          <p className="text-neutral-300 text-sm mt-2">{source.summary}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        <button
                          onClick={() => handleFlagHallucinated(source.id, source.is_hallucinated)}
                          className={`text-xs px-2 py-1 rounded border transition-colors ${
                            source.is_hallucinated
                              ? 'border-red-500 text-red-400 hover:bg-red-500/20'
                              : 'border-neutral-600 text-neutral-400 hover:border-red-500 hover:text-red-400'
                          }`}
                          title={source.is_hallucinated ? 'Remove hallucination flag' : 'Flag as hallucinated'}
                        >
                          {source.is_hallucinated ? '⚠ Unflag' : '⚠ Flag'}
                        </button>
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-400 hover:text-blue-300 text-sm"
                        >
                          View →
                        </a>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-neutral-400">No sources available.</p>
            )}
          </div>

          {/* Generation Trace Viewer */}
          <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-medium text-white">Generation Trace</h2>
              <button
                onClick={fetchTrace}
                disabled={traceLoading}
                className="text-sm px-3 py-1 rounded border border-neutral-600 text-neutral-300 hover:border-white hover:text-white transition-colors disabled:opacity-50"
              >
                {traceLoading ? 'Loading...' : traceOpen ? 'Hide Trace' : 'Show Trace'}
              </button>
            </div>
            {traceOpen && trace && (
              <div className="space-y-4">
                <div className="text-xs text-neutral-500 mb-2">
                  Pipeline: {trace.ai_pipeline_version} • Bias: {trace.bias_profile_version || 'None'}
                </div>
                {['phase_0', 'phase_1', 'phase_2', 'phase_3', 'phase_4', 'phase_5'].map(phaseKey => {
                  const phase = trace[phaseKey];
                  if (!phase) return null;
                  return (
                    <div key={phaseKey} className="border border-neutral-700 rounded p-4">
                      <h4 className="text-sm font-medium text-neutral-200 mb-1">
                        {phase.name || phaseKey}
                      </h4>
                      <p className="text-xs text-neutral-400 mb-2">{phase.description || ''}</p>
                      <pre className="text-xs text-neutral-300 bg-neutral-800 rounded p-3 overflow-x-auto max-h-48 overflow-y-auto whitespace-pre-wrap">
                        {typeof phase.output === 'string' ? phase.output : JSON.stringify(phase.output, null, 2)}
                      </pre>
                    </div>
                  );
                })}
                {trace.constraints_active && (
                  <div className="border border-neutral-700 rounded p-4">
                    <h4 className="text-sm font-medium text-neutral-200 mb-1">Active Constraints</h4>
                    <pre className="text-xs text-neutral-300 bg-neutral-800 rounded p-3 overflow-x-auto whitespace-pre-wrap">
                      {JSON.stringify(trace.constraints_active, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Feedback History */}
          <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-6">
            <h2 className="text-xl font-medium text-white mb-4">Feedback History ({idea.feedback_history?.length || 0})</h2>
            {idea.feedback_history?.length > 0 ? (
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

        {/* Right Column - Trust Signals, Actions & Verdict Panel */}
        <div className="space-y-6">
          {/* Trust Signals */}
          <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-6">
            <h2 className="text-xl font-medium text-white mb-4">Trust Signals</h2>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-neutral-300">Quality Score</span>
                <span className="text-white font-medium">{typeof idea.quality_score === 'number' ? (idea.quality_score / 10).toFixed(1) : 'N/A'}/10</span>
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

          {/* Admin Quick Actions */}
          <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-6">
            <h2 className="text-xl font-medium text-white mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <button
                onClick={handleHumanVerified}
                className={`w-full p-3 rounded border text-left text-sm transition-colors ${
                  idea.is_human_verified
                    ? 'border-green-500 bg-green-500/10 text-green-400'
                    : 'border-neutral-600 text-neutral-300 hover:border-green-500 hover:text-green-400'
                }`}
              >
                {idea.is_human_verified ? '✓ Human Verified — Click to remove' : '○ Mark as Human Verified'}
              </button>
              <button
                onClick={handleRescore}
                className="w-full p-3 rounded border border-neutral-600 text-neutral-300 hover:border-blue-500 hover:text-blue-400 text-left text-sm transition-colors"
              >
                ↻ Recalculate Scores
              </button>
            </div>
          </div>

          {/* Verdict Action Panel — always visible, supports updates */}
          <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-6">
            <h2 className="text-xl font-medium text-white mb-4">
              {idea.admin_verdict ? 'Update Verdict' : 'Admin Verdict'}
            </h2>

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

              <div>
                <label className="block text-sm font-medium text-neutral-300 mb-2">
                  Reason {verdict === 'rejected' && <span className="text-red-400">*</span>}
                </label>
                <textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder={verdict === 'rejected' ? 'Required: reason for rejection...' : 'Optional reason...'}
                  className="w-full h-24 bg-neutral-800 border border-neutral-600 rounded px-3 py-2 text-white placeholder-neutral-400 focus:border-white focus:outline-none"
                />
              </div>

              <button
                onClick={handleVerdict}
                disabled={submitting || !verdict}
                className="w-full bg-white text-black font-medium py-3 px-4 rounded hover:bg-neutral-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {submitting ? 'Submitting...' : idea.admin_verdict ? 'Update Verdict' : 'Submit Verdict'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminIdeaDetail;
