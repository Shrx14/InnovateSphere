import React, { useState } from 'react';
import { FiCheck, FiRefreshCw } from 'react-icons/fi';
import NoveltyChecker from './NoveltyChecker';
import axios from 'axios';

const GeneratorTab = ({ user }) => {
  const [query, setQuery] = useState("");
  const [generatedIdea, setGeneratedIdea] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerateIdea = () => {
    if (!query) return; // Don't run if query is empty

    setIsGenerating(true);
    setGeneratedIdea(null);

    axios.post('http://localhost:5000/api/generate-idea', { query })
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
      {isGenerating && <div className="text-center p-4">Loading...</div>}

      {generatedIdea && (
        <div className="bg-green-50 p-6 rounded-lg shadow-lg border border-green-200">
          <h3 className="text-2xl font-bold text-green-800 mb-3">Your Generated Idea!</h3>
          <p className="text-gray-700 text-lg mb-4">{generatedIdea.generated_text}</p>
          <h4 className="text-md font-semibold text-gray-600 mb-2">Inspired by these sources:</h4>
          <ul className="list-disc list-inside space-y-2">
            {generatedIdea.source_documents.map((doc, index) => (
              <li key={index} className="text-gray-600">
                <strong className="text-gray-800">{doc.title}</strong>
                <p className="text-sm italic pl-4">{doc.summary}</p>
              </li>
            ))}
          </ul>
        </div>
      )}
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