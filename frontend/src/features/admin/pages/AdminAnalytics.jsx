import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, BarChart, Bar, PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import api from '../../../lib/api';
import { formatScore } from '../../../lib/formatScore';

const StatCard = ({ label, value }) => (
  <div className="rounded-xl bg-neutral-900 border border-neutral-800 p-6">
    <p className="text-xs text-neutral-400 uppercase tracking-wide">{label}</p>
    <p className="mt-2 text-2xl font-medium text-white
  </div>
);

const AdminAnalytics = () => {
  const [data, setData] = useState({
    domains: [],
    trends: [],
    distributions: { novelty: [], quality: [] },
    userDomains: [],
    bias: null,
    kpis: null
  });
  const [loading, setLoading] = useState(true);
  const [partialError, setPartialError] = useState(false);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    setLoading(true);
    setPartialError(false);

    const endpoints = [
      { key: 'domains', url: '/admin/domains' },
      { key: 'trends', url: '/admin/trends' },
      { key: 'distributions', url: '/admin/distributions' },
      { key: 'userDomains', url: '/admin/user-domains' },
      { key: 'bias', url: '/analytics/admin/bias-transparency' },
      { key: 'kpis', url: '/analytics/admin/kpis' }
    ];

    const results = {};

    // Fetch all endpoints in parallel instead of sequentially
    const settled = await Promise.allSettled(
      endpoints.map(({ key, url }) => api.get(url).then(res => ({ key, data: res.data })))
    );

    for (const result of settled) {
      if (result.status === 'fulfilled') {
        results[result.value.key] = result.value.data;
      } else {
        setPartialError(true);
      }
    }

    setData({
      domains: results.domains?.domains || [],
      trends: results.trends?.trends || [],
      distributions: results.distributions || { novelty: [], quality: [] },
      userDomains: results.userDomains?.user_domains || [],
      bias: results.bias || null,
      kpis: results.kpis || null
    });

    setLoading(false);
  };

  const totalDomains = data.domains.length;
  const totalIdeas = data.kpis?.total_ideas ?? data.trends.reduce((sum, t) => sum + (t.count || 0), 0);
  const avgQuality = data.kpis
    ? formatScore(Math.round(data.kpis.avg_quality))
    : data.distributions.quality.length > 0
    ? (() => {
        const totalCount = data.distributions.quality.reduce((sum, b) => sum + (b.count || 0), 0);
        if (totalCount === 0) return 'No data available';
        const weightedSum = data.distributions.quality.reduce((sum, b) => {
          const midpoint = parseInt(b.range) + 5;
          return sum + midpoint * (b.count || 0);
        }, 0);
        return formatScore(Math.round(weightedSum / totalCount));
      })()
    : 'No data available';
  const topDomain = data.userDomains.length > 0
    ? data.userDomains.reduce((max, d) => (d.user_count || 0) > (max.user_count || 0) ? d : max).name
    : 'No data available';

  // Backend returns pre-bucketed {range, count} objects — use directly as chart data
  const noveltyHistogram = data.distributions.novelty.map(b => ({ bin: b.range, count: b.count }));
  const qualityHistogram = data.distributions.quality.map(b => ({ bin: b.range, count: b.count }));

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="mb-8">
          <h1 className="text-3xl font-light text-white Analytics</h1>
          <p className="mt-2 text-neutral-400 visibility and oversight</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-neutral-800 rounded-lg p-6 animate-pulse">
              <div className="h-4 bg-neutral-700 rounded mb-4"></div>
              <div className="h-6 bg-neutral-700 rounded"></div>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="bg-neutral-800 rounded-lg p-6 animate-pulse">
            <div className="h-4 bg-neutral-700 rounded mb-4"></div>
            <div className="h-32 bg-neutral-700 rounded"></div>
          </div>
          <div className="bg-neutral-800 rounded-lg p-6 animate-pulse">
            <div className="h-4 bg-neutral-700 rounded mb-4"></div>
            <div className="h-32 bg-neutral-700 rounded"></div>
          </div>
          <div className="bg-neutral-800 rounded-lg p-6 animate-pulse">
            <div className="h-4 bg-neutral-700 rounded mb-4"></div>
            <div className="h-32 bg-neutral-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-light text-white Analytics</h1>
        <p className="mt-2 text-neutral-400 visibility and oversight</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <StatCard label="Active domains" value={totalDomains || 'No data available'} />
        <StatCard label="Ideas generated" value={totalIdeas || 'No data available'} />
        <StatCard label="Avg quality" value={avgQuality} />
        <StatCard label="Top domain" value={topDomain} />
      </div>

      {/* Trend Chart */}
      <div className="bg-neutral-900 rounded-xl border border-neutral-800 p-6 mb-6">
        <ResponsiveContainer width="100%" height={300}>
          {data.trends.length > 0 ? (
            <LineChart data={data.trends}>
              <CartesianGrid stroke="#374151" />
              <XAxis dataKey="date" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Line type="monotone" dataKey="count" stroke="#9CA3AF" strokeWidth={2} dot={false} />
            </LineChart>
          ) : (
            <div className="flex items-center justify-center h-full text-neutral-400
              No data available
            </div>
          )}
        </ResponsiveContainer>
      </div>

      {/* Distribution Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-neutral-900 rounded-xl border border-neutral-800 p-6">
          <h3 className="text-lg font-medium text-white mb-4">Novelty Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            {noveltyHistogram.length > 0 ? (
              <BarChart data={noveltyHistogram}>
                <CartesianGrid stroke="#374151" />
                <XAxis dataKey="bin" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Bar dataKey="count" fill="#9CA3AF" />
              </BarChart>
            ) : (
              <div className="flex items-center justify-center h-full text-neutral-400
                No data available
              </div>
            )}
          </ResponsiveContainer>
        </div>
        <div className="bg-neutral-900 rounded-xl border border-neutral-800 p-6">
          <h3 className="text-lg font-medium text-white mb-4">Quality Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            {qualityHistogram.length > 0 ? (
              <BarChart data={qualityHistogram}>
                <CartesianGrid stroke="#374151" />
                <XAxis dataKey="bin" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Bar dataKey="count" fill="#9CA3AF" />
              </BarChart>
            ) : (
              <div className="flex items-center justify-center h-full text-neutral-400
                No data available
              </div>
            )}
          </ResponsiveContainer>
        </div>
      </div>

      {/* Extra KPI Row (from server KPIs) */}
      {data.kpis && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <StatCard label="Avg novelty" value={formatScore(Math.round(data.kpis.avg_novelty))} />
          <StatCard label="Rejection rate" value={`${(data.kpis.rejection_rate * 100).toFixed(1)}%`} />
          <StatCard label="Avg rating" value={`${data.kpis.avg_rating?.toFixed(1) ?? 'N/A'} / 5`} />
          <StatCard label="Total reviews" value={data.kpis.total_reviews} />
        </div>
      )}

      {/* Bias Transparency Section */}
      {data.bias && (
        <>
          <div className="mb-4 mt-8">
            <h2 className="text-2xl font-light text-white Transparency</h2>
            <p className="mt-1 text-neutral-400 text-sm">How HITL verdicts affect scores and generation patterns</p>
          </div>

          {/* Verdict Breakdown + Penalty Stats */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div className="bg-neutral-900 rounded-xl border border-neutral-800 p-6">
              <h3 className="text-lg font-medium text-white mb-4">Admin Verdicts</h3>
              {data.bias.admin_verdicts?.total > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Validated', value: data.bias.admin_verdicts.validated },
                        { name: 'Downgraded', value: data.bias.admin_verdicts.downgraded },
                        { name: 'Rejected', value: data.bias.admin_verdicts.rejected }
                      ].filter(d => d.value > 0)}
                      cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, value }) => `${name}: ${value}`}
                    >
                      <Cell fill="#6B7280" />
                      <Cell fill="#D97706" />
                      <Cell fill="#EF4444" />
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-neutral-500 text-sm">No verdicts recorded yet</p>
              )}
            </div>

            <div className="bg-neutral-900 rounded-xl border border-neutral-800 p-6">
              <h3 className="text-lg font-medium text-white mb-4">Penalty Impact</h3>
              <div className="space-y-4">
                <div className="flex justify-between text-sm">
                  <span className="text-neutral-400">Ideas with active penalties</span>
                  <span className="text-white font-mono">{data.bias.penalty_impact_stats?.total_ideas_with_penalties ?? 0}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-neutral-400">Avg penalty impact</span>
                  <span className="text-white font-mono">{data.bias.penalty_impact_stats?.average_penalty_impact ?? 0}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-neutral-400">Source domains affected</span>
                  <span className="text-white font-mono">{data.bias.penalty_impact_stats?.sources_affected ?? 0}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-neutral-400">Total generation traces</span>
                  <span className="text-white font-mono">{data.bias.bias_transparency_summary?.total_generation_traces ?? 0}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-neutral-400">Traces with constraints</span>
                  <span className="text-white font-mono">{data.bias.bias_transparency_summary?.traces_with_active_constraints ?? 0}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-neutral-400">Avg constraint complexity</span>
                  <span className="text-white font-mono">{data.bias.bias_transparency_summary?.average_constraint_complexity ?? 0}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Domain Strictness Distribution */}
          {data.bias.domain_strictness_distribution && Object.keys(data.bias.domain_strictness_distribution).length > 0 && (
            <div className="bg-neutral-900 rounded-xl border border-neutral-800 p-6 mb-6">
              <h3 className="text-lg font-medium text-white mb-4">Domain Strictness</h3>
              <div className="flex gap-6">
                {Object.entries(data.bias.domain_strictness_distribution).map(([level, count]) => (
                  <div key={level} className="flex-1 text-center">
                    <p className="text-2xl font-mono text-white
                    <p className="text-xs text-neutral-400 uppercase tracking-wide mt-1">{level}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Penalized Source Domains */}
          {data.bias.bias_impact_by_source && Object.keys(data.bias.bias_impact_by_source).length > 0 && (
            <div className="bg-neutral-900 rounded-xl border border-neutral-800 p-6 mb-6">
              <h3 className="text-lg font-medium text-white mb-4">Penalized Source Domains</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-neutral-400 text-left border-b border-neutral-800">
                      <th className="pb-2">Domain</th>
                      <th className="pb-2">Occurrences</th>
                      <th className="pb-2">Avg Penalty</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(data.bias.bias_impact_by_source)
                      .sort(([, a], [, b]) => b.count - a.count)
                      .map(([domain, stats]) => (
                        <tr key={domain} className="border-b border-neutral-800/50">
                          <td className="py-2 font-mono text-neutral-300">{domain}</td>
                          <td className="py-2 text-neutral-400">{stats.count}</td>
                          <td className="py-2 text-neutral-400">{stats.average_penalty_percent}%</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {partialError && (
        <div className="text-center text-neutral-400 text-sm">
          Some analytics data unavailable
        </div>
      )}
    </div>
  );
};

export default AdminAnalytics;
