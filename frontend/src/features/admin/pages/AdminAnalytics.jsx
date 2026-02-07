import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, BarChart, Bar, ResponsiveContainer } from 'recharts';
import api from '../../../lib/api';

const StatCard = ({ label, value }) => (
  <div className="rounded-xl bg-neutral-900 border border-neutral-800 p-6">
    <p className="text-xs text-neutral-400 uppercase tracking-wide">{label}</p>
    <p className="mt-2 text-2xl font-medium text-white">{value}</p>
  </div>
);

const AdminAnalytics = () => {
  const [data, setData] = useState({
    domains: [],
    trends: [],
    distributions: { novelty: [], quality: [] },
    userDomains: []
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
      { key: 'userDomains', url: '/admin/user-domains' }
    ];

    const results = {};

    for (const { key, url } of endpoints) {
      try {
        const res = await api.get(url);
        results[key] = res.data;
      } catch (error) {
        console.error(`Failed to fetch ${key}:`, error);
        setPartialError(true);
        results[key] = key === 'distributions' ? { novelty: [], quality: [] } : [];
      }
    }

    setData({
      domains: results.domains?.domains || [],
      trends: results.trends?.trends || [],
      distributions: results.distributions || { novelty: [], quality: [] },
      userDomains: results.userDomains?.domains || []
    });

    setLoading(false);
  };

  const createHistogramData = (values, bins = 10) => {
    if (!values || values.length === 0) return [];
    const min = 0;
    const max = 100;
    const range = max - min;
    const binSize = range / bins;

    const histogram = new Array(bins).fill(0);
    values.forEach(value => {
      const clamped = Math.max(min, Math.min(max, value));
      const binIndex = Math.min(Math.floor((clamped - min) / binSize), bins - 1);
      histogram[binIndex]++;
    });

    return histogram.map((count, index) => ({
      bin: `${Math.round(min + index * binSize)}-${Math.round(min + (index + 1) * binSize)}`,
      count
    }));
  };

  const totalDomains = data.domains.length;
  const totalIdeas = data.trends.reduce((sum, t) => sum + (t.count || 0), 0);
  const avgQuality = data.distributions.quality.length > 0
    ? Math.round(data.distributions.quality.reduce((sum, q) => sum + q, 0) / data.distributions.quality.length)
    : 'No data available';
  const topDomain = data.userDomains.length > 0
    ? data.userDomains.reduce((max, d) => (d.requests || 0) > (max.requests || 0) ? d : max).domain
    : 'No data available';

  const noveltyHistogram = createHistogramData(data.distributions.novelty);
  const qualityHistogram = createHistogramData(data.distributions.quality);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="mb-8">
          <h1 className="text-3xl font-light text-white">Admin Analytics</h1>
          <p className="mt-2 text-neutral-400">System-level visibility and oversight</p>
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
        <h1 className="text-3xl font-light text-white">Admin Analytics</h1>
        <p className="mt-2 text-neutral-400">System-level visibility and oversight</p>
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
            <div className="flex items-center justify-center h-full text-neutral-400">
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
              <div className="flex items-center justify-center h-full text-neutral-400">
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
              <div className="flex items-center justify-center h-full text-neutral-400">
                No data available
              </div>
            )}
          </ResponsiveContainer>
        </div>
      </div>

      {partialError && (
        <div className="text-center text-neutral-400 text-sm">
          Some analytics data unavailable
        </div>
      )}
    </div>
  );
};

export default AdminAnalytics;
