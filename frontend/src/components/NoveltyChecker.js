import React, { useState } from 'react';
import axios from 'axios';

const ProgressBar = ({ score }) => {
  const getColor = (s) => {
    if (s < 30) return 'bg-red-500';
    if (s < 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };
  const colorClass = getColor(score);
  return (
    <div className="w-full bg-gray-200 rounded-full h-8 my-4">
      <div
        className={`${colorClass} h-8 rounded-full flex items-center justify-center text-white font-bold text-sm`}
        style={{ width: `${score}%` }}
      >
        {score.toFixed(2)}% Novelty
      </div>
    </div>
  );
};

const NoveltyChecker = () => {
  const [ideaText, setIdeaText] = useState('');
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCheckNovelty = async () => {
    if (!ideaText.trim()) {
      setError('Please enter a project idea to check.');
      return;
    }
    setIsLoading(true);
    setError('');
    setResults(null);
    try {
      // Use env var for API base so production can point to real backend.
      const base = process.env.REACT_APP_API_BASE_URL || '';
      // First attempt: relative / proxy or explicit base
      let resp;
      try {
        const token = localStorage.getItem('access_token');
        resp = await axios.post(`${base}/api/check_novelty`, { description: ideaText }, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        setResults(resp.data);
        return;
      } catch (firstErr) {
        console.warn('First novelty POST failed:', firstErr?.message || firstErr);
        // If first attempt failed and we didn't already target localhost:5000, retry explicit local backend
        const local = 'http://localhost:5000';
        if ((base || '').includes('localhost') || base === local) {
          // already targeting localhost, rethrow
          throw firstErr;
        }
        try {
          const token = localStorage.getItem('access_token');
          resp = await axios.post(`${local}/api/check_novelty`, { description: ideaText }, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          });
          setResults(resp.data);
          return;
        } catch (secondErr) {
          // Both attempts failed — surface detailed info
          const status = secondErr?.response?.status || firstErr?.response?.status;
          const serverMsg = secondErr?.response?.data?.error || firstErr?.response?.data?.error || secondErr?.message || firstErr?.message;
          console.error('Novelty check failed (both attempts):', { status, serverMsg, firstErr, secondErr });
          setError(serverMsg ? `Failed to check novelty (status ${status}): ${serverMsg}` : `Failed to check novelty: ${secondErr?.message || firstErr?.message}`);
          return;
        }
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white shadow-lg rounded-lg mt-10">
      <h2 className="text-2xl font-bold mb-4 text-gray-800">Check Your Project's Novelty</h2>
      <p className="mb-4 text-gray-600">Paste your project idea or abstract below.</p>
      <textarea
        className="w-full h-40 p-3 border border-gray-300 rounded-md focus:outline-none"
        value={ideaText}
        onChange={(e) => setIdeaText(e.target.value)}
      />
      <button
        onClick={handleCheckNovelty}
        disabled={isLoading}
        className="w-full mt-4 bg-blue-600 text-white py-3 px-4 rounded-md font-semibold hover:bg-blue-700 disabled:bg-gray-400"
      >
        {isLoading ? 'Analyzing...' : 'Check Novelty'}
      </button>

      {error && <p className="text-red-500 mt-4">{error}</p>}

      {results && (
        <div className="mt-8">
          <h3 className="text-xl font-semibold mb-2">Analysis Results</h3>
          <ProgressBar score={results.novelty_score} />
          <h4 className="text-lg font-semibold mt-6 mb-3">Most Similar Existing Projects:</h4>
          {results.similar_projects.length > 0 ? (
            <ul className="space-y-4">
              {results.similar_projects.map((p) => (
                <li key={p.id} className="p-4 border border-gray-200 rounded-md">
                  <a href={p.url} target="_blank" rel="noreferrer" className="text-blue-600 font-bold">
                    {p.title}
                  </a>
                  <p className="text-sm text-gray-700 mt-1">{p.description}</p>
                  <span className="text-sm font-medium text-gray-600">Similarity: {p.similarity_percent}%</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-600">No similar projects found.</p>
          )}
        </div>
      )}
    </div>
  );
};

export default NoveltyChecker;
