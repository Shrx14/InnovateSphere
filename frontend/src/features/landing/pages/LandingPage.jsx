import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion, useInView } from "framer-motion";
import { ArrowRight, ExternalLink } from "lucide-react";

import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import { fadeIn, staggerContainer } from "@/lib/motion";
import { formatScore } from "@/lib/formatScore";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ScoreDisplay } from "@/components/ui/ScoreDisplay";
import { SkeletonCard } from "@/components/ui/Skeleton";

const AnimatedCounter = ({ target, label, sub }) => {
  const [count, setCount] = useState(0);
  const ref = React.useRef(null);
  const isInView = useInView(ref, { once: true });

  useEffect(() => {
    if (!target || !isInView) return;
    let current = 0;
    const increment = Math.ceil(target / 50);
    const timer = setInterval(() => {
      current += increment;
      if (current >= target) {
        current = target;
        clearInterval(timer);
      }
      setCount(current);
    }, 20);
    return () => clearInterval(timer);
  }, [target, isInView]);

  return (
    <Card className="p-8 md:p-12 text-center" ref={ref}>
      <div className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent mb-4">
        {count.toLocaleString()}
      </div>
      <p className="text-neutral-300 font-medium">{label}</p>
      <p className="text-neutral-500 text-sm mt-2">{sub}</p>
    </Card>
  );
};

const LandingPage = () => {
  const [topIdeas, setTopIdeas] = useState([]);
  const [topDomains, setTopDomains] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    Promise.all([
      api.get("/public/top-ideas").then((r) => r.data),
      api.get("/public/top-domains").then((r) => r.data),
      api.get("/public/stats").then((r) => r.data),
    ])
      .then(([ideas, domains, statsData]) => {
        setTopIdeas(ideas.ideas || []);
        setTopDomains(domains.domains || []);
        setStats(statsData || {});
        setLoading(false);
      })
      .catch(() => {
        setError('Failed to load data. Please try again later.');
        setLoading(false);
      });
  }, []);

  return (
    <div className="bg-neutral-950 min-h-screen">
      {error && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 bg-red-500/90 text-white px-6 py-3 rounded-lg shadow-lg">
          {error}
        </div>
      )}
      {/* ===== HERO ===== */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        {/* Animated background */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-900/40 via-purple-900/30 to-pink-900/20" />
          <motion.div
            animate={{ x: [0, 30, 0], y: [0, -20, 0] }}
            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            className="absolute top-0 -left-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20"
          />
          <motion.div
            animate={{ x: [0, -30, 0], y: [0, 20, 0] }}
            transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
            className="absolute top-0 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20"
          />
          <motion.div
            animate={{ x: [0, 20, 0], y: [0, 30, 0] }}
            transition={{ duration: 22, repeat: Infinity, ease: "linear" }}
            className="absolute -bottom-8 left-20 w-80 h-80 bg-pink-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20"
          />
        </div>

        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="relative z-10 max-w-4xl mx-auto px-6 text-center py-20"
        >
          <motion.h1
            variants={fadeIn}
            className="text-6xl md:text-7xl font-light tracking-tight mb-8 leading-tight"
          >
            <span className="text-white">Project ideas</span>
            <br />
            <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              from research evidence
            </span>
          </motion.h1>

          <motion.p
            variants={fadeIn}
            className="text-xl md:text-2xl text-neutral-300 leading-relaxed max-w-2xl mx-auto mb-12 font-light"
          >
            InnovateSphere evaluates ideas using evidence and real-time novelty scoring — not hype.
          </motion.p>

          <motion.div variants={fadeIn} className="flex flex-col sm:flex-row justify-center gap-4 mb-16">
            <Button asChild size="lg">
              <Link to="/explore">
                Explore Ideas <ArrowRight className="w-4 h-4 ml-2" />
              </Link>
            </Button>
            <Button asChild variant="secondary" size="lg">
              <Link to="/register">
                Start Building <ExternalLink className="w-4 h-4 ml-2" />
              </Link>
            </Button>
          </motion.div>

          {/* Floating Demo Card */}
          <motion.div
            variants={fadeIn}
            animate={{ y: [0, -8, 0] }}
            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
            className="relative mx-auto max-w-xl"
          >
            <Card className="p-6 md:p-8 border-neutral-700/50">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="text-xs text-neutral-500 uppercase tracking-wider mb-2">Featured Idea</p>
                  <h3 className="text-xl md:text-2xl font-semibold text-white text-left">
                    AI-Powered Healthcare Diagnostics
                  </h3>
                </div>
              </div>
              <p className="text-neutral-400 text-left mb-6 text-sm leading-relaxed">
                Real-time diagnostic system using transformer models for rare disease detection with 94% accuracy.
              </p>
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-neutral-800/50 rounded-xl p-4">
                  <div className="text-2xl font-bold text-indigo-400 mb-1">8.2</div>
                  <div className="text-xs text-neutral-500">Novelty</div>
                </div>
                <div className="bg-neutral-800/50 rounded-xl p-4">
                  <div className="text-2xl font-bold text-purple-400 mb-1">94%</div>
                  <div className="text-xs text-neutral-500">Quality</div>
                </div>
                <div className="bg-neutral-800/50 rounded-xl p-4">
                  <div className="text-2xl font-bold text-pink-400 mb-1">2.4K</div>
                  <div className="text-xs text-neutral-500">Views</div>
                </div>
              </div>
            </Card>
          </motion.div>
        </motion.div>
      </section>

      {/* ===== DOMAINS ===== */}
      <section className="relative py-20 md:py-32 bg-gradient-to-b from-neutral-950 to-neutral-900/50">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            variants={fadeIn}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            className="mb-16"
          >
            <p className="text-xs uppercase tracking-widest text-indigo-400 mb-4 font-semibold">Explore Domains</p>
            <h2 className="text-4xl md:text-5xl font-light text-white">
              Research across <span className="text-indigo-400">{stats?.total_domains || 0}</span> domains
            </h2>
          </motion.div>

          {loading ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[0, 1, 2].map((i) => <SkeletonCard key={i} />)}
            </div>
          ) : topDomains.length === 0 ? (
            <p className="text-neutral-400 text-center py-12">No domains yet.</p>
          ) : (
            <motion.div
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-100px" }}
              className="grid md:grid-cols-2 lg:grid-cols-3 gap-6"
            >
              {topDomains.map((d) => (
                <motion.div key={d.domain || d.id} variants={fadeIn}>
                  <Card className="p-8 hover:bg-neutral-800/50 transition-colors cursor-pointer group">
                    <h3 className="text-xl md:text-2xl font-semibold text-white group-hover:text-indigo-300 transition mb-4">
                      {d.domain}
                    </h3>
                    <p className="text-sm text-neutral-400 group-hover:text-neutral-300 transition">
                      {d.idea_count} {d.idea_count === 1 ? "idea" : "ideas"} · {d.views} views
                    </p>
                  </Card>
                </motion.div>
              ))}
            </motion.div>
          )}
        </div>
      </section>

      {/* ===== TOP IDEAS ===== */}
      <section className="py-20 md:py-32 relative">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            variants={fadeIn}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            className="mb-16"
          >
            <p className="text-xs uppercase tracking-widest text-purple-400 mb-4 font-semibold">Most Viewed</p>
            <h2 className="text-4xl md:text-5xl font-light text-white">
              Top ideas from the community
            </h2>
          </motion.div>

          {loading ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[0, 1, 2].map((i) => <SkeletonCard key={i} />)}
            </div>
          ) : topIdeas.length === 0 ? (
            <p className="text-neutral-400 text-center py-12">No public ideas yet.</p>
          ) : (
            <motion.div
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-100px" }}
              className="grid md:grid-cols-2 lg:grid-cols-3 gap-6"
            >
              {topIdeas.map((idea) => (
                <motion.div key={idea.id} variants={fadeIn}>
                  <Link to={`/idea/${idea.id}`}>
                    <Card className="p-8 hover:bg-neutral-800/50 transition-colors cursor-pointer group flex flex-col h-full">
                      <div className="flex-1">
                        <div className="mb-4">
                          <Badge>{idea.domain}</Badge>
                        </div>
                        <h3 className="text-xl font-semibold text-white mb-3 group-hover:text-purple-300 transition line-clamp-2">
                          {idea.title}
                        </h3>
                        <p className="text-sm text-neutral-400 line-clamp-3 mb-6 leading-relaxed">
                          {idea.problem_statement}
                        </p>
                      </div>
                      <div className="grid grid-cols-2 gap-3 pt-4 border-t border-neutral-800">
                        <ScoreDisplay value={idea.novelty_score} label="Novelty" />
                        <ScoreDisplay value={idea.quality_score} label="Quality" />
                      </div>
                    </Card>
                  </Link>
                </motion.div>
              ))}
            </motion.div>
          )}
        </div>
      </section>

      {/* ===== STATS ===== */}
      {stats && !loading && (
        <section className="py-20 md:py-32 relative bg-gradient-to-b from-neutral-900/50 to-neutral-950">
          <div className="max-w-7xl mx-auto px-6">
            <motion.h2
              variants={fadeIn}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              className="text-4xl md:text-5xl font-light text-white text-center mb-16"
            >
              Trusted by the research community
            </motion.h2>

            <motion.div
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              className="grid md:grid-cols-3 gap-6"
            >
              <motion.div variants={fadeIn}>
                <AnimatedCounter target={stats.total_public_ideas || 0} label="Project Ideas" sub="Evaluated and scored" />
              </motion.div>
              <motion.div variants={fadeIn}>
                <AnimatedCounter target={stats.total_domains || 0} label="Research Domains" sub="Across multiple fields" />
              </motion.div>
              <motion.div variants={fadeIn}>
                <AnimatedCounter target={stats.total_users || 0} label="Active Researchers" sub="Building ideas" />
              </motion.div>
            </motion.div>
          </div>
        </section>
      )}
    </div>
  );
};

export default LandingPage;