import React from 'react';

const ExplorePage = () => {
  const UI_STATE = "loading";

  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      {/* Header section */}
      <div className="mb-8">
        <h1 className="text-4xl font-light">Explore ideas</h1>
        <p className="mt-2 text-neutral-400">
          Browse project ideas generated from research evidence and novelty analysis.
        </p>
      </div>

      {/* Filter / scope placeholder */}
      <div className="mb-8 bg-neutral-900/60 border border-neutral-800 rounded-lg p-4">
        <div className="flex gap-3">
          <span className="px-4 py-2 border border-neutral-700 bg-neutral-900 hover:border-neutral-600 rounded text-neutral-300">Domain</span>
          <span className="px-4 py-2 border border-neutral-700 bg-neutral-900 hover:border-neutral-600 rounded text-neutral-300">Novelty range</span>
          <span className="px-4 py-2 border border-neutral-700 bg-neutral-900 hover:border-neutral-600 rounded text-neutral-300">Source type</span>
        </div>
      </div>

      <div className="h-px bg-neutral-800 mb-8" />

      {/* Loading state */}
      {UI_STATE === "loading" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="rounded-xl border border-neutral-800 bg-neutral-900 p-6 animate-pulse">
              <div className="h-6 bg-neutral-700 rounded mb-2"></div>
              <div className="h-4 bg-neutral-800 rounded w-16 mb-4"></div>
              <div className="h-1 bg-neutral-700 rounded-full"></div>
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {UI_STATE === "empty" && (
        <div className="rounded-xl border border-neutral-800 bg-neutral-900 py-20">
          <div className="text-center">
            <div className="mx-auto w-16 h-16 bg-neutral-700 rounded-full mb-4"></div>
            <h2 className="text-xl font-medium text-neutral-200 mb-2">No ideas yet</h2>
            <p className="text-neutral-400">Ideas will appear here once generated from research evidence.</p>
          </div>
        </div>
      )}

      {/* Populated state */}
      {UI_STATE === "populated" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="group rounded-xl border border-neutral-800 bg-neutral-900 p-6 hover:border-neutral-600 hover:bg-neutral-800/60 cursor-pointer transition-colors">
            <h3 className="text-lg font-medium text-neutral-200 group-hover:text-neutral-100 transition-colors">Bias-aware clinical triage system</h3>
            <div className="mt-2">
              <span className="px-2 py-1 text-xs bg-neutral-800 text-neutral-300 rounded">Healthcare</span>
            </div>
            <div className="mt-4">
              <div className="text-sm text-neutral-400">Novelty (example)</div>
              <div className="mt-1 w-full bg-neutral-700 rounded-full h-1">
                <div className="bg-neutral-400 h-1 rounded-full" style={{ width: '82%' }}></div>
              </div>
            </div>
            <div className="mt-6 text-xs text-neutral-500 group-hover:text-neutral-400 group-hover:translate-x-0.5 transition-all duration-200">View details</div>
          </div>
          <div className="group rounded-xl border border-neutral-800 bg-neutral-900 p-6 hover:border-neutral-600 hover:bg-neutral-800/60 cursor-pointer transition-colors">
            <h3 className="text-lg font-medium text-neutral-200 group-hover:text-neutral-100 transition-colors">Carbon-aware scheduling systems</h3>
            <div className="mt-2">
              <span className="px-2 py-1 text-xs bg-neutral-800 text-neutral-300 rounded">Climate</span>
            </div>
            <div className="mt-4">
              <div className="text-sm text-neutral-400">Novelty (example)</div>
              <div className="mt-1 w-full bg-neutral-700 rounded-full h-1">
                <div className="bg-neutral-400 h-1 rounded-full" style={{ width: '78%' }}></div>
              </div>
            </div>
            <div className="mt-6 text-xs text-neutral-500 group-hover:text-neutral-400 group-hover:translate-x-0.5 transition-all duration-200">View details</div>
          </div>
          <div className="group rounded-xl border border-neutral-800 bg-neutral-900 p-6 hover:border-neutral-600 hover:bg-neutral-800/60 cursor-pointer transition-colors">
            <h3 className="text-lg font-medium text-neutral-200 group-hover:text-neutral-100 transition-colors">Explainable fraud detection pipelines</h3>
            <div className="mt-2">
              <span className="px-2 py-1 text-xs bg-neutral-800 text-neutral-300 rounded">Fintech</span>
            </div>
            <div className="mt-4">
              <div className="text-sm text-neutral-400">Novelty (example)</div>
              <div className="mt-1 w-full bg-neutral-700 rounded-full h-1">
                <div className="bg-neutral-400 h-1 rounded-full" style={{ width: '85%' }}></div>
              </div>
            </div>
            <div className="mt-6 text-xs text-neutral-500 group-hover:text-neutral-400 group-hover:translate-x-0.5 transition-all duration-200">View details</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExplorePage;
