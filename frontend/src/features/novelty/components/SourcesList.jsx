import React, { useState } from 'react';

const SourcesList = ({ sources, evidenceBreakdown }) => {
  const [showPeripheral, setShowPeripheral] = useState(false);

  const tierConfig = {
    supporting: {
      color: '#10b981',
      bgColor: 'bg-emerald-500/10',
      borderColor: 'border-emerald-500/30',
      label: 'Supporting Evidence',
      icon: '✓',
      description: 'Directly relevant to your problem',
    },
    contextual: {
      color: '#f59e0b',
      bgColor: 'bg-amber-500/10',
      borderColor: 'border-amber-500/30',
      label: 'Contextual Background',
      icon: 'ℹ',
      description: 'Related but not directly applicable',
    },
    peripheral: {
      color: '#6b7280',
      bgColor: 'bg-neutral-500/10',
      borderColor: 'border-neutral-500/30',
      label: 'Peripheral Sources',
      icon: '○',
      description: 'Tangentially related; low relevance',
    },
  };

  const sourcesByTier = {
    supporting: sources.filter((s) => s.relevance_tier === 'supporting'),
    contextual: sources.filter((s) => s.relevance_tier === 'contextual'),
    peripheral: sources.filter((s) => s.relevance_tier === 'peripheral'),
  };

  const renderSourceCard = (source) => (
    <div
      key={source.id || source.url}
      className={`p-3 rounded border ${tierConfig[source.relevance_tier]?.bgColor || 'bg-neutral-500/10'} ${tierConfig[source.relevance_tier]?.borderColor || 'border-neutral-500/30'}`}
    >
      <div className="flex items-start justify-between gap-2">
        <a 
          href={source.url}
          target="_blank"
          rel="noopener noreferrer"
          className={`font-medium text-sm underline break-words flex-1 ${
            source.source_type === 'arxiv' ? 'text-indigo-300 hover:text-indigo-200' : 'text-purple-300 hover:text-purple-200'
          }`}
        >
          {source.title}
        </a>
        <span className={`text-xs px-2 py-0.5 rounded font-semibold ${
          source.source_type === 'arxiv' 
            ? 'bg-indigo-600/40 text-indigo-200' 
            : 'bg-purple-600/40 text-purple-200'
        }`}>
          {source.source_type?.toUpperCase()}
        </span>
      </div>
      
      {source.relevance_explanation && (
        <p className="text-xs text-neutral-400 mt-2 italic">
          {source.relevance_explanation}
        </p>
      )}
      
      {source.summary && (
        <p className="text-xs text-neutral-500 mt-2 line-clamp-2 leading-relaxed">
          {source.summary}
        </p>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Supporting tier */}
      {sourcesByTier.supporting.length > 0 && (
        <div className={`p-4 rounded-lg ${tierConfig.supporting.bgColor} border ${tierConfig.supporting.borderColor}`}>
          <div className="flex items-center gap-3 mb-2">
            <span className="text-lg font-bold" style={{ color: tierConfig.supporting.color }}>
              {tierConfig.supporting.icon}
            </span>
            <h3 className="text-sm font-semibold text-white flex-1">
              {tierConfig.supporting.label}
            </h3>
            <span className="text-xs px-2 py-1 bg-white/10 rounded-full font-semibold text-white
              {sourcesByTier.supporting.length}
            </span>
          </div>
          <p className="text-xs text-neutral-400 mb-3 italic">
            {tierConfig.supporting.description}
          </p>
          <div className="space-y-2">
            {sourcesByTier.supporting.map(renderSourceCard)}
          </div>
        </div>
      )}

      {/* Contextual tier */}
      {sourcesByTier.contextual.length > 0 && (
        <details className={`p-4 rounded-lg ${tierConfig.contextual.bgColor} border ${tierConfig.contextual.borderColor}`}>
          <summary className="flex items-center gap-3 cursor-pointer list-none">
            <span className="text-lg font-bold" style={{ color: tierConfig.contextual.color }}>
              {tierConfig.contextual.icon}
            </span>
            <h3 className="text-sm font-semibold text-white flex-1">
              {tierConfig.contextual.label}
            </h3>
            <span className="text-xs px-2 py-1 bg-white/10 rounded-full font-semibold text-white
              {sourcesByTier.contextual.length}
            </span>
          </summary>
          <p className="text-xs text-neutral-400 mt-2 mb-3 italic">
            {tierConfig.contextual.description}
          </p>
          <div className="space-y-2 mt-3">
            {sourcesByTier.contextual.map(renderSourceCard)}
          </div>
        </details>
      )}

      {/* Peripheral tier — collapsed by default */}
      {sourcesByTier.peripheral.length > 0 && (
        <div className={`p-4 rounded-lg ${tierConfig.peripheral.bgColor} border ${tierConfig.peripheral.borderColor}`}>
          <button
            onClick={() => setShowPeripheral(!showPeripheral)}
            className="w-full flex items-center gap-3 text-left"
          >
            <span className="text-lg font-bold" style={{ color: tierConfig.peripheral.color }}>
              {showPeripheral ? '−' : '+'}
            </span>
            <h3 className="text-sm font-semibold text-neutral-400 flex-1">
              {tierConfig.peripheral.label}
            </h3>
            <span className="text-xs px-2 py-1 bg-white/10 rounded-full font-semibold text-neutral-400
              {sourcesByTier.peripheral.length}
            </span>
          </button>
          
          {showPeripheral && (
            <>
              <p className="text-xs text-neutral-500 mt-2 mb-3 italic">
                {tierConfig.peripheral.description}
              </p>
              <div className="space-y-2 mt-3">
                {sourcesByTier.peripheral.map(renderSourceCard)}
              </div>
            </>
          )}
        </div>
      )}

      {/* Evidence breakdown summary */}
      {evidenceBreakdown && (
        <div className="p-3 bg-white/5 rounded border border-white/10 text-center">
          <p className="text-xs text-neutral-400
            <span className="text-emerald-400 font-semibold">{evidenceBreakdown.supporting || 0}</span> supporting •{' '}
            <span className="text-amber-400 font-semibold">{evidenceBreakdown.contextual || 0}</span> contextual •{' '}
            <span className="text-neutral-500 font-semibold">{evidenceBreakdown.peripheral || 0}</span> peripheral
          </p>
        </div>
      )}
    </div>
  );
};

export default SourcesList;
