import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Search, ChevronLeft, ChevronRight } from "lucide-react";

import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import useDebounce from "@/hooks/useDebounce";
import { fadeIn, staggerContainer, cardHover, cardTap } from "@/lib/motion";
import { cn } from "@/lib/utils";

import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { ScoreDisplay } from "@/components/ui/ScoreDisplay";
import { EmptyState } from "@/components/ui/EmptyState";
import { SkeletonCard } from "@/components/ui/Skeleton";

const ExplorePage = () => {
  const { isAuthenticated, user } = useAuth();
  const [ideas, setIdeas] = useState([]);
  const [domains, setDomains] = useState([]);
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(true);

  const [filters, setFilters] = useState({
    domain: "",
    q: "",
    page: 1,
  });

  const debouncedSearchQuery = useDebounce(filters.q, 300);

  // Fetch domains once on mount
  useEffect(() => {
    api.get("/domains")
      .then((res) => setDomains(res.data.domains))
      .catch(() => { });
  }, []);

  // Fetch ideas on filter/search/page change
  useEffect(() => {
    setLoading(true);
    const searchFilters = { ...filters, q: debouncedSearchQuery };

    api.get("/public/ideas", { params: searchFilters })
      .then((res) => {
        setIdeas(res.data.ideas);
        setMeta(res.data.meta);
      })
      .catch(() => {
        setIdeas([]);
        setMeta(null);
      })
      .finally(() => setLoading(false));
  }, [debouncedSearchQuery, filters.domain, filters.page]);

  return (
    <main className="min-h-screen">
      <div className="max-w-7xl mx-auto px-6 py-12 md:py-20">
        {/* Header */}
        <motion.div variants={fadeIn} initial="hidden" animate="visible" className="mb-12 md:mb-16">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-5xl md:text-6xl font-light text-white">Explore Ideas</h1>
            {isAuthenticated && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex items-center gap-2 px-4 py-2 bg-indigo-500/10 rounded-full border border-indigo-500/20"
              >
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                <span className="text-sm text-indigo-300">
                  Welcome back{user?.email ? `, ${user.email.split("@")[0]}` : ""}
                </span>
              </motion.div>
            )}
          </div>
          <p className="text-xl text-neutral-300">
            Discover project ideas evaluated with research evidence and novelty scoring.
          </p>
        </motion.div>

        {/* Search & Filter */}
        <div className="mb-12 space-y-4">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card className="p-6 glow-border transition-all focus-within:border-indigo-500/40 focus-within:shadow-[0_0_20px_rgba(99,102,241,0.15)]">
              <label className="block text-sm text-neutral-400 mb-3">Search Ideas</label>
              <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-500" />
                <Input
                  placeholder="Search by title, domain, or keywords..."
                  value={filters.q}
                  onChange={(e) => setFilters({ ...filters, q: e.target.value, page: 1 })}
                  className="pl-12"
                />
              </div>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="p-6">
              <label className="block text-sm text-neutral-400 mb-3">Filter by Domain</label>
              <div className="flex flex-wrap gap-2">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setFilters({ ...filters, domain: "", page: 1 })}
                  className={cn(
                    "px-4 py-2 rounded-lg text-sm font-medium transition-all",
                    filters.domain === ""
                      ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/20"
                      : "bg-neutral-800 text-neutral-300 hover:bg-neutral-700"
                  )}
                >
                  All Domains
                </motion.button>
                {domains.map((d) => (
                  <motion.button
                    key={d.id}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setFilters({ ...filters, domain: d.name, page: 1 })}
                    className={cn(
                      "px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap",
                      filters.domain === d.name
                        ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/20"
                        : "bg-neutral-800 text-neutral-300 hover:bg-neutral-700"
                    )}
                  >
                    {d.name}
                  </motion.button>
                ))}
              </div>
            </Card>
          </motion.div>
        </div>

        {/* Results */}
        {loading ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[0, 1, 2, 3, 4, 5].map((i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : ideas.length === 0 ? (
          <EmptyState
            title="No ideas found"
            description="Try adjusting your search or filters"
          />
        ) : (
          <div>
            <motion.div
              variants={staggerContainer}
              initial="hidden"
              animate="visible"
              className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12"
            >
              {ideas.map((idea) => (
                <motion.div key={idea.id} variants={fadeIn}>
                  <Link to={`/idea/${idea.id}`}>
                    <motion.div whileHover={cardHover} whileTap={cardTap}>
                      <Card className="p-8 hover:bg-neutral-800/50 transition-colors cursor-pointer group flex flex-col h-full glow-border card-shine overflow-hidden">
                        <div className="mb-4">
                          <Badge>{idea.domain}</Badge>
                        </div>
                        <h3 className="text-xl font-semibold text-white mb-3 group-hover:text-indigo-300 transition line-clamp-2 flex-grow">
                          {idea.title}
                        </h3>
                        <p className="text-sm text-neutral-400 line-clamp-3 mb-6 leading-relaxed">
                          {idea.problem_statement}
                        </p>
                        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-neutral-800">
                          <ScoreDisplay value={idea.novelty_score} label="Novelty" />
                          <ScoreDisplay value={idea.quality_score} label="Quality" />
                        </div>
                      </Card>
                    </motion.div>
                  </Link>
                </motion.div>
              ))}
            </motion.div>

            {/* Pagination */}
            {meta && meta.pages > 1 && (
              <div className="flex justify-center items-center gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setFilters({ ...filters, page: Math.max(1, meta.page - 1) })}
                  disabled={meta.page === 1 || loading}
                >
                  <ChevronLeft className="w-4 h-4 mr-1" /> Previous
                </Button>

                <div className="flex gap-1">
                  {Array.from({ length: meta.pages }).map((_, i) => {
                    const pageNum = i + 1;
                    if (
                      pageNum === 1 ||
                      pageNum === meta.pages ||
                      (pageNum >= meta.page - 1 && pageNum <= meta.page + 1)
                    ) {
                      return (
                        <Button
                          key={i}
                          variant={meta.page === pageNum ? "default" : "ghost"}
                          size="sm"
                          onClick={() => setFilters({ ...filters, page: pageNum })}
                          disabled={loading}
                        >
                          {pageNum}
                        </Button>
                      );
                    }
                    if (
                      (i === 1 && meta.page > 3) ||
                      (i === meta.pages - 2 && meta.page < meta.pages - 2)
                    ) {
                      return (
                        <span key={i} className="text-neutral-500 px-2 py-1">...</span>
                      );
                    }
                    return null;
                  })}
                </div>

                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setFilters({ ...filters, page: Math.min(meta.pages, meta.page + 1) })}
                  disabled={meta.page === meta.pages || loading}
                >
                  Next <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
};

export default ExplorePage;
