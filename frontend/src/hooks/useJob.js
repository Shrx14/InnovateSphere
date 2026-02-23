import { useState, useEffect, useRef, useCallback } from 'react';
import api from '@/lib/api';
import { getPhaseLabel } from '@/lib/phaseLabels';
import { API_BASE_URL } from '@/config/config';

/**
 * Low-level hook: subscribe to a generation job's progress via SSE,
 * with automatic fallback to 2s polling if SSE fails.
 *
 * @param {string|null} jobId - The job ID to track (null = idle)
 * @returns {{ status, phase, phaseName, progress, sourcesCount, noveltyScore, result, error }}
 */
export function useJob(jobId) {
  const [state, setState] = useState({
    status: null,     // 'queued' | 'running' | 'completed' | 'failed'
    phase: null,
    phaseName: '',
    progress: 0,
    sourcesCount: 0,
    noveltyScore: null,
    result: null,
    error: null,
  });

  const eventSourceRef = useRef(null);
  const pollRef = useRef(null);
  const fallbackActivated = useRef(false);

  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  // Apply a status update from either SSE or poll
  const applyUpdate = useCallback((data) => {
    const phaseName = getPhaseLabel(data.phase, data.phase_name);

    setState(prev => ({
      ...prev,
      status: data.status || prev.status,
      phase: data.phase ?? prev.phase,
      phaseName,
      progress: data.progress ?? prev.progress,
      sourcesCount: data.sources_count ?? prev.sourcesCount,
      noveltyScore: data.novelty_score ?? prev.noveltyScore,
    }));

    // Terminal states
    if (data.status === 'completed' && data.result) {
      setState(prev => ({
        ...prev,
        status: 'completed',
        progress: 100,
        phaseName: 'Complete',
        result: data.result,
      }));
      return true; // signal done
    }
    if (data.status === 'failed') {
      setState(prev => ({
        ...prev,
        status: 'failed',
        error: data.error || 'Generation failed',
      }));
      return true;
    }
    return false;
  }, []);

  // Fallback polling
  const startPolling = useCallback(() => {
    if (!jobId || pollRef.current) return;

    pollRef.current = setInterval(async () => {
      try {
        const res = await api.get(`/ideas/generate/${jobId}`);
        const done = applyUpdate(res.data);
        if (done) cleanup();
      } catch (err) {
        const status = err.response?.status;
        if (status === 400 || status === 404) {
          setState(prev => ({
            ...prev,
            status: 'failed',
            error: err.response?.data?.error || 'Generation failed',
          }));
          cleanup();
        }
        // On 5xx / network errors, keep polling
      }
    }, 2000);
  }, [jobId, applyUpdate, cleanup]);

  useEffect(() => {
    if (!jobId) {
      cleanup();
      return;
    }

    // Reset state for new job
    setState({
      status: 'queued',
      phase: null,
      phaseName: 'Starting generation…',
      progress: 5,
      sourcesCount: 0,
      noveltyScore: null,
      result: null,
      error: null,
    });
    fallbackActivated.current = false;

    // Try SSE first
    // NOTE: EventSource API does not support custom headers, so JWT is passed
    // via query param. The backend validates it with decode_token(). This is the
    // standard workaround — the token is short-lived (JWT_EXP_SECONDS) and the
    // connection is over HTTPS in production, mitigating URL-logging risk.
    const token = localStorage.getItem('access_token');
    const sseUrl = `${API_BASE_URL}/ideas/generate/${jobId}/stream${token ? `?token=${token}` : ''}`;

    try {
      const es = new EventSource(sseUrl);
      eventSourceRef.current = es;

      es.addEventListener('progress', (e) => {
        try {
          const data = JSON.parse(e.data);
          applyUpdate(data);
        } catch { /* ignore parse errors */ }
      });

      es.addEventListener('complete', (e) => {
        try {
          const data = JSON.parse(e.data);
          applyUpdate({ ...data, status: 'completed' });
        } catch { /* ignore */ }
        cleanup();
      });

      es.addEventListener('error_event', (e) => {
        try {
          const data = JSON.parse(e.data);
          setState(prev => ({
            ...prev,
            status: 'failed',
            error: data.error || 'Generation failed',
          }));
        } catch { /* ignore */ }
        cleanup();
      });

      es.onerror = () => {
        // SSE connection failed — fall back to polling
        if (!fallbackActivated.current) {
          fallbackActivated.current = true;
          es.close();
          eventSourceRef.current = null;
          startPolling();
        }
      };
    } catch {
      // EventSource constructor failed — fall back to polling
      startPolling();
    }

    return cleanup;
  }, [jobId, applyUpdate, cleanup, startPolling]);

  return state;
}
