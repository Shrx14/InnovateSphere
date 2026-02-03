import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../../shared/api';

const ExplorePage = () => {
  const [ideas, setIdeas] = useState([]);
  const [domains, setDomains] = useState([]);
  const [loading, setLoading] = useState(true);

  const [filters, setFilters] = useState({
    domain: '',
    noveltyMin: 0,
    noveltyMax: 100,
    sort: 'newest',
  });

  useEffect(() => {
    setLoading(true);

    Promise.all([
      api.get('/public/ideas'),
      api.get('/public/domains'),
    ])
      .then(([ideasRes, domainsRes]) => {
        setIdeas(ideasRes.data || []);
        setDomains(domainsRes.data || []);
      })
      .finally(() => setLoading(false));
  }, []);

  const filteredIdeas = ideas
    .filter((idea) => {
      if (filters.domain && idea.domain !== filters.domain) return false;
      if (idea.novelty_score < filters.noveltyMin) return false;
      if (idea.novelty_score > filters.noveltyMax) return false;
      return true;
    })
    .sort((a, b) => {
      if (filters.sort === 'most_novel') {
        return b.novelty_score - a.novelty_score;
      }
      return new Date(b.created_at) - new Date(a.created_at);
    });

  const UI_STATE = loading
    ? 'loading'
    : filteredIdeas.length === 0
    ? 'empty'
    : 'populated';

  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-light">Explore ideas</h1>
        <p className="mt-2 text-neutral-400">
          Browse project ideas generated from research evidence and novelty analysis.
        </p>
      </div>

      {/* Filters */}
      <div className="mb-8 bg-neutral-900/60 border border-neutral-800 rounded-lg p-4 grid md:grid-cols-4 gap-4">
        <select
          value={filters.domain}
          onChange={(e) => setFilters({ ...filters, domain: e.target.value })}
          className="bg-neutral-950 border border-neutral-800 rounded px-3 py-2 text-sm text-neutral-200"
        >
          <option value="">All domains</option>
          {domains.map((d) => (
            <option key={d.id} value={d.name}>
              {d.name}
            </option>
          ))}
        </select>

        <input
          type="number"
          min={0}
          max={100}
          value={filters.noveltyMin}
          onChange={(e) =>
            setFilters({ ...filters, noveltyMin: Number(e.target.value) })
          }
          placeholder="Min novelty"
          className="bg-neutral-950 border border-neutral-800 rounded px-3 py-2 text-sm text-neutral-200"
        />

        <input
          type="number"
          min={0}
          max={100}
          value={filters.noveltyMax}
          onChange={(e) =>
            setFilters({ ...filters, noveltyMax: Number(e.target.value) })
          }
          placeholder="Max novelty"
          className="bg-neutral-950 border border-neutral-800 rounded px-3 py-2 text-sm text-neutral-200"
        />

        <select
          value={filters.sort}
          onChange={(e) => setFilters({ ...filters, sort: e.target.value })}
          className="bg-neutral-950 border border-neutral-800 rounded px-3 py-2 text-sm text-neutral-200"
        >
          <option value="newest">Newest</option>
          <option value="most_novel">Most novel</option>
        </select>
      </div>

      <div className="h-px bg-neutral-800 mb-8" />

      {/* Loading */}
      {UI_STATE === 'loading' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="rounded-xl border border-neutral-800 bg-neutral-900 p-6 animate-pulse"
            >
              <div className="h-6 bg-neutral-700 rounded mb-2" />
              <div className="h-4 bg-neutral-800 rounded w-24 mb-4" />
              <div className="h-1 bg-neutral-700 rounded-full" />
            </div>
          ))}
        </div>
      )}

      {/* Empty */}
      {UI_STATE === 'empty' && (
        <div className="rounded-xl border border-neutral-800 bg-neutral-900 py-20 text-center">
          <h2 className="text-xl font-medium text-neutral-200 mb-2">
            No ideas found
          </h2>
          <p className="text-neutral-400">
            Try adjusting filters or check back later.
          </p>
        </div>
      )}

      {/* Populated */}
      {UI_STATE === 'populated' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredIdeas.map((idea) => (
            <Link
              key={idea.id}
              to={`/idea/${idea.id}`}
              className="group rounded-xl border border-neutral-800 bg-neutral-900 p-6 hover:border-neutral-600 hover:bg-neutral-800/60 transition-colors"
            >
              <h3 className="text-lg font-medium text-neutral-200 group-hover:text-neutral-100">
                {idea.title}
              </h3>

              <div className="mt-2">
                <span className="px-2 py-1 text-xs bg-neutral-800 text-neutral-300 rounded">
                  {idea.domain}
                </span>
              </div>

              <div className="mt-4">
                <div className="text-sm text-neutral-400">Novelty</div>
                <div className="mt-1 w-full bg-neutral-700 rounded-full h-1">
                  <div
                    className="bg-neutral-400 h-1 rounded-full"
                    style={{ width: `${idea.novelty_score}%` }}
                  />
                </div>
              </div>

              <div className="mt-6 text-xs text-neutral-500">
                View details
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};

export default ExplorePage;
