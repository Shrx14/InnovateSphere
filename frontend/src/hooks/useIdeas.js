import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';

/**
 * Hook for fetching the current user's ideas with client-side
 * filtering and sorting (mirrors the existing Dashboard + MyIdeas logic).
 *
 * @param {object} options
 * @param {boolean} options.autoLoad - Load on mount (default true)
 */
export function useIdeas({ autoLoad = true } = {}) {
  const [ideas, setIdeas] = useState([]);
  const [loading, setLoading] = useState(autoLoad);
  const [error, setError] = useState(null);

  const fetchIdeas = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/ideas/mine');
      setIdeas(res.data.ideas || []);
    } catch (err) {
      console.error('Failed to load ideas:', err);
      setError('Failed to load your ideas');
      setIdeas([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (autoLoad) {
      fetchIdeas();
    }
  }, [autoLoad, fetchIdeas]);

  // Group ideas by status
  const grouped = {
    all: ideas,
    validated: ideas.filter(i => i.status === 'validated'),
    pending: ideas.filter(i => i.status === 'pending'),
    rejected: ideas.filter(i => i.status === 'rejected' || i.status === 'downgraded'),
  };

  return {
    ideas,
    loading,
    error,
    grouped,
    refetch: fetchIdeas,
  };
}
