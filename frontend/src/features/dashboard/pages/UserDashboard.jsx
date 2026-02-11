import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../../../lib/api";

export default function UserDashboard() {
  const [ideas, setIdeas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("all");

  useEffect(() => {
    api.get("/ideas/mine")
      .then(res => setIdeas(res.data.ideas || []))
      .finally(() => setLoading(false));
  }, []);

  const grouped = {
    all: ideas,
    validated: ideas.filter(i => i.status === "validated"),
    pending: ideas.filter(i => i.status === "pending"),
    rejected: ideas.filter(i => i.status === "rejected" || i.status === "downgraded"),
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "validated":
        return "✓";
      case "pending":
        return "⏳";
      case "rejected":
      case "downgraded":
        return "✕";
      default:
        return "→";
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "validated":
        return "from-emerald-500/20 to-teal-500/20 border-emerald-500/30 text-emerald-300";
      case "pending":
        return "from-yellow-500/20 to-orange-500/20 border-yellow-500/30 text-yellow-300";
      case "rejected":
      case "downgraded":
        return "from-red-500/20 to-pink-500/20 border-red-500/30 text-red-300";
      default:
        return "from-blue-500/20 to-indigo-500/20 border-blue-500/30 text-blue-300";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-neutral-950 via-neutral-950 to-neutral-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-neutral-400">Loading your ideas...</p>
        </div>
      </div>
    );
  }

  if (ideas.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-neutral-950 via-neutral-950 to-neutral-900 flex items-center justify-center px-6">
        <div className="text-center max-w-md">
          <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center mx-auto mb-6">
            <span className="text-4xl">💡</span>
          </div>
          <h2 className="text-3xl font-light text-white mb-3">
            No ideas yet
          </h2>
          <p className="text-neutral-400 mb-8">
            Start generating innovative ideas based on research evidence.
          </p>
          <Link
            to="/user/generate"
            className="btn-primary inline-flex items-center justify-center gap-2"
          >
            <span>✨ Generate Your First Idea</span>
            <span>→</span>
          </Link>
        </div>
      </div>
    );
  }

  const currentIdeas = grouped[activeTab];

  return (
    <div className="min-h-screen bg-gradient-to-b from-neutral-950 via-neutral-950 to-neutral-900">
      {/* Background decorations */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-600 rounded-full opacity-10 blur-3xl" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-purple-600 rounded-full opacity-10 blur-3xl" />
      </div>

      <div className="max-w-6xl mx-auto px-6 py-12 md:py-20 relative z-10">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-5xl md:text-6xl font-light text-white mb-2">
            Your Ideas
          </h1>
          <p className="text-xl text-neutral-300">
            Track the status and performance of your generated ideas.
          </p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6 mb-12">
          <div className="glass-card-lg p-6 text-center transform hover:scale-105 transition-transform duration-300">
            <div className="text-3xl font-bold text-white mb-2">
              {ideas.length}
            </div>
            <p className="text-sm text-neutral-400">Total Ideas</p>
          </div>
          <div className="glass-card-lg p-6 text-center transform hover:scale-105 transition-transform duration-300">
            <div className="text-3xl font-bold text-emerald-400 mb-2">
              {grouped.validated.length}
            </div>
            <p className="text-sm text-neutral-400">Validated</p>
          </div>
          <div className="glass-card-lg p-6 text-center transform hover:scale-105 transition-transform duration-300">
            <div className="text-3xl font-bold text-yellow-400 mb-2">
              {grouped.pending.length}
            </div>
            <p className="text-sm text-neutral-400">Pending</p>
          </div>
          <div className="glass-card-lg p-6 text-center transform hover:scale-105 transition-transform duration-300">
            <div className="text-3xl font-bold text-red-400 mb-2">
              {grouped.rejected.length}
            </div>
            <p className="text-sm text-neutral-400">Rejected</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-8">
          <div className="glass-card-lg p-2 border border-white/10 inline-flex gap-2">
            {[
              { key: "all", label: "All Ideas", count: grouped.all.length },
              { key: "validated", label: "Validated", count: grouped.validated.length },
              { key: "pending", label: "Pending", count: grouped.pending.length },
              { key: "rejected", label: "Rejected", count: grouped.rejected.length },
            ].map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-300 whitespace-nowrap ${
                  activeTab === tab.key
                    ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg"
                    : "text-neutral-300 hover:text-white hover:bg-white/10"
                }`}
              >
                {tab.label} ({tab.count})
              </button>
            ))}
          </div>
        </div>

        {/* Ideas List */}
        <div className="space-y-4">
          {currentIdeas.length === 0 ? (
            <div className="text-center py-12 glass-card-lg p-8">
              <p className="text-neutral-400 mb-4">
                {activeTab === "all"
                  ? "No ideas found."
                  : `No ${activeTab} ideas yet.`}
              </p>
              <Link
                to="/user/generate"
                className="text-indigo-400 hover:text-indigo-300 font-medium transition"
              >
                Generate an idea →
              </Link>
            </div>
          ) : (
            currentIdeas.map((idea, i) => (
              <Link
                key={idea.id}
                to={`/idea/${idea.id}`}
                className={`glass-card-lg p-6 md:p-8 hover:bg-white/10 transition-all duration-300 transform hover:scale-102 hover:border-indigo-500/50 group cursor-pointer`}
                style={{
                  animation: `fadeInUp 0.5s ease-out ${i * 50}ms backwards`,
                }}
              >
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-3">
                      <div className={`glass-card p-2 rounded-lg ${getStatusColor(idea.status)}`}>
                        <span className="font-semibold">{getStatusIcon(idea.status)}</span>
                      </div>
                      <div
                        className={`px-3 py-1 rounded-full text-xs font-semibold bg-gradient-to-r ${getStatusColor(
                          idea.status
                        )}`}
                      >
                        {idea.status.charAt(0).toUpperCase() + idea.status.slice(1)}
                      </div>
                    </div>

                    <h3 className="text-lg md:text-xl font-semibold text-white mb-2 group-hover:text-indigo-300 transition line-clamp-2">
                      {idea.title}
                    </h3>

                    <p className="text-sm text-neutral-400 line-clamp-2 mb-4">
                      {idea.problem_statement}
                    </p>

                    <div className="flex flex-wrap gap-6 text-sm">
                      <div>
                        <span className="text-neutral-500">Domain: </span>
                        <span className="text-neutral-300 font-medium">{idea.domain}</span>
                      </div>
                      <div>
                        <span className="text-neutral-500">Novelty: </span>
                        <span className="text-indigo-400 font-bold">
                          {typeof idea.novelty_score === 'number' ? idea.novelty_score.toFixed(1) : 'N/A'}
                        </span>
                      </div>
                      <div>
                        <span className="text-neutral-500">Quality: </span>
                        <span className="text-purple-400 font-bold">
                          {typeof idea.quality_score === 'number' ? idea.quality_score.toFixed(1) : 'N/A'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Arrow Icon */}
                  <div className="flex-shrink-0 text-indigo-400 group-hover:translate-x-2 transition-transform">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>
              </Link>
            ))
          )}
        </div>

        {/* Generate More Button */}
        <div className="text-center mt-12">
          <Link
            to="/user/generate"
            className="btn-primary inline-flex items-center justify-center gap-2"
          >
            <span>✨ Generate Another Idea</span>
            <span>→</span>
          </Link>
        </div>
      </div>

      <style>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
}
