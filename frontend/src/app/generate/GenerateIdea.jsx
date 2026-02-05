import React, { useState, useEffect } from "react";
import api from "../../shared/api";

const GenerateIdea = ({ onSubmit, loading }) => {
  const [domains, setDomains] = useState([]);
  const [domainId, setDomainId] = useState("");
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchDomains = async () => {
      try {
        const response = await api.get("/domains");
        setDomains(response.data.domains);
      } catch (err) {
        setError("Failed to load domains");
      }
    };
    fetchDomains();
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!domainId || !query.trim()) {
      setError("Domain and problem intent are required");
      return;
    }
    setError("");
    onSubmit({ domain_id: domainId, query });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl">
      <div>
        <label className="block text-sm text-gray-400 mb-2">
          Domain
        </label>
        <select
          value={domainId}
          onChange={(e) => setDomainId(e.target.value)}
          className="w-full bg-gray-900 border border-gray-700 p-3 rounded-md"
          required
        >
          <option value="">Select domain</option>
          {domains.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm text-gray-400 mb-2">
          Problem intent
        </label>
        <textarea
          rows={4}
          maxLength={300}
          placeholder="Describe the problem space, not the solution"
          className="w-full bg-gray-900 border border-gray-700 p-3 rounded-md"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          required
        />
        <div className="text-xs text-gray-500 mt-1">
          {query.length}/300
        </div>
      </div>

      {error && (
        <div className="border border-red-700 bg-red-950/20 p-4 rounded-md">
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      <button
        type="submit"
        className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md disabled:opacity-50"
        disabled={loading}
      >
        {loading ? "Analyzing evidence…" : "Generate idea"}
      </button>
    </form>
  );
};

export default GenerateIdea;
