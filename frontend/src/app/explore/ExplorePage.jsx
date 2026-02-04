import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../../shared/api";
import useDebounce from "../../hooks/useDebounce";

const ExplorePage = () => {
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
      .finally(() => setLoading(false));
  }, [filters.domain, filters.page, debouncedSearchQuery]);

  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      <h1 className="text-4xl font-light mb-2">Explore ideas</h1>
      <p className="text-neutral-400 mb-8">
        Publicly available project ideas. Sign in for novelty and analysis.
      </p>

      {/* Filters */}
      <div className="grid md:grid-cols-3 gap-4 mb-8">
        <select
          value={filters.domain}
          onChange={(e) => setFilters({ ...filters, domain: e.target.value, page: 1 })}
        >
          <option value="">All domains</option>
          {domains.map(d => (
            <option key={d.id} value={d.name}>{d.name}</option>
          ))}
        </select>

        <input
          placeholder="Search ideas"
          value={filters.q}
          onChange={(e) => setFilters({ ...filters, q: e.target.value, page: 1 })}
        />
      </div>

      {/* Results */}
      {loading ? (
        <p className="text-neutral-400">Loading ideas…</p>
      ) : ideas.length === 0 ? (
        <p className="text-neutral-400">No ideas found.</p>
      ) : (
        <div className="grid md:grid-cols-3 gap-6">
          {ideas.map(i => (
            <Link
              key={i.id}
              to={`/idea/${i.id}`}
              className="border border-neutral-800 rounded-xl p-6 hover:bg-neutral-800/40"
            >
              <h3 className="text-lg font-medium">{i.title}</h3>
              <p className="text-sm text-neutral-400 mt-2 line-clamp-3">
                {i.problem_statement}
              </p>
              <div className="mt-4 text-xs text-neutral-500">{i.domain}</div>
            </Link>
          ))}
        </div>
      )}

      {/* Pagination */}
      {meta && meta.pages > 1 && (
        <div className="mt-10 flex gap-2">
          {Array.from({ length: meta.pages }).map((_, i) => (
            <button
              key={i}
              onClick={() => setFilters({ ...filters, page: i + 1 })}
              disabled={loading}
              className={`px-3 py-1 rounded ${
                meta.page === i + 1 ? "bg-white text-black" : "border border-neutral-700"
              } ${loading ? "opacity-50 cursor-not-allowed" : ""}`}
            >
              {i + 1}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default ExplorePage;
