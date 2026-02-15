import React, { useEffect, useState, useRef } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../../context/AuthContext";
import api from "../../../lib/api";

const LandingPage = () => {
  const [topIdeas, setTopIdeas] = useState([]);
  const [topDomains, setTopDomains] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [displayedStats, setDisplayedStats] = useState({
    total_public_ideas: 0,
    total_domains: 0,
    total_users: 0,
  });
  const { isAuthenticated } = useAuth();
  const timersRef = useRef([]);

  useEffect(() => {
    Promise.all([
      api.get("/public/top-ideas").then(r => r.data),
      api.get("/public/top-domains").then(r => r.data),
      api.get("/public/stats").then(r => r.data),
    ]).then(([ideas, domains, statsData]) => {
      setTopIdeas(ideas.ideas || []);
      setTopDomains(domains.domains || []);
      setStats(statsData || {});
      setLoading(false);
      
      // Animate stats counters
      if (statsData) {
        animateCounter("ideas", statsData.total_public_ideas || 0);
        animateCounter("domains", statsData.total_domains || 0);
        animateCounter("users", statsData.total_users || 0);
      }
    }).catch(() => {
      setLoading(false);
    });

    // Cleanup timers on unmount
    return () => {
      timersRef.current.forEach(t => clearInterval(t));
    };
  }, []);

  const animateCounter = (key, target) => {
    let current = 0;
    const increment = Math.ceil(target / 50);
    const timer = setInterval(() => {
      current += increment;
      if (current >= target) {
        current = target;
        clearInterval(timer);
      }
      setDisplayedStats(prev => ({
        ...prev,
        [key === "ideas" ? "total_public_ideas" : key === "domains" ? "total_domains" : "total_users"]: current,
      }));
    }, 20);
    timersRef.current.push(timer);
  };

  const HeroSection = () => (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Animated Background Gradient */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 opacity-40" />
        
        {/* Animated Blobs */}
        <div className="absolute top-0 -left-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob" />
        <div className="absolute top-0 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob-delay-2" />
        <div className="absolute -bottom-8 left-20 w-80 h-80 bg-pink-500 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob-delay-4" />
      </div>

      {/* Hero Content */}
      <div className="relative z-10 max-w-4xl mx-auto px-6 text-center py-20">
        {/* Main Heading with Gradient */}
        <h1 className="text-6xl md:text-7xl font-light tracking-tight mb-8 leading-tight">
          <span className="text-white">Project ideas</span>
          <br />
          <span className="gradient-text-animated">from research evidence</span>
        </h1>

        {/* Subheading */}
        <p className="text-xl md:text-2xl text-neutral-300 leading-relaxed max-w-2xl mx-auto mb-12 font-light">
          InnovateSphere evaluates ideas using evidence and real-time novelty scoring — not hype.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row justify-center gap-4 mb-16">
          <Link
            to="/explore"
            className="btn-primary inline-flex items-center justify-center gap-2 whitespace-nowrap"
          >
            <span>Explore Ideas</span>
            <span>→</span>
          </Link>
          <Link
            to="/register"
            className="btn-glass inline-flex items-center justify-center gap-2 whitespace-nowrap"
          >
            <span>Start Building</span>
            <span>↗</span>
          </Link>
        </div>

        {/* Floating Demo Card */}
        <div className="relative mx-auto max-w-xl animate-float">
          <div className="glass-card-lg p-6 md:p-8 border border-white/20">
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="text-xs text-neutral-400 uppercase tracking-wider mb-2">Featured Idea</p>
                <h3 className="text-xl md:text-2xl font-semibold text-white text-left">
                  AI-Powered Healthcare Diagnostics
                </h3>
              </div>
              <div className="flex gap-2">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 opacity-20" />
              </div>
            </div>
            
            <p className="text-neutral-300 text-left mb-6 text-sm leading-relaxed">
              Real-time diagnostic system using transformer models for rare disease detection with 94% accuracy.
            </p>

            {/* Metrics */}
            <div className="grid grid-cols-3 gap-4">
              <div className="glass-card p-4">
                <div className="text-2xl font-bold text-indigo-400 mb-1">8.2</div>
                <div className="text-xs text-neutral-400">Novelty</div>
              </div>
              <div className="glass-card p-4">
                <div className="text-2xl font-bold text-purple-400 mb-1">94%</div>
                <div className="text-xs text-neutral-400">Quality</div>
              </div>
              <div className="glass-card p-4">
                <div className="text-2xl font-bold text-pink-400 mb-1">2.4K</div>
                <div className="text-xs text-neutral-400">Views</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );

  const DomainSection = () => (
    <section className="relative py-20 md:py-32 bg-gradient-to-b from-neutral-950 to-neutral-900/50">
      <div className="max-w-7xl mx-auto px-6">
        <div className="mb-16">
          <p className="text-xs uppercase tracking-widest text-indigo-400 mb-4 font-semibold">Explore Domains</p>
          <h2 className="text-4xl md:text-5xl font-light text-white">
            Research across <span className="text-indigo-400">{displayedStats.total_domains}</span> domains
          </h2>
        </div>

        {loading ? (
          <div className="text-neutral-400 text-center py-12">Loading domains...</div>
        ) : topDomains.length === 0 ? (
          <div className="text-neutral-400 text-center py-12">No domains yet.</div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {topDomains.map((d, i) => (
              <div
                key={i}
                className="group glass-card-lg p-8 hover:bg-white/10 transition-all duration-300 cursor-pointer transform hover:scale-105 hover:border-indigo-500/50"
                style={{
                  animation: `fadeInUp 0.5s ease-out ${i * 50}ms backwards`,
                }}
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-xl md:text-2xl font-semibold text-white group-hover:text-indigo-300 transition">
                      {d.domain}
                    </h3>
                  </div>
                  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500/20 to-purple-500/20 group-hover:from-indigo-500/40 group-hover:to-purple-500/40 transition" />
                </div>
                <p className="text-sm text-neutral-400 group-hover:text-neutral-300 transition">
                  {d.idea_count} {d.idea_count === 1 ? 'idea' : 'ideas'} · {d.views} views
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );

  const TopIdeasSection = () => (
    <section className="py-20 md:py-32 relative">
      {/* Background gradient */}
      <div className="absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-900 rounded-full opacity-10 blur-3xl" />
      </div>

      <div className="max-w-7xl mx-auto px-6">
        <div className="mb-16">
          <p className="text-xs uppercase tracking-widest text-purple-400 mb-4 font-semibold">Most Viewed</p>
          <h2 className="text-4xl md:text-5xl font-light text-white">
            Top ideas from the community
          </h2>
        </div>

        {loading ? (
          <div className="text-neutral-400 text-center py-12">Loading ideas...</div>
        ) : topIdeas.length === 0 ? (
          <div className="text-neutral-400 text-center py-12">No public ideas yet.</div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {topIdeas.map((idea, i) => (
              <Link
                key={idea.id}
                to={`/idea/${idea.id}`}
                className="group glass-card-lg p-8 hover:bg-white/10 transition-all duration-300 transform hover:scale-105 hover:border-purple-500/50 flex flex-col"
                style={{
                  animation: `fadeInUp 0.5s ease-out ${i * 50}ms backwards`,
                }}
              >
                <div className="flex-1">
                  <div className="inline-block mb-4 px-3 py-1 bg-gradient-to-r from-indigo-500/20 to-purple-500/20 rounded-full">
                    <span className="text-xs font-semibold text-indigo-300">{idea.domain}</span>
                  </div>
                  
                  <h3 className="text-xl font-semibold text-white mb-3 group-hover:text-purple-300 transition line-clamp-2">
                    {idea.title}
                  </h3>
                  
                  <p className="text-sm text-neutral-300 line-clamp-3 mb-6 leading-relaxed">
                    {idea.problem_statement}
                  </p>
                </div>

                {/* Scores Section */}
                <div className="grid grid-cols-2 gap-3 pt-4 border-t border-white/10">
                  <div>
                    <div className="text-sm font-bold text-indigo-400">
                      {typeof idea.novelty_score === 'number' ? (idea.novelty_score / 10).toFixed(1) : 'N/A'}
                    </div>
                    <div className="text-xs text-neutral-500">Novelty</div>
                  </div>
                  <div>
                    <div className="text-sm font-bold text-purple-400">
                      {typeof idea.quality_score === 'number' ? (idea.quality_score / 10).toFixed(1) : 'N/A'}
                    </div>
                    <div className="text-xs text-neutral-500">Quality</div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </section>
  );

  const StatsSection = () => (
    stats && !loading && (
      <section className="py-20 md:py-32 relative bg-gradient-to-b from-neutral-900/50 to-neutral-950">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-4xl md:text-5xl font-light text-white text-center mb-16">
            Trusted by the research community
          </h2>

          <div className="grid md:grid-cols-3 gap-6">
            {/* Ideas Counter */}
            <div className="glass-card-lg p-8 md:p-12 text-center transform hover:scale-105 transition-transform duration-300">
              <div className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent mb-4">
                {displayedStats.total_public_ideas.toLocaleString()}
              </div>
              <p className="text-neutral-300 font-medium">Project Ideas</p>
              <p className="text-neutral-500 text-sm mt-2">Evaluated and scored</p>
            </div>

            {/* Domains Counter */}
            <div className="glass-card-lg p-8 md:p-12 text-center transform hover:scale-105 transition-transform duration-300">
              <div className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent mb-4">
                {displayedStats.total_domains.toLocaleString()}
              </div>
              <p className="text-neutral-300 font-medium">Research Domains</p>
              <p className="text-neutral-500 text-sm mt-2">Across multiple fields</p>
            </div>

            {/* Users Counter */}
            <div className="glass-card-lg p-8 md:p-12 text-center transform hover:scale-105 transition-transform duration-300">
              <div className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-pink-400 to-indigo-400 bg-clip-text text-transparent mb-4">
                {displayedStats.total_users.toLocaleString()}
              </div>
              <p className="text-neutral-300 font-medium">Active Researchers</p>
              <p className="text-neutral-500 text-sm mt-2">Building ideas</p>
            </div>
          </div>
        </div>
      </section>
    )
  );

  return (
    <div className="bg-neutral-950 min-h-screen">
      <style>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
      <HeroSection />
      <DomainSection />
      <TopIdeasSection />
      <StatsSection />    </div>
  );
};

export default LandingPage;