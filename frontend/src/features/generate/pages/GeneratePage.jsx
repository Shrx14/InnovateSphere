import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../../lib/api";

const GeneratePage = () => {
  const navigate = useNavigate();
  const [domains, setDomains] = useState([]);
  const [selectedDomainId, setSelectedDomainId] = useState("");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [generatedIdea, setGeneratedIdea] = useState(null);
  const [error, setError] = useState("");
  const [progress, setProgress] = useState(0);

  // Load available domains on mount
  useEffect(() => {
    const loadDomains = async () => {
      try {
        const res = await api.get("/domains");
        setDomains(res.data.domains || []);
      } catch (err) {
        console.error("Failed to load domains:", err);
        setError("Failed to load available domains");
      }
    };
    loadDomains();
  }, []);

  // Simulate progress bar during generation
  useEffect(() => {
    if (!loading) {
      setProgress(0);
      return;
    }

    setProgress(10);
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) return 90;
        return prev + Math.random() * 20;
      });
    }, 300);

    return () => clearInterval(interval);
  }, [loading]);

  const handleGenerate = async () => {
    if (!query.trim()) {
      setError("Please enter a query or topic");
      return;
    }

    if (!selectedDomainId) {
      setError("Please select a domain");
      return;
    }

    setLoading(true);
    setError("");
    setGeneratedIdea(null);

    try {
      const response = await api.post("/ideas/generate", {
        query: query.trim(),
        domain_id: parseInt(selectedDomainId)
      });

      setProgress(100);
      setTimeout(() => {
        setGeneratedIdea(response.data);
        setLoading(false);
        setProgress(0);
      }, 500);
      setQuery("");
      setSelectedDomainId("");
    } catch (err) {
      const errorMsg = err.response?.data?.error || "Failed to generate idea. Please try again.";
      setError(errorMsg);
      setLoading(false);
      setProgress(0);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-neutral-950 via-neutral-950 to-neutral-900">
      {/* Background decorations */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-0 w-96 h-96 bg-purple-600 rounded-full opacity-10 blur-3xl" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-indigo-600 rounded-full opacity-10 blur-3xl" />
      </div>

      <div className="max-w-4xl mx-auto px-6 py-12 md:py-20 relative z-10">
        {/* Header */}
        <div className="mb-12 md:mb-16">
          <h1 className="text-5xl md:text-6xl font-light text-white mb-4">
            Generate Idea
          </h1>
          <p className="text-xl text-neutral-300">
            Create innovative project ideas evaluated with research evidence and real-time novelty scoring.
          </p>
        </div>

        {!generatedIdea ? (
          <div className="space-y-8">
            {/* Domain Selection Grid */}
            <div>
              <label className="block text-sm font-semibold text-neutral-300 mb-4 uppercase tracking-wide">
                Select Domain
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {domains.map((domain, i) => (
                  <button
                    key={domain.id}
                    onClick={() => setSelectedDomainId(String(domain.id))}
                    className={`glass-card-lg p-4 transition-all duration-300 transform hover:scale-105 text-center group ${
                      selectedDomainId === String(domain.id)
                        ? "bg-gradient-to-br from-indigo-500/40 to-purple-500/40 border-indigo-500/50 text-white"
                        : "hover:bg-white/10 hover:border-indigo-500/30 text-neutral-300"
                    }`}
                    style={{
                      animation: `slideIn 0.5s ease-out ${i * 50}ms backwards`,
                    }}
                  >
                    <div className="text-2xl mb-2 group-hover:scale-125 transition-transform">📚</div>
                    <div className="text-sm font-medium truncate">{domain.name}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Form Card */}
            <div className="glass-card-lg p-8 md:p-12 border border-white/10">
              <div className="space-y-6">
                {/* Topic Input */}
                <div>
                  <label className="block text-sm font-semibold text-neutral-300 mb-3 uppercase tracking-wide">
                    Describe Your Idea
                  </label>
                  <textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value.slice(0, 2000))}
                    placeholder="e.g., 'Build an AI system that detects rare diseases using retinal imaging' or 'Create a blockchain-based supply chain tracking system for pharmaceutical companies'..."
                    rows={5}
                    className="glass-input w-full resize-none"
                  />
                  <div className="flex justify-between items-center mt-2">
                    <p className="text-xs text-neutral-500">
                      Be specific about the problem you're solving
                    </p>
                    <p className={`text-xs font-medium ${query.length > 1800 ? "text-yellow-400" : "text-neutral-500"}`}>
                      {query.length}/2000
                    </p>
                  </div>
                </div>

                {/* Error Display */}
                {error && (
                  <div className="p-4 bg-red-500/20 border border-red-500/50 rounded-lg text-red-200 text-sm animate-shake flex items-start gap-3">
                    <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                    {error}
                  </div>
                )}

                {/* Generate Button */}
                <button
                  onClick={handleGenerate}
                  disabled={loading || !selectedDomainId || !query.trim()}
                  className="btn-primary w-full flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Generating your idea...
                    </>
                  ) : (
                    <>
                      <span>✨ Generate Idea</span>
                      <span>→</span>
                    </>
                  )}
                </button>

                {/* Progress Bar */}
                {loading && (
                  <div className="space-y-2">
                    <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-300"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <p className="text-xs text-neutral-400 text-center">
                      Analyzing research and scoring novelty...
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          /* Generated Idea Display */
          <div
            className="glass-card-lg p-8 md:p-12 border border-indigo-500/50 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 animate-float"
            style={{
              animation: "slideUp 0.6s ease-out",
            }}
          >
            {/* Success Badge */}
            <div className="inline-block mb-6 px-4 py-2 bg-gradient-to-r from-indigo-500/30 to-purple-500/30 rounded-full border border-indigo-500/50">
              <span className="text-sm font-semibold text-indigo-300">✓ Idea Generated</span>
            </div>

            {/* Title */}
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-8 leading-tight">
              {generatedIdea.title}
            </h2>

            {/* Content Grid */}
            <div className="grid md:grid-cols-2 gap-8 mb-8">
              {/* Problem Statement */}
              <div className="space-y-3">
                <p className="text-xs text-indigo-400 uppercase tracking-widest font-semibold">
                  Problem Statement
                </p>
                <p className="text-base text-neutral-300 leading-relaxed">
                  {generatedIdea.problem_statement}
                </p>
              </div>

              {/* Tech Stack */}
              <div className="space-y-3">
                <p className="text-xs text-purple-400 uppercase tracking-widest font-semibold">
                  Suggested Tech Stack
                </p>
                <p className="text-base text-neutral-300 leading-relaxed">
                  {generatedIdea.tech_stack}
                </p>
              </div>
            </div>

            {/* Divider */}
            <div className="h-px bg-gradient-to-r from-white/0 via-white/10 to-white/0 my-8" />

            {/* Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="glass-card p-4 text-center">
                <div className="text-3xl font-bold text-indigo-400 mb-2">
                  {generatedIdea.domain}
                </div>
                <p className="text-xs text-neutral-500">Domain</p>
              </div>
              <div className="glass-card p-4 text-center">
                <div className="text-3xl font-bold text-purple-400 mb-2">
                  {typeof generatedIdea.novelty_score === 'number' ? (generatedIdea.novelty_score / 10).toFixed(1) : 'N/A'}
                </div>
                <p className="text-xs text-neutral-500">Novelty Score</p>
              </div>
              <div className="glass-card p-4 text-center">
                <div className="text-3xl font-bold text-pink-400 mb-2">
                  {typeof generatedIdea.quality_score === 'number' ? (generatedIdea.quality_score / 10).toFixed(1) : 'N/A'}
                </div>
                <p className="text-xs text-neutral-500">Quality Score</p>
              </div>
              <div className="glass-card p-4 text-center">
                <div className="text-3xl font-bold text-blue-400 mb-2">
                  Saved
                </div>
                <p className="text-xs text-neutral-500">Status</p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col md:flex-row gap-4 mt-8">
              <button
                onClick={() => setGeneratedIdea(null)}
                className="flex-1 glass-card px-6 py-3 rounded-lg font-medium text-neutral-300 hover:text-white hover:bg-white/15 transition"
              >
                Generate Another
              </button>
              <button
                onClick={() => {
                  // Navigate to view the idea
                  navigate(`/idea/${generatedIdea.id}`);
                }}
                className="flex-1 btn-primary rounded-lg font-medium"
              >
                View Full Details →
              </button>
            </div>
          </div>
        )}
      </div>

      <style>{`
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes slideUp {
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
    </div>
  );
};

export default GeneratePage;
