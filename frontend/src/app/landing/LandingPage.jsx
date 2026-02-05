import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

const LandingPage = () => {
  const [topIdeas, setTopIdeas] = useState([]);
  const [topDomains, setTopDomains] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch("/api/public/top-ideas").then(r => r.json()),
      fetch("/api/public/top-domains").then(r => r.json()),
      fetch("/api/public/stats").then(r => r.json()),
    ]).then(([ideas, domains, stats]) => {
      setTopIdeas(ideas.ideas || []);
      setTopDomains(domains.domains || []);
      setStats(stats);
      setLoading(false);
    }).catch(() => {
      setLoading(false);
      // silent fail — landing page must never crash
    });
  }, []);

  const HeroStatBlock = () => (
    <section className="animate-fade-in-up max-w-7xl mx-auto px-6 pt-32 pb-20">
      <div className="text-center">
        <h1 className="text-5xl font-light tracking-tight text-white mb-6">
          Project ideas from research evidence.
        </h1>
        <p className="text-lg text-neutral-300 leading-relaxed max-w-2xl mx-auto mb-10">
          This system evaluates ideas using evidence and review — not hype.
        </p>
        <div className="flex justify-center gap-4">
          <Link
            to="/explore"
            className="bg-indigo-600/90 hover:bg-indigo-600 text-white rounded-lg px-6 py-3 font-medium transition-colors"
          >
            Explore ideas
          </Link>
          <Link
            to="/register"
            className="border border-neutral-700 text-neutral-300 rounded-lg px-6 py-3 hover:border-neutral-500"
          >
            Sign up
          </Link>
        </div>
      </div>
    </section>
  );

  const DomainOverview = () => (
    <section className="animate-fade-in-up max-w-7xl mx-auto px-6 mb-20">
      <div className="text-xs uppercase tracking-widest text-neutral-400 mb-8">Top domains</div>
      {loading ? (
        <div className="text-neutral-400">Loading domains...</div>
      ) : topDomains.length === 0 ? (
        <div className="text-neutral-400">No domains yet.</div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {topDomains.map((d, i) => (
            <div key={i} className="bg-neutral-900 border border-neutral-800 rounded-2xl p-8">
              <h3 className="text-xl font-normal text-white mb-2">{d.domain}</h3>
              <p className="text-sm text-neutral-400">{d.idea_count} ideas · {d.views} views</p>
            </div>
          ))}
        </div>
      )}
    </section>
  );

  const TopIdeasPreview = () => (
    <section className="animate-fade-in-up max-w-7xl mx-auto px-6 pb-32">
      <div className="text-xs uppercase tracking-widest text-neutral-400 mb-8">Top ideas</div>
      {loading ? (
        <div className="text-neutral-400">Loading ideas...</div>
      ) : topIdeas.length === 0 ? (
        <div className="text-neutral-400">No public ideas yet.</div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {topIdeas.map((idea) => (
            <Link
              key={idea.id}
              to={`/idea/${idea.id}`}
              className="bg-neutral-900 border border-neutral-800 rounded-2xl p-8 hover:bg-neutral-800/80 transition-colors"
            >
              <h3 className="text-lg text-neutral-100 mb-3">{idea.title}</h3>
              <p className="text-sm text-neutral-400 line-clamp-3 mb-4">
                {idea.problem_statement}
              </p>
              <div className="text-xs text-neutral-500">{idea.domain}</div>
            </Link>
          ))}
        </div>
      )}
      {stats && !loading && (
        <div className="mt-12 text-center text-xs text-neutral-500">
          {stats.total_public_ideas} ideas · {stats.total_domains} domains · {stats.total_users} users
        </div>
      )}
    </section>
  );

  return (
    <div className="bg-neutral-950 min-h-screen">
      <HeroStatBlock />
      <DomainOverview />
      <TopIdeasPreview />
    </div>
  );
};

export default LandingPage;
