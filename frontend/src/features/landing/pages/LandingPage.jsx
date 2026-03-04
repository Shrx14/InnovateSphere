import React, { useEffect, useState, useRef, useCallback } from "react";
import { Link } from "react-router-dom";
import { motion, useInView, useMotionValue, useTransform, useSpring } from "framer-motion";
import { ArrowRight, ExternalLink, Sparkles, Search, BarChart3, Layers, Bot, BookOpen, Target, ShieldCheck } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip as ChartTooltip, ResponsiveContainer, Cell,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  AreaChart, Area,
} from 'recharts';

import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import { fadeIn, staggerContainer, cardHover, cardTap } from "@/lib/motion";
import { formatScore } from "@/lib/formatScore";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ScoreDisplay } from "@/components/ui/ScoreDisplay";
import { SkeletonCard } from "@/components/ui/Skeleton";

/* ─────────────── Chart Colors ─────────────── */
const CHART_COLORS = [
  '#6366f1', '#818cf8', '#a5b4fc', '#4f46e5', '#7c3aed',
  '#8b5cf6', '#a78bfa', '#c4b5fd', '#5b21b6', '#4338ca',
];
const CHART_COLORS_ALT = [
  '#8b5cf6', '#a855f7', '#c084fc', '#7c3aed', '#9333ea',
  '#6366f1', '#818cf8', '#a78bfa', '#d8b4fe', '#e9d5ff',
];

/* ─────────────── 3D Tilt Card ─────────────── */
const TiltCard = ({ children, className = "" }) => {
  const ref = useRef(null);
  const mouseX = useMotionValue(0.5);
  const mouseY = useMotionValue(0.5);

  const rotateX = useSpring(useTransform(mouseY, [0, 1], [8, -8]), {
    stiffness: 200,
    damping: 20,
  });
  const rotateY = useSpring(useTransform(mouseX, [0, 1], [-8, 8]), {
    stiffness: 200,
    damping: 20,
  });

  const handleMouse = useCallback(
    (e) => {
      const rect = ref.current?.getBoundingClientRect();
      if (!rect) return;
      mouseX.set((e.clientX - rect.left) / rect.width);
      mouseY.set((e.clientY - rect.top) / rect.height);
    },
    [mouseX, mouseY]
  );

  const handleLeave = useCallback(() => {
    mouseX.set(0.5);
    mouseY.set(0.5);
  }, [mouseX, mouseY]);

  return (
    <div className={`tilt-card ${className}`}>
      <motion.div
        ref={ref}
        className="tilt-card-inner"
        style={{ rotateX, rotateY }}
        onMouseMove={handleMouse}
        onMouseLeave={handleLeave}
      >
        {children}
      </motion.div>
    </div>
  );
};

/* ─────────────── Animated Counter ─────────────── */
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
    <motion.div whileHover={cardHover} whileTap={cardTap}>
      <Card className="p-8 md:p-12 text-center glow-border card-shine overflow-hidden" ref={ref}>
        <div className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent mb-4">
          {count.toLocaleString()}
        </div>
        <p className="dark:text-neutral-300 text-neutral-600 font-medium">{label}</p>
        <p className="dark:text-neutral-500 text-neutral-400 text-sm mt-2">{sub}</p>
      </Card>
    </motion.div>
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
    <div className="dark:bg-neutral-950/0 min-h-screen">
      {error && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 bg-red-500/90 dark:text-white text-neutral-900 px-6 py-3 rounded-lg shadow-lg">
          {error}
        </div>
      )}

      {/* ===== HERO ===== */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        {/* Subtle radial accents — kept very low opacity to match black background */}
        <div className="absolute inset-0 -z-10">
          <div
            className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] rounded-full"
            style={{
              background: 'radial-gradient(ellipse, rgba(99,102,241,0.08) 0%, transparent 70%)',
            }}
          />
          <div
            className="absolute bottom-0 left-0 w-[500px] h-[500px] rounded-full"
            style={{
              background: 'radial-gradient(ellipse, rgba(139,92,246,0.05) 0%, transparent 70%)',
            }}
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
            <span className="dark:text-white text-neutral-900">Project ideas</span>
            <br />
            <span className="gradient-text-animated">
              from research evidence
            </span>
          </motion.h1>

          <motion.p
            variants={fadeIn}
            className="text-xl md:text-2xl dark:text-neutral-300 text-neutral-600 leading-relaxed max-w-2xl mx-auto mb-12 font-light"
          >
            InnovateSphere evaluates ideas using evidence and real-time novelty scoring — not hype.
          </motion.p>

          <motion.div variants={fadeIn} className="flex flex-col sm:flex-row justify-center gap-4 mb-16">
            <Button asChild size="lg">
              <Link to="/explore">
                <motion.span
                  className="flex items-center"
                  whileHover={{ x: 2 }}
                >
                  Explore Ideas <ArrowRight className="w-4 h-4 ml-2" />
                </motion.span>
              </Link>
            </Button>
            <Button asChild variant="secondary" size="lg">
              <Link to="/register">
                <motion.span
                  className="flex items-center"
                  whileHover={{ x: 2 }}
                >
                  Start Building <ExternalLink className="w-4 h-4 ml-2" />
                </motion.span>
              </Link>
            </Button>
          </motion.div>

          {/* Floating Featured Card with 3D Tilt — shows top idea from DB */}
          <motion.div variants={fadeIn} className="relative mx-auto max-w-xl">
            <TiltCard>
              <motion.div
                animate={{ y: [0, -8, 0] }}
                transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
              >
                {(() => {
                  const featured = topIdeas[0];
                  const title = featured?.title || "Loading...";
                  const description = featured?.problem_statement || "Discovering the top research idea for you...";
                  const novelty = featured ? formatScore(featured.novelty_score) : "—";
                  const quality = featured ? formatScore(featured.quality_score) : "—";
                  const views = featured?.view_count != null
                    ? (featured.view_count >= 1000 ? `${(featured.view_count / 1000).toFixed(1)}K` : String(featured.view_count))
                    : "—";

                  return (
                    <Link to={featured ? `/idea/${featured.id}` : "#"} className="block">
                      <Card className="p-6 md:p-8 dark:border-neutral-700/50 border-neutral-200 glow-border-pulse card-shine overflow-hidden group">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-3 mb-2">
                              <p className="text-xs dark:text-neutral-500 text-neutral-400 uppercase tracking-wider">Featured Idea</p>
                              {featured?.domain && <Badge>{featured.domain}</Badge>}
                            </div>
                            <h3 className="text-xl md:text-2xl font-semibold dark:text-white text-neutral-900 text-left group-hover:text-indigo-300 transition line-clamp-2">
                              {title}
                            </h3>
                          </div>
                        </div>
                        <p className="dark:text-neutral-400 text-neutral-500 text-left mb-6 text-sm leading-relaxed line-clamp-2">
                          {description}
                        </p>
                        <div className="grid grid-cols-3 gap-4">
                          {[
                            { value: novelty, label: "Novelty", color: "text-indigo-400" },
                            { value: quality, label: "Quality", color: "text-purple-400" },
                            { value: views, label: "Views", color: "text-pink-400" },
                          ].map(({ value, label, color }) => (
                            <motion.div
                              key={label}
                              className="dark:bg-neutral-800/50 bg-neutral-100 rounded-xl p-4"
                              whileHover={{ scale: 1.05, backgroundColor: "rgba(38,38,38,0.8)" }}
                              transition={{ duration: 0.2 }}
                            >
                              <div className={`text-2xl font-bold ${color} mb-1`}>{value}</div>
                              <div className="text-xs dark:text-neutral-500 text-neutral-400">{label}</div>
                            </motion.div>
                          ))}
                        </div>
                      </Card>
                    </Link>
                  );
                })()}
              </motion.div>
            </TiltCard>
          </motion.div>
        </motion.div>
      </section>

      {/* ===== WHY INNOVATESPHERE ===== */}
      <section className="relative py-20 md:py-32">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
          >
            <motion.div variants={fadeIn} className="mb-16 max-w-3xl">
              <p className="text-xs uppercase tracking-widest text-amber-400 mb-4 font-semibold">Why InnovateSphere</p>
              <h2 className="text-4xl md:text-5xl font-light dark:text-white text-neutral-900 mb-6">
                Not another <span className="text-amber-400">chatbot</span>
              </h2>
              <p className="text-lg dark:text-neutral-300 text-neutral-600 leading-relaxed">
                Most idea tools give you generic brainstorming lists. InnovateSphere is a research-grade system
                that generates ideas backed by real evidence, scores their novelty against existing work,
                and evaluates feasibility — so you start with confidence, not guesswork.
              </p>
            </motion.div>

            <motion.div
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              className="grid md:grid-cols-2 gap-6"
            >
              {[
                {
                  icon: Bot,
                  problem: 'Generic chatbot outputs',
                  solution: 'AI grounded in real research papers & evidence',
                  description: 'Every idea is synthesized from credible academic and industry sources — not hallucinated text.',
                  color: 'text-indigo-400',
                  border: 'border-indigo-500/20',
                  bg: 'bg-indigo-500/5',
                },
                {
                  icon: Search,
                  problem: 'Hours of manual literature review',
                  solution: 'Automated novelty scoring in seconds',
                  description: 'Our engine cross-references your idea against existing work and quantifies how original it truly is.',
                  color: 'text-emerald-400',
                  border: 'border-emerald-500/20',
                  bg: 'bg-emerald-500/5',
                },
                {
                  icon: Layers,
                  problem: 'One-size-fits-all suggestions',
                  solution: 'Domain-specific idea generation',
                  description: 'Choose from 10+ research domains. Ideas are tailored to Healthcare, AI, Blockchain, IoT, and more.',
                  color: 'text-purple-400',
                  border: 'border-purple-500/20',
                  bg: 'bg-purple-500/5',
                },
                {
                  icon: BarChart3,
                  problem: 'Subjective "is this good?" guessing',
                  solution: 'Data-driven quality & feasibility scores',
                  description: 'Every idea gets scored on feasibility, impact, and technical depth — measurable, not just a feeling.',
                  color: 'text-amber-400',
                  border: 'border-amber-500/20',
                  bg: 'bg-amber-500/5',
                },
              ].map((item) => (
                <motion.div
                  key={item.solution}
                  variants={fadeIn}
                  whileHover={{ y: -4 }}
                  className={`p-6 md:p-8 rounded-2xl ${item.bg} border ${item.border} backdrop-blur-sm transition-all duration-300`}
                >
                  <item.icon className={`w-8 h-8 ${item.color} mb-5`} />
                  <div className="flex items-start gap-3 mb-2">
                    <span className="text-xs dark:text-neutral-500 text-neutral-400 line-through">{item.problem}</span>
                  </div>
                  <h3 className="text-lg font-display font-semibold dark:text-white text-neutral-900 mb-3">{item.solution}</h3>
                  <p className="text-sm dark:text-neutral-400 text-neutral-500 leading-relaxed">{item.description}</p>
                </motion.div>
              ))}
            </motion.div>

            <motion.div variants={fadeIn} className="mt-10 text-center">
              <Link
                to="/how-it-works"
                className="inline-flex items-center gap-2 text-sm dark:text-neutral-400 text-neutral-500 hover:text-indigo-300 transition group"
              >
                Learn how it works
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>
            </motion.div>
          </motion.div>
        </div>
      </section>
      <section className="relative py-20 md:py-32">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            variants={fadeIn}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            className="mb-16"
          >
            <p className="text-xs uppercase tracking-widest text-indigo-400 mb-4 font-semibold">Explore Domains</p>
            <h2 className="text-4xl md:text-5xl font-light dark:text-white text-neutral-900">
              Research across <span className="text-indigo-400">{stats?.total_domains || 0}</span> domains
            </h2>
          </motion.div>

          {loading ? (
            <div className="grid md:grid-cols-2 gap-6">
              {[0, 1].map((i) => <SkeletonCard key={i} />)}
            </div>
          ) : topDomains.length === 0 ? (
            <p className="dark:text-neutral-400 text-neutral-500 text-center py-12">No domains yet.</p>
          ) : (
            <motion.div
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-100px" }}
              className="grid lg:grid-cols-2 gap-8"
            >
              {/* Left: Bar Chart — Ideas per Domain */}
              <motion.div variants={fadeIn}>
                <Card className="p-6 md:p-8 glow-border overflow-hidden">
                  <p className="text-xs uppercase tracking-widest text-indigo-400 mb-1 font-semibold">Ideas by Domain</p>
                  <p className="text-sm dark:text-neutral-500 text-neutral-400 mb-6">Number of research ideas generated per domain</p>
                  <div className="w-full" style={{ height: Math.max(topDomains.length * 52, 200) }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={topDomains.map(d => ({
                          name: d.domain.length > 20 ? d.domain.slice(0, 18) + '…' : d.domain,
                          fullName: d.domain,
                          ideas: d.idea_count,
                          views: d.views,
                        }))}
                        layout="vertical"
                        margin={{ top: 0, right: 20, bottom: 0, left: 0 }}
                        barCategoryGap="20%"
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
                        <XAxis type="number" stroke="#525252" tick={{ fill: '#737373', fontSize: 12 }} axisLine={false} tickLine={false} />
                        <YAxis type="category" dataKey="name" stroke="#525252" tick={{ fill: '#a3a3a3', fontSize: 12 }} width={140} axisLine={false} tickLine={false} />
                        <ChartTooltip
                          cursor={{ fill: 'rgba(99,102,241,0.08)' }}
                          contentStyle={{
                            background: 'rgba(23,23,23,0.95)',
                            border: '1px solid rgba(99,102,241,0.3)',
                            borderRadius: '12px',
                            backdropFilter: 'blur(12px)',
                            padding: '12px 16px',
                          }}
                          itemStyle={{ color: '#e5e5e5', fontSize: '13px' }}
                          labelStyle={{ color: '#a3a3a3', fontSize: '12px', marginBottom: '4px' }}
                          labelFormatter={(label) => {
                            const item = topDomains.find(d => d.domain.startsWith(label.replace('…', '')));
                            return item ? item.domain : label;
                          }}
                        />
                        <Bar dataKey="ideas" name="Ideas" radius={[0, 6, 6, 0]} maxBarSize={28}>
                          {topDomains.map((_, i) => (
                            <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </Card>
              </motion.div>

              {/* Right: Radial Chart — Views Distribution */}
              <motion.div variants={fadeIn}>
                <Card className="p-6 md:p-8 glow-border overflow-hidden">
                  <p className="text-xs uppercase tracking-widest text-purple-400 mb-1 font-semibold">Views Distribution</p>
                  <p className="text-sm dark:text-neutral-500 text-neutral-400 mb-6">Community engagement across domains</p>
                  <div className="w-full" style={{ height: Math.max(topDomains.length * 52, 200) }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={topDomains.map(d => ({
                          name: d.domain.length > 20 ? d.domain.slice(0, 18) + '…' : d.domain,
                          fullName: d.domain,
                          views: d.views,
                        })).sort((a, b) => b.views - a.views)}
                        layout="vertical"
                        margin={{ top: 0, right: 20, bottom: 0, left: 0 }}
                        barCategoryGap="20%"
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
                        <XAxis type="number" stroke="#525252" tick={{ fill: '#737373', fontSize: 12 }} axisLine={false} tickLine={false} />
                        <YAxis type="category" dataKey="name" stroke="#525252" tick={{ fill: '#a3a3a3', fontSize: 12 }} width={140} axisLine={false} tickLine={false} />
                        <ChartTooltip
                          cursor={{ fill: 'rgba(139,92,246,0.08)' }}
                          contentStyle={{
                            background: 'rgba(23,23,23,0.95)',
                            border: '1px solid rgba(139,92,246,0.3)',
                            borderRadius: '12px',
                            backdropFilter: 'blur(12px)',
                            padding: '12px 16px',
                          }}
                          itemStyle={{ color: '#e5e5e5', fontSize: '13px' }}
                          labelStyle={{ color: '#a3a3a3', fontSize: '12px', marginBottom: '4px' }}
                          labelFormatter={(label) => {
                            const item = topDomains.find(d => d.domain.startsWith(label.replace('…', '')));
                            return item ? item.domain : label;
                          }}
                        />
                        <Bar dataKey="views" name="Views" radius={[0, 6, 6, 0]} maxBarSize={28}>
                          {topDomains.map((_, i) => (
                            <Cell key={i} fill={CHART_COLORS_ALT[i % CHART_COLORS_ALT.length]} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </Card>
              </motion.div>
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
            <h2 className="text-4xl md:text-5xl font-light dark:text-white text-neutral-900">
              Top ideas from the community
            </h2>
          </motion.div>

          {loading ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[0, 1, 2].map((i) => <SkeletonCard key={i} />)}
            </div>
          ) : topIdeas.length === 0 ? (
            <p className="dark:text-neutral-400 text-neutral-500 text-center py-12">No public ideas yet.</p>
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
                    <motion.div whileHover={cardHover} whileTap={cardTap}>
                      <Card className="p-8 dark:hover:bg-neutral-800/50 bg-neutral-100 transition-colors cursor-pointer group flex flex-col h-full glow-border card-shine overflow-hidden">
                        <div className="flex-1">
                          <div className="mb-4">
                            <Badge>{idea.domain}</Badge>
                          </div>
                          <h3 className="text-xl font-semibold dark:text-white text-neutral-900 mb-3 group-hover:text-purple-300 transition line-clamp-2">
                            {idea.title}
                          </h3>
                          <p className="text-sm dark:text-neutral-400 text-neutral-500 line-clamp-3 mb-6 leading-relaxed">
                            {idea.problem_statement}
                          </p>
                        </div>
                        <div className="grid grid-cols-2 gap-3 pt-4 border-t border-neutral-800">
                          <ScoreDisplay value={idea.novelty_score} label="Novelty" />
                          <ScoreDisplay value={idea.quality_score} label="Quality" />
                        </div>
                      </Card>
                    </motion.div>
                  </Link>
                </motion.div>
              ))}
            </motion.div>
          )}
        </div>
      </section>

      {/* ===== IDEA QUALITY ANALYTICS ===== */}
      {!loading && topIdeas.length > 0 && (
        <section className="py-20 md:py-32 relative">
          <div className="max-w-7xl mx-auto px-6">
            <motion.div
              variants={fadeIn}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-100px" }}
              className="mb-16"
            >
              <p className="text-xs uppercase tracking-widest text-emerald-400 mb-4 font-semibold">Quality Analytics</p>
              <h2 className="text-4xl md:text-5xl font-light dark:text-white text-neutral-900">
                Novelty vs Quality scores
              </h2>
            </motion.div>

            <motion.div
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-100px" }}
              className="grid lg:grid-cols-2 gap-8"
            >
              {/* Left: Radar Chart — Score Profiles */}
              <motion.div variants={fadeIn}>
                <Card className="p-6 md:p-8 glow-border overflow-hidden">
                  <p className="text-xs uppercase tracking-widest text-emerald-400 mb-1 font-semibold">Score Profiles</p>
                  <p className="text-sm dark:text-neutral-500 text-neutral-400 mb-6">Novelty & quality across top ideas</p>
                  <div className="w-full" style={{ height: 360 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart
                        data={topIdeas.slice(0, 6).map(idea => ({
                          name: idea.title.length > 25 ? idea.title.slice(0, 23) + '…' : idea.title,
                          Novelty: idea.novelty_score || 0,
                          Quality: idea.quality_score || 0,
                        }))}
                      >
                        <PolarGrid stroke="rgba(255,255,255,0.08)" />
                        <PolarAngleAxis
                          dataKey="name"
                          tick={{ fill: '#a3a3a3', fontSize: 11 }}
                        />
                        <PolarRadiusAxis
                          angle={30}
                          domain={[0, 'auto']}
                          tick={{ fill: '#525252', fontSize: 10 }}
                          axisLine={false}
                        />
                        <Radar name="Novelty" dataKey="Novelty" stroke="#6366f1" fill="#6366f1" fillOpacity={0.2} strokeWidth={2} />
                        <Radar name="Quality" dataKey="Quality" stroke="#10b981" fill="#10b981" fillOpacity={0.15} strokeWidth={2} />
                        <ChartTooltip
                          contentStyle={{
                            background: 'rgba(23,23,23,0.95)',
                            border: '1px solid rgba(99,102,241,0.3)',
                            borderRadius: '12px',
                            backdropFilter: 'blur(12px)',
                            padding: '12px 16px',
                          }}
                          itemStyle={{ color: '#e5e5e5', fontSize: '13px' }}
                          labelStyle={{ color: '#a3a3a3', fontSize: '12px' }}
                        />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="flex items-center justify-center gap-6 mt-4">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-indigo-500" />
                      <span className="text-xs dark:text-neutral-400 text-neutral-500">Novelty</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-emerald-500" />
                      <span className="text-xs dark:text-neutral-400 text-neutral-500">Quality</span>
                    </div>
                  </div>
                </Card>
              </motion.div>

              {/* Right: Area Chart — Score Trends */}
              <motion.div variants={fadeIn}>
                <Card className="p-6 md:p-8 glow-border overflow-hidden">
                  <p className="text-xs uppercase tracking-widest text-indigo-400 mb-1 font-semibold">Score Comparison</p>
                  <p className="text-sm dark:text-neutral-500 text-neutral-400 mb-6">Side-by-side quality & novelty for top ideas</p>
                  <div className="w-full" style={{ height: 360 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart
                        data={topIdeas.slice(0, 8).map((idea, i) => ({
                          name: `#${i + 1}`,
                          fullTitle: idea.title,
                          Novelty: idea.novelty_score || 0,
                          Quality: idea.quality_score || 0,
                          Views: idea.view_count || 0,
                        }))}
                        margin={{ top: 10, right: 10, bottom: 0, left: 10 }}
                      >
                        <defs>
                          <linearGradient id="fillNovelty" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#6366f1" stopOpacity={0.3} />
                            <stop offset="100%" stopColor="#6366f1" stopOpacity={0.02} />
                          </linearGradient>
                          <linearGradient id="fillQuality" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#10b981" stopOpacity={0.3} />
                            <stop offset="100%" stopColor="#10b981" stopOpacity={0.02} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                        <XAxis dataKey="name" stroke="#525252" tick={{ fill: '#a3a3a3', fontSize: 12 }} axisLine={false} tickLine={false} />
                        <YAxis stroke="#525252" tick={{ fill: '#737373', fontSize: 12 }} axisLine={false} tickLine={false} />
                        <ChartTooltip
                          contentStyle={{
                            background: 'rgba(23,23,23,0.95)',
                            border: '1px solid rgba(99,102,241,0.3)',
                            borderRadius: '12px',
                            backdropFilter: 'blur(12px)',
                            padding: '12px 16px',
                          }}
                          itemStyle={{ color: '#e5e5e5', fontSize: '13px' }}
                          labelStyle={{ color: '#a3a3a3', fontSize: '12px' }}
                          labelFormatter={(label) => {
                            const idx = parseInt(label.replace('#', '')) - 1;
                            return topIdeas[idx]?.title || label;
                          }}
                        />
                        <Area type="monotone" dataKey="Novelty" stroke="#6366f1" fill="url(#fillNovelty)" strokeWidth={2} dot={{ r: 4, fill: '#6366f1' }} />
                        <Area type="monotone" dataKey="Quality" stroke="#10b981" fill="url(#fillQuality)" strokeWidth={2} dot={{ r: 4, fill: '#10b981' }} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="flex items-center justify-center gap-6 mt-4">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-indigo-500" />
                      <span className="text-xs dark:text-neutral-400 text-neutral-500">Novelty</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-emerald-500" />
                      <span className="text-xs dark:text-neutral-400 text-neutral-500">Quality</span>
                    </div>
                  </div>
                </Card>
              </motion.div>
            </motion.div>
          </div>
        </section>
      )}

      {/* ===== STATS ===== */}
      {stats && !loading && (
        <section className="py-20 md:py-32 relative">
          <div className="max-w-7xl mx-auto px-6">
            <motion.h2
              variants={fadeIn}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              className="text-4xl md:text-5xl font-light dark:text-white text-neutral-900 text-center mb-16"
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