import React, { useState } from 'react';
import { API_BASE_URL } from '../config';

const AdminDashboard = ({ user }) => {
  const [ingestionMode, setIngestionMode] = useState('single'); // 'single' or 'bulk'
  const [singleProject, setSingleProject] = useState({
    title: '',
    description: '',
    source_url: ''
  });
  const [bulkProjects, setBulkProjects] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [results, setResults] = useState(null);

  const handleSingleInputChange = (e) => {
    const { name, value } = e.target;
    setSingleProject(prev => ({ ...prev, [name]: value }));
  };

  const validateSingleProject = () => {
    if (!singleProject.title.trim()) return 'Title is required';
    if (!singleProject.description.trim()) return 'Description is required';
    return null;
  };

  const validateBulkProjects = () => {
    if (!bulkProjects.trim()) return 'Bulk projects data is required';
    try {
      const projects = JSON.parse(bulkProjects);
      if (!Array.isArray(projects)) return 'Must be an array of projects';
      if (projects.length > 50) return 'Maximum 50 projects allowed';
      if (projects.length === 0) return 'At least one project required';

      for (let i = 0; i < projects.length; i++) {
        const project = projects[i];
        if (!project.title || !project.description) {
          return `Project ${i + 1}: title and description are required`;
        }
      }
      return null;
    } catch (e) {
      return 'Invalid JSON format';
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage({ type: '', text: '' });
    setResults(null);

    let validationError = null;
    let payload = null;

    if (ingestionMode === 'single') {
      validationError = validateSingleProject();
      if (!validationError) {
        payload = [singleProject];
      }
    } else {
      validationError = validateBulkProjects();
      if (!validationError) {
        payload = JSON.parse(bulkProjects);
      }
    }

    if (validationError) {
      setMessage({ type: 'error', text: validationError });
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/admin/ingest`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ projects: payload })
      });

      const data = await response.json();

      if (response.ok) {
        setResults(data);
        setMessage({ type: 'success', text: 'Projects ingested successfully!' });
        // Reset forms
        setSingleProject({ title: '', description: '', source_url: '' });
        setBulkProjects('');
      } else if (response.status === 401 || response.status === 403) {
        setMessage({ type: 'error', text: 'Unauthorized access. Please login again.' });
        // Optionally force logout
        localStorage.removeItem('access_token');
        window.location.reload();
      } else {
        setMessage({ type: 'error', text: data.error || 'Ingestion failed' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Network error. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-3xl font-bold mb-8 bg-gradient-to-r from-red-600 to-orange-600 bg-clip-text text-transparent">
        Admin Dashboard
      </h2>

      {/* Message Display */}
      {message.text && (
        <div className={`mb-6 p-4 rounded-lg ${
          message.type === 'error'
            ? 'bg-red-100 text-red-700 border border-red-200'
            : 'bg-green-100 text-green-700 border border-green-200'
        }`}>
          {message.text}
        </div>
      )}

      {/* Ingestion Form */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-6 mb-8">
        <h3 className="text-xl font-semibold mb-4">Project Ingestion</h3>

        {/* Mode Toggle */}
        <div className="mb-6">
          <div className="flex space-x-4">
            <button
              onClick={() => setIngestionMode('single')}
              className={`px-4 py-2 rounded-lg font-medium ${
                ingestionMode === 'single'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Single Project
            </button>
            <button
              onClick={() => setIngestionMode('bulk')}
              className={`px-4 py-2 rounded-lg font-medium ${
                ingestionMode === 'bulk'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Bulk Import (JSON)
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          {ingestionMode === 'single' ? (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Title *</label>
                <input
                  type="text"
                  name="title"
                  value={singleProject.title}
                  onChange={handleSingleInputChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter project title"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Description *</label>
                <textarea
                  name="description"
                  value={singleProject.description}
                  onChange={handleSingleInputChange}
                  required
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter project description"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Source URL (optional)</label>
                <input
                  type="url"
                  name="source_url"
                  value={singleProject.source_url}
                  onChange={handleSingleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="https://example.com"
                />
              </div>
            </div>
          ) : (
            <div>
              <label className="block text-sm font-medium mb-1">
                Projects JSON Array (max 50 projects)
              </label>
              <textarea
                value={bulkProjects}
                onChange={(e) => setBulkProjects(e.target.value)}
                rows={10}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                placeholder={`[
  {
    "title": "Project Title",
    "description": "Project Description",
    "source_url": "https://optional-source.com"
  }
]`}
              />
              <p className="mt-2 text-sm text-gray-600">
                Each project must have title and description. Source URL is optional.
              </p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="mt-6 w-full bg-blue-500 text-white py-3 px-4 rounded-md hover:bg-blue-600 disabled:bg-gray-400 font-medium"
          >
            {loading ? 'Ingesting Projects...' : 'Ingest Projects'}
          </button>
        </form>
      </div>

      {/* Results Display */}
      {results && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-6">
          <h3 className="text-xl font-semibold mb-4">Ingestion Results</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{results.success_count || 0}</div>
              <div className="text-sm text-gray-600">Successful</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">{results.skipped_duplicates || 0}</div>
              <div className="text-sm text-gray-600">Duplicates Skipped</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{results.errors?.length || 0}</div>
              <div className="text-sm text-gray-600">Errors</div>
            </div>
          </div>
          {results.errors && results.errors.length > 0 && (
            <div className="mt-4">
              <h4 className="font-medium text-red-700 mb-2">Errors:</h4>
              <ul className="list-disc list-inside text-sm text-red-600 space-y-1">
                {results.errors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
