import React, { useState } from 'react';
import { FiCheck, FiRefreshCw } from 'react-icons/fi';
import NoveltyChecker from './NoveltyChecker';
import axios from 'axios';
import { AiOutlineLoading3Quarters } from 'react-icons/ai';

const GeneratorTab = ({ user }) => {
  const [query, setQuery] = useState("");
  const [generatedIdea, setGeneratedIdea] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerateIdea = () => {
    if (!query) return; // Don't run if query is empty

    setIsGenerating(true);
    setGeneratedIdea(null);

    const token = localStorage.getItem('access_token');
    axios.post('http://localhost:5000/api/generate-idea', { query }, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    })
      .then(response => {
        setGeneratedIdea(response.data);
      })
      .catch(error => {
        console.error("Error generating idea:", error);
        // You can add a state to show an error message to the user
      })
      .finally(() => {
        setIsGenerating(false);
      });
  };

  const parseGeneratedText = (text) => {
    if (!text) return { overview: '' };

    // Look for labeled sections like "Problem Statement:", "Tech Stack:",
    // "Project Description:", "Modules:" etc. Fallback to full overview.
    const labels = [
      'Problem Statement',
      'Tech Stack',
      'Uniqueness',
      'Project Description',
      'Modules',
      'Methods',
      'Overview'
    ];

    const sections = {};
    // Build regex to find each label and capture text until next label
    const labelRegex = new RegExp('(' + labels.join('|') + ')\s*[:\-–—]?','gi');
    const indices = [];
    let m;
    while ((m = labelRegex.exec(text)) !== null) {
      indices.push({ label: m[1].trim(), index: m.index + m[0].length });
    }

    if (indices.length === 0) {
      return { overview: text.trim() };
    }

    // Prepare a regex to detect any label inside extracted text
    const innerLabelRegex = new RegExp('\\b(' + labels.join('|') + ')\\s*[:\\-–—]?','i');

    for (let i = 0; i < indices.length; i++) {
      const start = indices[i].index;
      const end = i + 1 < indices.length ? indices[i + 1].index : text.length;
      let raw = text.slice(start, end).trim();

      // If the generated model inserted the next label inline (e.g., "... internet. Tech Stack:"),
      // cut the content at that label to avoid repeating headings.
      const innerMatch = innerLabelRegex.exec(raw);
      if (innerMatch && innerMatch.index > 0) {
        raw = raw.slice(0, innerMatch.index).trim();
      }

      const k = indices[i].label.replace(/\s+/g, '_').toLowerCase();
      sections[k] = raw.replace(/^[:\-\s]+/, '').trim();
    }

    // Ensure at least overview exists
    if (!sections.overview && Object.keys(sections).length > 0) {
      sections.overview = sections[Object.keys(sections)[0]];
    }

    return sections;
  };

  return (
    <div className="space-y-8">
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl shadow-lg p-8 text-white">
        <div className="flex flex-col md:flex-row items-center justify-between">
          <div className="mb-6 md:mb-0">
            <h3 className="text-2xl font-bold mb-2">AI-Powered Project Generation</h3>
            <p className="text-blue-100">Generate innovative project ideas tailored to your skills and interests.</p>
          </div>
        </div>
      </div>

      {/* --- NEW: Idea Generator UI --- */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-8">
        <h3 className="text-xl font-bold text-gray-800 mb-2">Idea Generator</h3>
        <p className="text-gray-600 mb-4">
          Type in a topic or domain (e.g., "Beginner web app with AI")
        </p>
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your query..."
            className="flex-grow px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <button
            onClick={handleGenerateIdea}
            disabled={isGenerating}
            className="bg-indigo-600 text-white font-bold py-2 px-6 rounded-md hover:bg-indigo-700 disabled:bg-gray-400"
          >
            {isGenerating ? 'Generating...' : 'Generate'}
          </button>
        </div>
      </div>

      {/* --- NEW: Display for Generated Idea --- */}
      {isGenerating && (
        <div className="p-4">
          <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 flex items-center justify-center bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full">
                <AiOutlineLoading3Quarters className="text-white w-6 h-6 animate-spin" />
              </div>
              <div>
                <div className="h-4 bg-gray-200 rounded w-48 mb-2 animate-pulse"></div>
                <div className="h-3 bg-gray-200 rounded w-32 animate-pulse"></div>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="h-24 bg-gray-100 rounded animate-pulse"></div>
              <div className="h-24 bg-gray-100 rounded animate-pulse"></div>
              <div className="h-24 bg-gray-100 rounded animate-pulse col-span-1 sm:col-span-2"></div>
            </div>
          </div>
        </div>
      )}

      {generatedIdea && (() => {
        const sections = parseGeneratedText(generatedIdea.generated_text);
        return (
          <div className="bg-white p-6 rounded-lg shadow-lg border border-gray-100 max-w-4xl mx-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-2xl font-bold text-gray-800">Your Generated Idea</h3>
              <span className="text-sm text-gray-500">Tailored to: <strong className="text-gray-700">{query}</strong></span>
            </div>

            {sections.problem_statement && (
              <section className="mb-4">
                <h4 className="text-lg font-semibold text-indigo-600">Problem Statement</h4>
                <p className="text-gray-700 mt-2">{sections.problem_statement}</p>
              </section>
            )}

            {sections.tech_stack && (
              <section className="mb-4">
                <h4 className="text-lg font-semibold text-indigo-600">Tech Stack</h4>
                <div className="flex flex-wrap gap-2 mt-2">
                  {sections.tech_stack.split(/[,;|•\n]/).map((s, i) => s.trim()).filter(Boolean).map((tech, i) => (
                    <span key={i} className="bg-indigo-50 text-indigo-700 text-sm px-3 py-1 rounded-full border border-indigo-100">{tech}</span>
                  ))}
                </div>
              </section>
            )}

            {sections.uniqueness && (
              <section className="mb-4">
                <h4 className="text-lg font-semibold text-indigo-600">Uniqueness</h4>
                <p className="text-gray-700 mt-2">{sections.uniqueness}</p>
              </section>
            )}

            {sections.project_description && (
              <section className="mb-4">
                <h4 className="text-lg font-semibold text-indigo-600">Project Description</h4>
                <p className="text-gray-700 mt-2">{sections.project_description}</p>
              </section>
            )}

            {sections.modules && (
              <section className="mb-4">
                <h4 className="text-lg font-semibold text-indigo-600">Modules / Methods</h4>
                <ul className="list-disc list-inside mt-2 text-gray-700">
                  {sections.modules.split(/\n|\.|;|,/).map((m, i) => m.trim()).filter(Boolean).map((m, i) => (
                    <li key={i}>{m}</li>
                  ))}
                </ul>
              </section>
            )}

            {!sections.problem_statement && !sections.tech_stack && !sections.project_description && (
              <section className="mb-4">
                <h4 className="text-lg font-semibold text-indigo-600">Overview</h4>
                <p className="text-gray-700 mt-2">{sections.overview}</p>
              </section>
            )}

            <div className="mt-6">
              <h4 className="text-md font-semibold text-gray-600 mb-2">Inspired by these sources:</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {generatedIdea.source_documents.map((doc, index) => (
                  <div key={index} className="border border-gray-100 rounded p-3 bg-gray-50">
                    {doc.url ? (
                      <a href={doc.url} target="_blank" rel="noreferrer" className="text-blue-600 font-semibold">
                        {doc.title || 'Source'}
                      </a>
                    ) : (
                      <div className="font-semibold text-gray-800">{doc.title || 'Source'}</div>
                    )}
                    {doc.summary && <div className="text-sm text-gray-600 mt-1">{doc.summary}</div>}
                  </div>
                ))}
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
};

const ProjectIdeas = ({ user }) => {
  const [activeTab, setActiveTab] = useState("generator");

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          Project Ideas
        </h2>
        <div className="flex bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setActiveTab("generator")}
            className={`px-4 py-2 rounded-md transition-colors duration-200 ${
              activeTab === "generator" ? "bg-white shadow-sm text-blue-600" : "text-gray-600 hover:text-gray-900"
            }`}
          >
            <div className="flex items-center space-x-2">
              <FiRefreshCw className="w-4 h-4" />
              <span>Generator</span>
            </div>
          </button>
          <button
            onClick={() => setActiveTab("checker")}
            className={`px-4 py-2 rounded-md transition-colors duration-200 ${
              activeTab === "checker" ? "bg-white shadow-sm text-blue-600" : "text-gray-600 hover:text-gray-900"
            }`}
          >
            <div className="flex items-center space-x-2">
              <FiCheck className="w-4 h-4" />
              <span>Novelty Checker</span>
            </div>
          </button>
        </div>
      </div>

      {activeTab === "generator" ? <GeneratorTab user={user} /> : <NoveltyChecker />}
    </div>
  );
};

export default ProjectIdeas;