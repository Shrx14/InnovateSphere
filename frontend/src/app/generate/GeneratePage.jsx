import React, { useState } from "react";
import api from "../../shared/api";

const GeneratePage = () => {
  const [domain, setDomain] = useState("");
  const [loading, setLoading] = useState(false);
  const [generatedIdea, setGeneratedIdea] = useState(null);
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    if (!domain.trim()) {
      setError("Please enter a domain");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const response = await api.post("/ideas/generate", { domain });
      setGeneratedIdea(response.data);
    } catch (err) {
      setError("Failed to generate idea. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      <h1 className="text-5xl font-light tracking-tight text-white mb-8">Generate Idea</h1>

      <div className="mb-20">
        <p className="text-base text-neutral-300 leading-relaxed mb-8">
          Enter a domain to generate a new project idea based on current research and novelty analysis.
        </p>

        <div className="space-y-6">
          <div>
            <label className="block text-sm text-neutral-400 mb-2">Domain</label>
            <input
              type="text"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              placeholder="e.g., Healthcare, AI, Finance"
              className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-3 text-white placeholder-neutral-500 focus:border-indigo-500 focus:outline-none"
            />
          </div>

          {error && <p className="text-red-400 text-sm">{error}</p>}

          <button
            onClick={handleGenerate}
            disabled={loading}
            className="bg-indigo-600/90 hover:bg-indigo-600 text-white rounded-lg px-6 py-3 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Generating..." : "Generate Idea"}
          </button>
        </div>
      </div>

      {generatedIdea && (
        <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-8">
          <h2 className="text-xl font-medium text-white mb-4">{generatedIdea.title}</h2>
          <p className="text-base text-neutral-300 leading-relaxed mb-6">{generatedIdea.description}</p>
          <div className="text-sm text-neutral-400">
            Domain: {generatedIdea.domain} | Novelty: {generatedIdea.novelty_score}/100 | Quality: {generatedIdea.quality_score}/100
          </div>
        </div>
      )}
    </div>
  );
};

export default GeneratePage;
