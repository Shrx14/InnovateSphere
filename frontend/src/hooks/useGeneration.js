import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import { useJob } from './useJob';

/**
 * High-level hook for the idea generation workflow.
 * Manages form state, domain loading, job submission, and tracks progress.
 */
export function useGeneration() {
  const [domains, setDomains] = useState([]);
  const [domainsLoading, setDomainsLoading] = useState(true);
  const [selectedDomainId, setSelectedDomainId] = useState('');
  const [query, setQuery] = useState('');
  const [jobId, setJobId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');

  // SSE/poll job tracking
  const job = useJob(jobId);

  // Load domains on mount
  useEffect(() => {
    api.get('/domains')
      .then(res => setDomains(res.data.domains || []))
      .catch(err => {
        console.error('Failed to load domains:', err);
        setSubmitError('Failed to load available domains');
      })
      .finally(() => setDomainsLoading(false));
  }, []);

  // Submit a generation request
  const submit = useCallback(async () => {
    if (!query.trim()) {
      setSubmitError('Please enter a query or topic');
      return;
    }
    if (!selectedDomainId) {
      setSubmitError('Please select a domain');
      return;
    }

    setSubmitting(true);
    setSubmitError('');
    setJobId(null);

    try {
      const res = await api.post('/ideas/generate', {
        query: query.trim(),
        domain_id: parseInt(selectedDomainId),
      });

      const newJobId = res.data?.job_id;
      if (!newJobId) {
        // Backend returned result directly (shouldn't happen in normal flow)
        setSubmitting(false);
        return res.data;
      }

      setJobId(newJobId);
      setSubmitting(false);
      return { jobId: newJobId };
    } catch (err) {
      const errorMsg =
        err.response?.data?.error ||
        err.response?.data?.msg ||
        'Failed to start generation. Please try again.';
      setSubmitError(errorMsg);
      setSubmitting(false);
      return null;
    }
  }, [query, selectedDomainId]);

  // Reset form for a new generation
  const reset = useCallback(() => {
    setJobId(null);
    setQuery('');
    setSelectedDomainId('');
    setSubmitError('');
  }, []);

  // Cancel the current job (reset tracking)
  const cancel = useCallback(() => {
    setJobId(null);
    setSubmitError('');
  }, []);

  // Derived state
  const isGenerating = !!jobId && job.status !== 'completed' && job.status !== 'failed';
  const isComplete = job.status === 'completed';
  const isFailed = job.status === 'failed';

  return {
    // Form state
    domains,
    domainsLoading,
    selectedDomainId,
    setSelectedDomainId,
    query,
    setQuery,

    // Submission
    submit,
    submitting,
    submitError,
    setSubmitError,

    // Job tracking
    jobId,
    isGenerating,
    isComplete,
    isFailed,
    phase: job.phase,
    phaseName: job.phaseName,
    progress: job.progress,
    sourcesCount: job.sourcesCount,
    noveltyScore: job.noveltyScore,
    result: job.result,
    jobError: job.error,

    // Actions
    reset,
    cancel,
  };
}
