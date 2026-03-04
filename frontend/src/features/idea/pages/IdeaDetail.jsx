import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { ArrowLeft, Eye, Star, MessageSquare, AlertTriangle, ShieldCheck, Bookmark, Share2, Users } from "lucide-react";

import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import { fadeIn, staggerContainer } from "@/lib/motion";
import { cn } from "@/lib/utils";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Textarea } from "@/components/ui/Textarea";
import { ScoreDisplay } from "@/components/ui/ScoreDisplay";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { SkeletonText } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import SourcesList from "../../novelty/components/SourcesList";

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
          className={cn(
            "text-2xl transition",
            star <= (hover || value) ? "text-yellow-400" : "text-neutral-700",
            disabled ? "cursor-not-allowed" : "cursor-pointer hover:scale-110"
          )}
        >
          <Star className="w-7 h-7" fill={star <= (hover || value) ? "currentColor" : "none"} />
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
  const [feedbackType, setFeedbackType] = useState("");
  const [feedbackComment, setFeedbackComment] = useState("");
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
  const [noveltyBreakdown, setNoveltyBreakdown] = useState(null);
  const [rating, setRating] = useState(0);
  const [reviewComment, setReviewComment] = useState("");
  const [submittingReview, setSubmittingReview] = useState(false);
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [requestedCount, setRequestedCount] = useState(0);

  useEffect(() => {
    const endpoint = user ? `/ideas/${id}` : `/public/ideas/${id}`;
    api
      .get(endpoint)
      .then((res) => {
        const loadedIdea = res.data.idea || res.data;
        setIdea(loadedIdea);
        setRequestedCount(loadedIdea.requested_count || 0);
        setLoading(false);
      })
      .catch(() => setLoading(false));

    // Check bookmark status for authenticated users
    if (user) {
      api.get(`/ideas/${id}/feedbacks`)
        .then(res => {
          const bookmarks = (res.data.by_type?.bookmark || []);
          setIsBookmarked(bookmarks.length > 0);
        })
        .catch(() => { });
    }
  }, [id, user]);

  // Fetch novelty breakdown for authenticated users
  useEffect(() => {
    if (user && id) {
      api
        .get(`/ideas/${id}/novelty-explanation`)
        .then((res) => setNoveltyBreakdown(res.data))
        .catch(() => { }); // non-critical
    }
  }, [id, user]);

  const handleFeedbackSubmit = async () => {
    if (!feedbackType) return;
    setSubmittingFeedback(true);
    try {
      await api.post(`/ideas/${id}/feedback`, {
        feedback_type: feedbackType,
        comment: feedbackComment || null,
      });
      toast.success("Thank you! Feedback submitted successfully.");
      setFeedbackType("");
      setFeedbackComment("");
    } catch (err) {
      toast.error(err.response?.data?.error || "Submission failed");
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
        comment: reviewComment || null,
      });
      toast.success("Review submitted!");
    } catch (err) {
      toast.error(err.response?.data?.error || "Submission failed");
    } finally {
      setSubmittingReview(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-neutral-950">
        <div className="max-w-4xl mx-auto px-6 py-12 md:py-20">
          <div className="h-6 w-20 dark:bg-neutral-800 bg-neutral-100 rounded mb-8" />
          <div className="h-10 w-3/4 dark:bg-neutral-800 bg-neutral-100 rounded-lg mb-4" />
          <div className="h-6 w-48 dark:bg-neutral-800 bg-neutral-100 rounded mb-12" />
          <Card className="p-8 mb-8"><SkeletonText lines={4} /></Card>
          <Card className="p-8"><SkeletonText lines={3} /></Card>
        </div>
      </div>
    );
  }

  if (!idea) {
    return (
      <div className="min-h-screen bg-neutral-950 flex items-center justify-center px-6">
        <EmptyState
          title="Idea not found"
          description="The idea you're looking for doesn't exist or has been removed."
          action={
            <Button asChild variant="secondary">
              <Link to="/explore">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to explore
              </Link>
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-950">
      <div className="max-w-4xl mx-auto px-6 py-12 md:py-20">
        {/* Back Button */}
        <motion.div variants={fadeIn} initial="hidden" animate="visible">
          <Link
            to="/explore"
            className="inline-flex items-center gap-2 text-indigo-400 hover:text-indigo-300 font-medium mb-8 transition group"
          >
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
            <span>Back</span>
          </Link>
        </motion.div>

        <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-8">
          {/* Header */}
          <motion.div variants={fadeIn} className="mb-4">
            <div className="flex items-center gap-3 mb-4">
              <Badge>{idea.domain}</Badge>
              {idea.status && <StatusBadge status={idea.status} />}
              <span className="flex items-center gap-1 text-sm dark:text-neutral-500 text-neutral-400">
                <Eye className="w-4 h-4" /> {idea.view_count || 0}
              </span>
            </div>
            <h1 className="text-4xl md:text-5xl font-light dark:text-white text-neutral-900 leading-tight mb-4">
              {idea.title}
            </h1>
            {user && (
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={async () => {
                    try {
                      if (isBookmarked) {
                        await api.delete(`/ideas/${id}/feedback?feedback_type=bookmark`);
                        setIsBookmarked(false);
                        toast.success('Bookmark removed');
                      } else {
                        await api.post(`/ideas/${id}/feedback`, { feedback_type: 'bookmark' });
                        setIsBookmarked(true);
                        toast.success('Idea bookmarked');
                      }
                    } catch (err) {
                      toast.error(err.response?.data?.error || 'Failed');
                    }
                  }}
                  className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${isBookmarked
                      ? 'bg-indigo-600 text-white'
                      : 'bg-neutral-800 dark:text-neutral-300 text-neutral-600 hover:bg-neutral-700'
                    }`}
                >
                  <Bookmark className="w-4 h-4" fill={isBookmarked ? 'currentColor' : 'none'} />
                  {isBookmarked ? 'Bookmarked' : 'Bookmark'}
                </button>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(window.location.href);
                    toast.success('Link copied to clipboard');
                  }}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-neutral-800 dark:text-neutral-300 text-neutral-600 hover:bg-neutral-700 transition-colors"
                >
                  <Share2 className="w-4 h-4" />
                  Share
                </button>
                <button
                  onClick={async () => {
                    try {
                      const res = await api.post(`/ideas/${id}/request`);
                      setRequestedCount(res.data.requested_count);
                      toast.success('Interest recorded!');
                    } catch (err) {
                      toast.error(err.response?.data?.error || 'Failed');
                    }
                  }}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-neutral-800 dark:text-neutral-300 text-neutral-600 hover:bg-neutral-700 transition-colors"
                >
                  <Users className="w-4 h-4" />
                  Request ({requestedCount})
                </button>
              </div>
            )}
          </motion.div>

          {/* Problem Statement */}
          <motion.div variants={fadeIn}>
            <Card className="p-8">
              <h2 className="text-sm font-semibold text-indigo-400 uppercase tracking-widest mb-4">
                Problem Statement
              </h2>
              <p className="text-lg dark:text-neutral-200 text-neutral-700 leading-relaxed">{idea.problem_statement}</p>
            </Card>
          </motion.div>

          {/* Tech Stack */}
          <motion.div variants={fadeIn}>
            <Card className="p-8">
              <h2 className="text-sm font-semibold text-purple-400 uppercase tracking-widest mb-4">
                Suggested Tech Stack
              </h2>
              {idea.tech_stack_json && Array.isArray(idea.tech_stack_json) && idea.tech_stack_json.length > 0 ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  {idea.tech_stack_json.map((item, idx) => {
                    // Handle two schemas: { component, technologies[], rationale } and { name, role, justification }
                    const name = item.component || item.name || "Technology";
                    const techs = item.technologies;
                    const desc = item.rationale || item.role || "";
                    const extra = item.justification || "";
                    return (
                      <div
                        key={idx}
                        className="rounded-xl border border-neutral-800 dark:bg-neutral-900/60 bg-white/60 p-4 hover:border-purple-500/30 transition"
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-sm font-semibold text-purple-300">{name}</span>
                          {techs && techs.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {techs.map((t, i) => (
                                <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
                                  {t}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                        {desc && <p className="text-sm dark:text-neutral-400 text-neutral-500 leading-relaxed">{desc}</p>}
                        {extra && <p className="text-xs dark:text-neutral-500 text-neutral-400 mt-1 italic">{extra}</p>}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-base dark:text-neutral-300 text-neutral-600 leading-relaxed">{idea.tech_stack}</p>
              )}
            </Card>
          </motion.div>

          {/* Evidence Sources */}
          <motion.div variants={fadeIn}>
            <Card className="p-8">
              <h2 className="text-sm font-semibold text-pink-400 uppercase tracking-widest mb-4">
                Evidence Sources
              </h2>
              {idea.sources && idea.sources.length > 0 ? (
                <SourcesList sources={idea.sources} evidenceBreakdown={null} />
              ) : (
                <span className="dark:text-neutral-500 text-neutral-400">No sources available</span>
              )}
            </Card>
          </motion.div>

          {/* Metrics Cards */}
          <motion.div variants={fadeIn} className="grid md:grid-cols-3 gap-6">
            <Card className="p-6 text-center">
              <div className="text-xs text-indigo-400 uppercase tracking-widest font-semibold mb-3">Novelty Score</div>
              <ScoreDisplay value={idea.novelty_score} size="lg" />
              <div className="text-sm dark:text-neutral-500 text-neutral-400 mt-2">How novel and original</div>
            </Card>
            <Card className="p-6 text-center">
              <div className="text-xs text-purple-400 uppercase tracking-widest font-semibold mb-3">Quality Score</div>
              <ScoreDisplay value={idea.quality_score} size="lg" />
              <div className="text-sm dark:text-neutral-500 text-neutral-400 mt-2">Overall quality & viability</div>
            </Card>
            <Card className="p-6 text-center">
              <div className="text-xs text-pink-400 uppercase tracking-widest font-semibold mb-3">Trust Signal</div>
              <div className="flex justify-center mb-2">
                <ShieldCheck className="w-10 h-10 text-emerald-400" />
              </div>
              <div className="text-sm dark:text-neutral-500 text-neutral-400">Backed by research</div>
            </Card>
          </motion.div>

          {/* Authenticated user sections */}
          {user && (
            <>
              {/* Novelty Breakdown Panel */}
              {noveltyBreakdown && (
                <motion.div variants={fadeIn}>
                  <Card className="p-8 border-indigo-500/20 bg-indigo-500/5">
                    <h2 className="text-sm font-semibold text-indigo-400 uppercase tracking-widest mb-4">
                      Novelty Breakdown
                    </h2>
                    <div className="grid md:grid-cols-2 gap-6">
                      <div>
                        <p className="dark:text-neutral-300 text-neutral-600 leading-relaxed mb-4 whitespace-pre-line">
                          {typeof noveltyBreakdown.explanation === 'object'
                            ? (noveltyBreakdown.explanation.full_narrative || noveltyBreakdown.explanation.summary || JSON.stringify(noveltyBreakdown.explanation))
                            : noveltyBreakdown.explanation}
                        </p>
                        <div className="space-y-2">
                          {noveltyBreakdown.signal_breakdown?.signals &&
                            Object.entries(noveltyBreakdown.signal_breakdown.signals).map(([key, value]) => (
                              <div key={key} className="flex justify-between items-center text-sm">
                                <span className="dark:text-neutral-400 text-neutral-500">{key.replace(/_/g, " ")}</span>
                                <span
                                  className={cn(
                                    "font-mono font-bold",
                                    value >= 0 ? "text-emerald-400" : "text-red-400"
                                  )}
                                >
                                  {value >= 0 ? "+" : ""}
                                  {value.toFixed(1)}
                                </span>
                              </div>
                            ))}
                        </div>
                      </div>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center text-sm">
                          <span className="dark:text-neutral-400 text-neutral-500">Evidence Strength</span>
                          <span className="font-semibold dark:text-neutral-200 text-neutral-700">{noveltyBreakdown.evidence_strength}</span>
                        </div>
                        <div className="flex justify-between items-center text-sm">
                          <span className="dark:text-neutral-400 text-neutral-500">Sources Analyzed</span>
                          <span className="font-semibold dark:text-neutral-200 text-neutral-700">{noveltyBreakdown.sources_analyzed}</span>
                        </div>
                        <div className="flex justify-between items-center text-sm">
                          <span className="dark:text-neutral-400 text-neutral-500">Hallucination Risk</span>
                          <span
                            className={cn(
                              "font-semibold",
                              noveltyBreakdown.hallucination_risk === "low"
                                ? "text-emerald-400"
                                : noveltyBreakdown.hallucination_risk === "medium"
                                  ? "text-yellow-400"
                                  : "text-red-400"
                            )}
                          >
                            {noveltyBreakdown.hallucination_risk}
                          </span>
                        </div>
                      </div>
                    </div>
                  </Card>
                </motion.div>
              )}

              {/* Star Rating Widget */}
              <motion.div variants={fadeIn}>
                <Card className="p-8">
                  <h2 className="text-sm font-semibold text-yellow-400 uppercase tracking-widest mb-4">
                    Rate This Idea
                  </h2>
                  <div className="flex items-center gap-6">
                    <StarRating value={rating} onChange={setRating} disabled={submittingReview} />
                    <span className="dark:text-neutral-500 text-neutral-400 text-sm">
                      {rating ? `${rating}/5` : "Select a rating"}
                    </span>
                  </div>
                  <Textarea
                    value={reviewComment}
                    onChange={(e) => setReviewComment(e.target.value.slice(0, 1000))}
                    placeholder="Optional comment about this idea..."
                    className="mt-4 h-20 resize-none"
                  />
                  <Button onClick={handleReviewSubmit} disabled={!rating || submittingReview} className="mt-4">
                    {submittingReview ? "Submitting..." : "Submit Rating"}
                  </Button>
                </Card>
              </motion.div>

              {/* Novelty Explanation (fallback when no full breakdown) */}
              {idea.novelty_explanation && !noveltyBreakdown && (
                <motion.div variants={fadeIn}>
                  <Card className="p-8 border-indigo-500/20 bg-indigo-500/5">
                    <h2 className="text-sm font-semibold text-indigo-400 uppercase tracking-widest mb-4">
                      Why This Is Novel
                    </h2>
                    <p className="text-base dark:text-neutral-300 text-neutral-600 leading-relaxed whitespace-pre-line">
                      {typeof idea.novelty_explanation === 'object'
                        ? (idea.novelty_explanation.full_narrative || idea.novelty_explanation.summary || '')
                        : idea.novelty_explanation}
                    </p>
                  </Card>
                </motion.div>
              )}

              {/* Hallucination Risk / Quality Indicators */}
              {idea.hallucination_risk_level && (
                <motion.div variants={fadeIn}>
                  <Card className="p-8 border-yellow-500/20 bg-yellow-500/5">
                    <h2 className="text-sm font-semibold text-yellow-400 uppercase tracking-widest mb-4">
                      Quality Indicators
                    </h2>
                    <div className="space-y-3">
                      {idea.hallucination_risk_level && (
                        <div className="flex justify-between items-center">
                          <span className="dark:text-neutral-400 text-neutral-500 flex items-center gap-2">
                            <AlertTriangle className="w-4 h-4" /> Hallucination Risk
                          </span>
                          <span className="font-medium dark:text-neutral-300 text-neutral-600">{typeof idea.hallucination_risk_level === 'object' ? JSON.stringify(idea.hallucination_risk_level) : idea.hallucination_risk_level}</span>
                        </div>
                      )}
                      {idea.evidence_strength && (
                        <div className="flex justify-between items-center">
                          <span className="dark:text-neutral-400 text-neutral-500 flex items-center gap-2">
                            <ShieldCheck className="w-4 h-4" /> Evidence Strength
                          </span>
                          <span className="font-medium dark:text-neutral-300 text-neutral-600">{typeof idea.evidence_strength === 'object' ? JSON.stringify(idea.evidence_strength) : idea.evidence_strength}</span>
                        </div>
                      )}
                    </div>
                  </Card>
                </motion.div>
              )}

              {/* Quick Reactions */}
              <motion.div variants={fadeIn}>
                <Card className="p-6">
                  <h2 className="text-sm font-semibold dark:text-neutral-300 text-neutral-600 uppercase tracking-widest mb-4">
                    Quick Reactions
                  </h2>
                  <div className="flex flex-wrap gap-3">
                    {[
                      { type: 'upvote', label: '👍 Upvote', color: 'bg-emerald-600 hover:bg-emerald-500' },
                      { type: 'downvote', label: '👎 Downvote', color: 'bg-red-600 hover:bg-red-500' },
                      { type: 'bookmark', label: '🔖 Bookmark', color: 'bg-indigo-600 hover:bg-indigo-500' },
                      { type: 'helpful', label: '✅ Helpful', color: 'bg-blue-600 hover:bg-blue-500' },
                      { type: 'not_helpful', label: '❌ Not Helpful', color: 'bg-neutral-600 hover:bg-neutral-500' },
                    ].map(({ type, label, color }) => (
                      <button
                        key={type}
                        onClick={async () => {
                          try {
                            await api.post(`/ideas/${id}/feedback`, { feedback_type: type });
                            toast.success(`${label.split(' ').slice(1).join(' ')} recorded!`);
                          } catch (err) {
                            toast.error(err.response?.data?.error || 'Failed');
                          }
                        }}
                        className={`px-4 py-2 rounded-lg text-sm font-medium dark:text-white text-neutral-900 transition-colors ${color}`}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </Card>
              </motion.div>

              {/* Detailed Feedback Section */}
              <motion.div variants={fadeIn}>
                <Card className="p-8">
                  <h2 className="text-sm font-semibold dark:text-neutral-300 text-neutral-600 uppercase tracking-widest mb-6">
                    Share Your Feedback
                  </h2>
                  <p className="dark:text-neutral-400 text-neutral-500 mb-6">
                    Help improve the system by providing feedback on this idea.
                  </p>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium dark:text-neutral-300 text-neutral-600 mb-3">
                        Feedback Type
                      </label>
                      <select
                        value={feedbackType}
                        onChange={(e) => setFeedbackType(e.target.value)}
                        className="w-full h-10 rounded-lg border border-neutral-700 dark:bg-neutral-800 bg-neutral-100 px-3 py-2 text-sm dark:text-white text-neutral-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
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

                    <div>
                      <label className="block text-sm font-medium dark:text-neutral-300 text-neutral-600 mb-3">
                        Comment (Optional)
                      </label>
                      <Textarea
                        value={feedbackComment}
                        onChange={(e) => setFeedbackComment(e.target.value.slice(0, 1000))}
                        placeholder="Add context, references, or additional insights..."
                        className="h-24 resize-none"
                      />
                      <p className="text-xs text-neutral-600 mt-1">{feedbackComment.length}/1000</p>
                    </div>

                    <Button
                      onClick={handleFeedbackSubmit}
                      disabled={!feedbackType || submittingFeedback}
                      className="w-full"
                    >
                      {submittingFeedback ? "Submitting..." : "Submit Feedback"}
                    </Button>
                  </div>
                </Card>
              </motion.div>
            </>
          )}

          {/* Not logged in */}
          {!user && (
            <motion.div variants={fadeIn}>
              <Card className="p-8 border-indigo-500/20 bg-indigo-500/5 text-center">
                <p className="dark:text-neutral-300 text-neutral-600 mb-4">
                  Sign in to provide feedback and see detailed analysis.
                </p>
                <Button asChild>
                  <Link to="/login">Sign in</Link>
                </Button>
              </Card>
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  );
};

export default IdeaDetail;
