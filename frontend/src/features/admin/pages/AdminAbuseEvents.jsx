import React, { useEffect, useState, useCallback } from 'react';
import api from '../../../lib/api';

const AdminAbuseEvents = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const perPage = 25;

  const fetchEvents = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get(`/admin/abuse-events?page=${page}&per_page=${perPage}`);
      setEvents(res.data.events || res.data || []);
    } catch (err) {
      console.error('Failed to fetch abuse events:', err);
    } finally {
      setLoading(false);
    }
  }, [page, perPage]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-light dark:text-white text-neutral-900">Abuse Events</h1>
        <p className="mt-2 dark:text-neutral-400 text-neutral-500">Monitor rate-limit violations and suspicious activity</p>
      </div>

      {loading ? (
        <div className="text-center dark:text-neutral-400 text-neutral-500 py-12">Loading abuse events...</div>
      ) : events.length === 0 ? (
        <div className="text-center dark:text-neutral-400 text-neutral-500 py-12">
          <p className="text-lg">No abuse events recorded.</p>
          <p className="text-sm mt-2">This is good — no suspicious activity detected.</p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-neutral-800 dark:text-neutral-400 text-neutral-500 text-xs uppercase tracking-wide">
                  <th className="py-3 px-4">ID</th>
                  <th className="py-3 px-4">User ID</th>
                  <th className="py-3 px-4">Event Type</th>
                  <th className="py-3 px-4">Details</th>
                  <th className="py-3 px-4">Created At</th>
                </tr>
              </thead>
              <tbody>
                {events.map((event) => (
                  <tr key={event.id} className="border-b dark:border-neutral-800/50 border-neutral-200 hover:bg-neutral-900/50">
                    <td className="py-3 px-4 dark:text-neutral-300 text-neutral-600 text-sm">{event.id}</td>
                    <td className="py-3 px-4 dark:text-neutral-300 text-neutral-600 text-sm">{event.user_id || 'Anonymous'}</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-1 text-xs rounded bg-red-500/10 text-red-400 border border-red-500/20">
                        {event.event_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 dark:text-neutral-400 text-neutral-500 text-sm max-w-xs truncate">
                      {event.details ? JSON.stringify(event.details) : '—'}
                    </td>
                    <td className="py-3 px-4 dark:text-neutral-400 text-neutral-500 text-sm">
                      {event.created_at ? new Date(event.created_at).toLocaleString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-center gap-4 mt-6">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-4 py-2 text-sm rounded border border-neutral-700 dark:text-neutral-300 text-neutral-600 hover:border-white dark:hover:text-white text-neutral-900 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              ← Previous
            </button>
            <span className="dark:text-neutral-400 text-neutral-500 text-sm">Page {page}</span>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={events.length < perPage}
              className="px-4 py-2 text-sm rounded border border-neutral-700 dark:text-neutral-300 text-neutral-600 hover:border-white dark:hover:text-white text-neutral-900 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              Next →
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default AdminAbuseEvents;
