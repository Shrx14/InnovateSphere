import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../../context/AuthContext";
import api from "../../../lib/api";
import useDebounce from "../../../hooks/useDebounce";


const ExplorePage = () => {
  const { isAuthenticated, user } = useAuth();
  const [ideas, setIdeas] = useState([]);
  const [domains, setDomains] = useState([]);
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchFocused, setSearchFocused] = useState(false);

  const [filters, setFilters] = useState({
    domain: "",
    q: "",
    page: 1,
  });




  const debouncedSearchQuery = useDebounce(filters.q, 300);

  useEffect(() => {
    setLoading(true);

    const searchFilters = { ...filters, q: debouncedSearchQuery };

    Promise.all([
      api.get("/public/ideas", { params: searchFilters }),
      api.get("/domains"),
    ])
      .then(([ideasRes, domainsRes]) => {
        setIdeas(ideasRes.data.ideas);
        setMeta(ideasRes.data.meta);
        setDomains(domainsRes.data.domains);
      })
      .catch((err) => {
        console.error("Failed to fetch ideas:", err);
        setIdeas([]);
        setMeta(null);
      })
      .finally(() => setLoading(false));
  }, [debouncedSearchQuery, filters.domain, filters.page]);

  return (
    <main className="min-h-screen bg-gradient-to-b from-neutral-950 via-neutral-950 to-neutral-900">
      {/* Background decorations */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-600 rounded-full opacity-10 blur-3xl" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-purple-600 rounded-full opacity-10 blur-3xl" />
      </div>

      <div className="max-w-7xl mx-auto px-6 py-12 md:py-20">
        {/* Header */}
        <div className="mb-12 md:mb-16">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-5xl md:text-6xl font-light text-white">
              Explore Ideas
            </h1>
            {isAuthenticated && (
              <div className="flex items-center gap-2 px-4 py-2 bg-indigo-500/20 rounded-full border border-indigo-500/30">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-sm text-indigo-300">
                  Welcome back{user?.email ? `, ${user.email.split('@')[0]}` : ''}
                </span>
              </div>
            )}
          </div>
          <p className="text-xl text-neutral-300">
            Discover project ideas evaluated with research evidence and novelty scoring.
          </p>
        </div>


        {/* Search and Filter Section */}
        <div className="mb-12 space-y-4">
          {/* Search Bar */}
          <div className={`transition-all duration-300 ${searchFocused ? "scale-105" : ""}`}>
            <div
              className={`glass-card-lg p-6 border transition-all duration-300 ${
                searchFocused ? "border-indigo-500/50 bg-white/10" : "border-white/10"
              }`}
            >
              <label className="block text-sm text-neutral-400 mb-3">
                Search Ideas
              </label>
              <div className="relative">
                <svg
                  className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
                <input
                  placeholder="Search by title, domain, or keywords..."
                  value={filters.q}
                  onChange={(e) => setFilters({ ...filters, q: e.target.value, page: 1 })}
                  onFocus={() => setSearchFocused(true)}
                  onBlur={() => setSearchFocused(false)}
                  className="w-full bg-transparent pl-12 pr-4 py-3 text-white placeholder-neutral-500 focus:outline-none"
                />
              </div>
            </div>
          </div>

          {/* Filter Bar */}
          <div className="glass-card-lg p-6 border border-white/10">
            <label className="block text-sm text-neutral-400 mb-3">
              Filter by Domain
            </label>
            <div className="flex flex-wrap gap-3">
              {/* "All Domains" Button */}
              <button
                onClick={() => setFilters({ ...filters, domain: "", page: 1 })}
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-300 ${
                  filters.domain === ""
                    ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg"
                    : "glass-card hover:bg-white/15 text-neutral-300"
                }`}
              >
                All Domains
              </button>

              {/* Domain Buttons */}
              {domains.map((d) => (
                <button
                  key={d.id}
                  onClick={() => setFilters({ ...filters, domain: d.name, page: 1 })}
                  className={`px-4 py-2 rounded-lg font-medium transition-all duration-300 whitespace-nowrap ${
                    filters.domain === d.name
                      ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg"
                      : "glass-card hover:bg-white/15 text-neutral-300"
                  }`}
                >
                  {d.name}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Results Section */}
        {loading ? (
          <div className="text-center py-20">
            <div className="inline-block">
              <div className="w-12 h-12 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin mx-auto mb-4" />
              <p className="text-neutral-400">Discovering ideas...</p>
            </div>
          </div>
        ) : ideas.length === 0 ? (
          <div className="text-center py-20">
            <div className="inline-block">
              <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 text-neutral-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <p className="text-neutral-400 text-lg">No ideas found</p>
              <p className="text-neutral-500 text-sm mt-2">Try adjusting your search or filters</p>
            </div>
          </div>
        ) : (
          <div>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
              {ideas.map((idea, i) => (
                <Link
                  key={idea.id}
                  to={`/idea/${idea.id}`}
                  className="group glass-card-lg p-8 hover:bg-white/10 transition-all duration-300 transform hover:scale-105 hover:shadow-lg hover:border-indigo-500/50 flex flex-col h-full"
                  style={{
                    animation: `fadeInUp 0.5s ease-out ${i * 50}ms backwards`,
                  }}
                >
                  {/* Domain Badge */}
                  <div className="mb-4">
                    <span className="inline-block px-3 py-1 bg-gradient-to-r from-indigo-500/20 to-purple-500/20 rounded-full text-xs font-semibold text-indigo-300 group-hover:from-indigo-500/40 group-hover:to-purple-500/40 transition">
                      {idea.domain}
                    </span>
                  </div>

                  {/* Title */}
                  <h3 className="text-xl font-semibold text-white mb-3 group-hover:text-indigo-300 transition line-clamp-2 flex-grow">
                    {idea.title}
                  </h3>

                  {/* Problem Statement */}
                  <p className="text-sm text-neutral-300 line-clamp-3 mb-6 leading-relaxed">
                    {idea.problem_statement}
                  </p>

                  {/* Scores */}
                  <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/10">
                    <div className="group/stat">
                      <div className="text-sm font-bold text-indigo-400 group-hover/stat:text-indigo-300 transition">
                        {typeof idea.novelty_score === 'number' ? (idea.novelty_score / 10).toFixed(1) : 'N/A'}
                      </div>
                      <div className="text-xs text-neutral-500">Novelty</div>
                    </div>
                    <div className="group/stat">
                      <div className="text-sm font-bold text-purple-400 group-hover/stat:text-purple-300 transition">
                        {typeof idea.quality_score === 'number' ? (idea.quality_score / 10).toFixed(1) : 'N/A'}
                      </div>
                      <div className="text-xs text-neutral-500">Quality</div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>

            {/* Pagination */}
            {meta && meta.pages > 1 && (
              <div className="flex justify-center items-center gap-2 mb-8">
                <button
                  onClick={() => setFilters({ ...filters, page: Math.max(1, meta.page - 1) })}
                  disabled={meta.page === 1 || loading}
                  className="px-4 py-2 rounded-lg glass-card text-neutral-300 hover:text-white hover:bg-white/15 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  ← Previous
                </button>

                <div className="flex gap-2">
                  {Array.from({ length: meta.pages }).map((_, i) => {
                    const pageNum = i + 1;
                    // Show only nearby pages to avoid too many buttons
                    if (
                      pageNum === 1 ||
                      pageNum === meta.pages ||
                      (pageNum >= meta.page - 1 && pageNum <= meta.page + 1)
                    ) {
                      return (
                        <button
                          key={i}
                          onClick={() => setFilters({ ...filters, page: pageNum })}
                          disabled={loading}
                          className={`px-4 py-2 rounded-lg font-medium transition-all duration-300 ${
                            meta.page === pageNum
                              ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg"
                              : "glass-card text-neutral-300 hover:text-white hover:bg-white/15"
                          } disabled:opacity-50 disabled:cursor-not-allowed`}
                        >
                          {pageNum}
                        </button>
                      );
                    }
                    if ((i === 1 && meta.page > 3) || (i === meta.pages - 2 && meta.page < meta.pages - 2)) {
                      return (
                        <span key={i} className="text-neutral-500">
                          ...
                        </span>
                      );
                    }
                    return null;
                  })}
                </div>

                <button
                  onClick={() => setFilters({ ...filters, page: Math.min(meta.pages, meta.page + 1) })}
                  disabled={meta.page === meta.pages || loading}
                  className="px-4 py-2 rounded-lg glass-card text-neutral-300 hover:text-white hover:bg-white/15 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  Next →
                </button>
              </div>
            )}
          </div>
        )}
      </div>

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
    </main>
  );
};

export default ExplorePage;
