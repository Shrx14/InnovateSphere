import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, ArrowRight, AlertCircle, RotateCcw, ExternalLink } from 'lucide-react';

import { useGeneration } from '@/hooks/useGeneration';
import { formatScore } from '@/lib/formatScore';
import { fadeIn, staggerContainer } from '@/lib/motion';
import { cn } from '@/lib/utils';

import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { Textarea } from '@/components/ui/Textarea';
import { Badge } from '@/components/ui/Badge';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { ScoreDisplay } from '@/components/ui/ScoreDisplay';
import { Skeleton, SkeletonText } from '@/components/ui/Skeleton';

const GeneratePage = () => {
  const navigate = useNavigate();
  const gen = useGeneration();

  return (
    <div className="min-h-screen">
      <div className="max-w-4xl mx-auto px-6 py-12 md:py-20">
        {/* Header */}
        <motion.div
          variants={fadeIn}
          initial="hidden"
          animate="visible"
          className="mb-12 md:mb-16"
        >
          <h1 className="text-5xl md:text-6xl font-light text-white mb-4">
            Generate Idea
          </h1>
          <p className="text-xl text-neutral-300
            Create innovative project ideas evaluated with research evidence and real-time novelty scoring.
          </p>
        </motion.div>

        <AnimatePresence mode="wait">
          {/* ==================== GENERATING STATE ==================== */}
          {gen.isGenerating && (
            <motion.div
              key="generating"
              variants={fadeIn}
              initial="hidden"
              animate="visible"
              exit="exit"
            >
              <Card className="p-8 md:p-12 border-neutral-800 glow-border">
                <CardContent className="space-y-8">
                  <div className="text-center space-y-3">
                    <motion.div
                      animate={{ opacity: [0.5, 1, 0.5] }}
                      transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                      className="text-indigo-400 text-sm font-medium uppercase tracking-widest"
                    >
                      {gen.phaseName || 'Starting generation…'}
                    </motion.div>
                  </div>

                  <ProgressBar value={gen.progress} label={gen.phaseName} />

                  {/* Intermediate results reveal */}
                  <div className="space-y-3">
                    <AnimatePresence>
                      {gen.sourcesCount > 0 && (
                        <motion.div
                          variants={fadeIn}
                          initial="hidden"
                          animate="visible"
                          className="flex items-center gap-2 text-sm text-neutral-400
                        >
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                          Found {gen.sourcesCount} relevant sources
                        </motion.div>
                      )}
                      {gen.noveltyScore != null && (
                        <motion.div
                          variants={fadeIn}
                          initial="hidden"
                          animate="visible"
                          className="flex items-center gap-2 text-sm text-neutral-400
                        >
                          <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
                          Novelty: {formatScore(gen.noveltyScore)}/10
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>

                  {/* Skeleton preview of result layout */}
                  <div className="space-y-4 pt-4 border-t border-neutral-800">
                    <Skeleton className="h-8 w-3/4" />
                    <SkeletonText lines={3} />
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {[0, 1, 2, 3].map(i => (
                        <Skeleton key={i} className="h-20 rounded-xl" />
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* ==================== RESULT STATE ==================== */}
          {gen.isComplete && gen.result && (
            <motion.div
              key="result"
              variants={fadeIn}
              initial="hidden"
              animate="visible"
              exit="exit"
            >
              <Card className="p-8 md:p-12 border-indigo-500/30 glow-border-pulse card-shine overflow-hidden">
                <CardContent className="space-y-8">
                  {/* Success indicator */}
                  <Badge variant="success" className="text-sm px-3 py-1">
                    Idea Generated
                  </Badge>

                  {/* Title */}
                  <h2 className="text-3xl md:text-4xl font-bold text-white leading-tight">
                    {gen.result.title}
                  </h2>

                  {/* Content Grid */}
                  <div className="grid md:grid-cols-2 gap-8">
                    <div className="space-y-3">
                      <p className="text-xs text-indigo-400 uppercase tracking-widest font-semibold">
                        Problem Statement
                      </p>
                      <p className="text-base text-neutral-300 leading-relaxed">
                        {gen.result.problem_statement}
                      </p>
                    </div>
                    <div className="space-y-3">
                      <p className="text-xs text-neutral-400 uppercase tracking-widest font-semibold">
                        Suggested Tech Stack
                      </p>
                      {(() => {
                        const tsJson = gen.result.idea?.tech_stack_json || gen.result.tech_stack_json;
                        if (tsJson && Array.isArray(tsJson) && tsJson.length > 0) {
                          return (
                            <div className="grid gap-3 sm:grid-cols-2">
                              {tsJson.map((item, idx) => {
                                const name = item.component || item.name || "Technology";
                                const techs = item.technologies;
                                const desc = item.rationale || item.role || "";
                                const extra = item.justification || "";
                                return (
                                  <div key={idx} className="rounded-lg border border-neutral-700 bg-neutral-800/50 p-3">
                                    <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                                      <span className="text-sm font-semibold text-indigo-400">{name}</span>
                                      {techs && techs.length > 0 && techs.map((t, i) => (
                                        <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                                          {t}
                                        </span>
                                      ))}
                                    </div>
                                    {desc && <p className="text-xs text-neutral-400 leading-relaxed">{desc}</p>}
                                    {extra && <p className="text-xs text-neutral-500 mt-1 italic">{extra}</p>}
                                  </div>
                                );
                              })}
                            </div>
                          );
                        }
                        return (
                          <p className="text-base text-neutral-300 leading-relaxed">
                            {gen.result.tech_stack}
                          </p>
                        );
                      })()}
                    </div>
                  </div>

                  {/* Divider */}
                  <div className="h-px bg-neutral-800 />

                  {/* Metrics */}
                  <motion.div
                    variants={staggerContainer}
                    initial="hidden"
                    animate="visible"
                    className="grid grid-cols-2 md:grid-cols-4 gap-4"
                  >
                    <motion.div variants={fadeIn}>
                      <Card className="p-4 text-center bg-neutral-900/50">
                        <div className="text-lg font-bold text-white mb-1">
                          {gen.result.domain}
                        </div>
                        <p className="text-xs text-neutral-500
                      </Card>
                    </motion.div>
                    <motion.div variants={fadeIn}>
                      <Card className="p-4 text-center bg-neutral-900/50">
                        <ScoreDisplay value={gen.result.novelty_score} label="Novelty" className="justify-center" />
                      </Card>
                    </motion.div>
                    <motion.div variants={fadeIn}>
                      <Card className="p-4 text-center bg-neutral-900/50">
                        <ScoreDisplay value={gen.result.quality_score} label="Quality" className="justify-center" />
                      </Card>
                    </motion.div>
                    <motion.div variants={fadeIn}>
                      <Card className="p-4 text-center bg-neutral-900/50">
                        <div className="text-lg font-bold text-emerald-400 mb-1">Saved</div>
                        <p className="text-xs text-neutral-500
                      </Card>
                    </motion.div>
                  </motion.div>

                  {/* Actions */}
                  <div className="flex flex-col md:flex-row gap-4">
                    <Button
                      variant="secondary"
                      className="flex-1"
                      onClick={gen.reset}
                    >
                      <RotateCcw className="w-4 h-4 mr-2" />
                      Generate Another
                    </Button>
                    <Button
                      className="flex-1"
                      onClick={() => navigate(`/idea/${gen.result.id}`)}
                    >
                      View Full Details
                      <ExternalLink className="w-4 h-4 ml-2" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* ==================== FAILED STATE ==================== */}
          {gen.isFailed && (
            <motion.div
              key="failed"
              variants={fadeIn}
              initial="hidden"
              animate="visible"
              exit="exit"
            >
              <Card className="p-8 border-red-500/20">
                <CardContent className="space-y-6">
                  <div className="flex items-start gap-3 text-red-300">
                    <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="font-medium">Generation failed</p>
                      <p className="text-sm text-red-400 mt-1">{gen.jobError || 'An unexpected error occurred.'}</p>
                    </div>
                  </div>
                  <Button variant="secondary" onClick={gen.reset}>
                    <RotateCcw className="w-4 h-4 mr-2" />
                    Try Again
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* ==================== INPUT FORM ==================== */}
          {!gen.isGenerating && !gen.isComplete && !gen.isFailed && (
            <motion.div
              key="form"
              variants={fadeIn}
              initial="hidden"
              animate="visible"
              exit="exit"
              className="space-y-8"
            >
              {/* Domain Selection Grid */}
              <div>
                <label className="block text-sm font-semibold text-neutral-300 mb-4 uppercase tracking-wide">
                  Select Domain
                </label>
                {gen.domainsLoading ? (
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                    {[0, 1, 2, 3, 4, 5].map(i => (
                      <Skeleton key={i} className="h-20 rounded-2xl" />
                    ))}
                  </div>
                ) : (
                  <motion.div
                    variants={staggerContainer}
                    initial="hidden"
                    animate="visible"
                    className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3"
                  >
                    {gen.domains.map((domain) => (
                      <motion.button
                        key={domain.id}
                        variants={fadeIn}
                        whileHover={{ scale: 1.03, y: -2 }}
                        whileTap={{ scale: 0.97 }}
                        onClick={() => gen.setSelectedDomainId(String(domain.id))}
                        className={cn(
                          'rounded-2xl border p-4 transition-colors text-center glow-border',
                          gen.selectedDomainId === String(domain.id)
                            ? 'bg-indigo-500/15 border-indigo-500/40 text-white shadow-lg shadow-indigo-500/10'
                            : 'bg-neutral-900 border-neutral-800 text-neutral-300 hover:bg-neutral-800 hover:border-neutral-700'
                        )}
                      >
                        <div className="text-sm font-medium truncate">{domain.name}</div>
                      </motion.button>
                    ))}
                  </motion.div>
                )}
              </div>

              {/* Form Card */}
              <Card className="p-8 md:p-12 glow-border">
                <CardContent className="space-y-6">
                  <div>
                    <label className="block text-sm font-semibold text-neutral-300 mb-3 uppercase tracking-wide">
                      Describe Your Idea
                    </label>
                    <Textarea
                      value={gen.query}
                      onChange={(e) => gen.setQuery(e.target.value.slice(0, 2000))}
                      placeholder="e.g., 'Build an AI system that detects rare diseases using retinal imaging' or 'Create a blockchain-based supply chain tracking system for pharmaceutical companies'..."
                      rows={5}
                      className="resize-none"
                    />
                    <div className="flex justify-between items-center mt-2">
                      <p className="text-xs text-neutral-500
                        Be specific about the problem you're solving
                      </p>
                      <p className={cn(
                        'text-xs font-medium',
                        gen.query.length > 1800 ? 'text-yellow-400' : 'text-neutral-500
                      )}>
                        {gen.query.length}/2000
                      </p>
                    </div>
                  </div>

                  {/* Error Display */}
                  <AnimatePresence>
                    {gen.submitError && (
                      <motion.div
                        variants={fadeIn}
                        initial="hidden"
                        animate="visible"
                        exit="exit"
                        className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-300 text-sm flex items-start gap-3"
                      >
                        <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                        {gen.submitError}
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Generate Button */}
                  <Button
                    onClick={gen.submit}
                    disabled={gen.submitting || !gen.selectedDomainId || !gen.query.trim()}
                    size="lg"
                    className="w-full"
                  >
                    {gen.submitting ? (
                      <>
                        <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                        Starting…
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4 mr-2" />
                        Generate Idea
                        <ArrowRight className="w-4 h-4 ml-2" />
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default GeneratePage;
