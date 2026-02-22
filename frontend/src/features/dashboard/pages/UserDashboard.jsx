import { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, ArrowRight, ChevronRight } from 'lucide-react';

import { useIdeas } from '@/hooks/useIdeas';

import { fadeIn, staggerContainer } from '@/lib/motion';
import { cn } from '@/lib/utils';

import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs';
import { ScoreDisplay } from '@/components/ui/ScoreDisplay';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { EmptyState } from '@/components/ui/EmptyState';
import { SkeletonCard, SkeletonMetric } from '@/components/ui/Skeleton';

const SORT_OPTIONS = [
  { value: 'recent', label: 'Most Recent' },
  { value: 'novelty_desc', label: 'Novelty (High)' },
  { value: 'novelty_asc', label: 'Novelty (Low)' },
  { value: 'quality_desc', label: 'Quality (High)' },
  { value: 'quality_asc', label: 'Quality (Low)' },
];

function sortIdeas(ideas, sortBy) {
  const sorted = [...ideas];
  switch (sortBy) {
    case 'novelty_desc': return sorted.sort((a, b) => (b.novelty_score || 0) - (a.novelty_score || 0));
    case 'novelty_asc': return sorted.sort((a, b) => (a.novelty_score || 0) - (b.novelty_score || 0));
    case 'quality_desc': return sorted.sort((a, b) => (b.quality_score || 0) - (a.quality_score || 0));
    case 'quality_asc': return sorted.sort((a, b) => (a.quality_score || 0) - (b.quality_score || 0));
    case 'recent': return sorted.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    default: return sorted;
  }
}

export default function UserDashboard() {
  const { ideas, loading, grouped, error } = useIdeas();
  const [sortBy, setSortBy] = useState('recent');

  // Loading state with skeletons
  if (loading) {
    return (
      <div className="min-h-screen bg-neutral-950">
        <div className="max-w-6xl mx-auto px-6 py-12 md:py-20">
          <div className="mb-12">
            <div className="h-12 w-64 bg-neutral-800 rounded-lg mb-4" />
            <div className="h-6 w-96 bg-neutral-800 rounded-lg" />
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6 mb-12">
            {[0, 1, 2, 3].map(i => <SkeletonMetric key={i} />)}
          </div>
          <div className="space-y-4">
            {[0, 1, 2].map(i => <SkeletonCard key={i} />)}
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-neutral-950 flex items-center justify-center px-6">
        <EmptyState
          title="Failed to load ideas"
          description={error}
          action={
            <Button onClick={() => window.location.reload()}>
              Try Again
            </Button>
          }
        />
      </div>
    );
  }

  // Empty state
  if (ideas.length === 0) {
    return (
      <div className="min-h-screen bg-neutral-950 flex items-center justify-center px-6">
        <EmptyState
          title="No ideas yet"
          description="Start generating innovative ideas based on research evidence."
          action={
            <Button asChild>
              <Link to="/user/generate">
                <Sparkles className="w-4 h-4 mr-2" />
                Generate Your First Idea
                <ArrowRight className="w-4 h-4 ml-2" />
              </Link>
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-950">
      <div className="max-w-6xl mx-auto px-6 py-12 md:py-20">
        {/* Header */}
        <motion.div variants={fadeIn} initial="hidden" animate="visible" className="mb-12">
          <h1 className="text-5xl md:text-6xl font-light text-white mb-2">Your Ideas</h1>
          <p className="text-xl text-neutral-300">
            Track the status and performance of your generated ideas.
          </p>
        </motion.div>

        {/* Stats Overview */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6 mb-12"
        >
          {[
            { label: 'Total Ideas', value: ideas.length, color: 'text-white' },
            { label: 'Validated', value: grouped.validated.length, color: 'text-emerald-400' },
            { label: 'Pending', value: grouped.pending.length, color: 'text-yellow-400' },
            { label: 'Rejected', value: grouped.rejected.length, color: 'text-red-400' },
          ].map(stat => (
            <motion.div key={stat.label} variants={fadeIn}>
              <Card className="p-6 text-center">
                <div className={cn('text-3xl font-bold mb-2', stat.color)}>{stat.value}</div>
                <p className="text-sm text-neutral-400">{stat.label}</p>
              </Card>
            </motion.div>
          ))}
        </motion.div>

        {/* Tabs */}
        <Tabs defaultValue="all" className="mb-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
            <TabsList>
              <TabsTrigger value="all">All ({grouped.all.length})</TabsTrigger>
              <TabsTrigger value="validated">Validated ({grouped.validated.length})</TabsTrigger>
              <TabsTrigger value="pending">Pending ({grouped.pending.length})</TabsTrigger>
              <TabsTrigger value="rejected">Rejected ({grouped.rejected.length})</TabsTrigger>
            </TabsList>

            <select
              value={sortBy}
              onChange={e => setSortBy(e.target.value)}
              className="h-10 rounded-lg border border-neutral-700 bg-neutral-800/50 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {SORT_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          {['all', 'validated', 'pending', 'rejected'].map(tab => (
            <TabsContent key={tab} value={tab}>
              <IdeaList ideas={sortIdeas(grouped[tab], sortBy)} tab={tab} />
            </TabsContent>
          ))}
        </Tabs>

        {/* Generate More Button */}
        <div className="text-center mt-12">
          <Button asChild>
            <Link to="/user/generate">
              <Sparkles className="w-4 h-4 mr-2" />
              Generate Another Idea
              <ArrowRight className="w-4 h-4 ml-2" />
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}

function IdeaList({ ideas, tab }) {
  if (ideas.length === 0) {
    return (
      <Card className="p-8 text-center">
        <p className="text-neutral-400 mb-4">
          {tab === 'all' ? 'No ideas found.' : `No ${tab} ideas yet.`}
        </p>
        <Link to="/user/generate" className="text-indigo-400 hover:text-indigo-300 font-medium transition">
          Generate an idea <ArrowRight className="w-4 h-4 inline ml-1" />
        </Link>
      </Card>
    );
  }

  return (
    <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-4">
      {ideas.map(idea => (
        <motion.div key={idea.id} variants={fadeIn}>
          <Link to={`/idea/${idea.id}`}>
            <Card className="p-6 md:p-8 hover:bg-neutral-800/50 transition-colors cursor-pointer group">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-3">
                    <StatusBadge status={idea.status} />
                    {idea.domain && <Badge>{idea.domain}</Badge>}
                  </div>
                  <h3 className="text-lg md:text-xl font-semibold text-white mb-2 group-hover:text-indigo-300 transition line-clamp-2">
                    {idea.title}
                  </h3>
                  <p className="text-sm text-neutral-400 line-clamp-2 mb-4">
                    {idea.problem_statement}
                  </p>
                  <div className="flex flex-wrap gap-4 text-sm">
                    <ScoreDisplay value={idea.novelty_score} label="Novelty" />
                    <ScoreDisplay value={idea.quality_score} label="Quality" />
                  </div>
                </div>
                <ChevronRight className="w-5 h-5 text-neutral-600 group-hover:text-indigo-400 transition flex-shrink-0 hidden md:block" />
              </div>
            </Card>
          </Link>
        </motion.div>
      ))}
    </motion.div>
  );
}
