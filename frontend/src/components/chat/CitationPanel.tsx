/**
 * CitationPanel - Side panel showing all citations for a message
 */

import type { Citation } from '../../types';

interface CitationPanelProps {
  citations: Citation[];
  activeCitation?: string;
  onCitationClick?: (citation: Citation) => void;
  onClose?: () => void;
}

export function CitationPanel({
  citations,
  activeCitation,
  onCitationClick,
  onClose,
}: CitationPanelProps) {
  if (citations.length === 0) return null;

  return (
    <div className="w-80 h-full bg-noir-900/95 backdrop-blur-xl border-l border-noir-700/50 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-noir-700/30">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-brass-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span className="text-sm font-medium text-noir-200">引用來源</span>
          <span className="badge badge-neutral">{citations.length}</span>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="btn btn-ghost btn-icon p-1.5"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Citations List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3 scrollbar-thin">
        {citations.map((citation) => (
          <button
            key={citation.id}
            onClick={() => onCitationClick?.(citation)}
            className={`w-full text-left citation-card card-interactive p-4 ${
              activeCitation === citation.id ? 'border-brass-500/50 shadow-glow-brass' : ''
            }`}
          >
            {/* Header */}
            <div className="flex items-start justify-between gap-2 mb-2">
              <span className="badge badge-brass">{citation.number}</span>
              {citation.relevance && (
                <div className="flex items-center gap-1">
                  <div className="w-12 h-1 bg-noir-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-jade-500 rounded-full"
                      style={{ width: `${citation.relevance * 100}%` }}
                    />
                  </div>
                  <span className="text-2xs text-noir-500">
                    {Math.round(citation.relevance * 100)}%
                  </span>
                </div>
              )}
            </div>

            {/* Source */}
            <p className="text-xs font-mono text-brass-400/80 mb-2 line-clamp-1">
              {citation.source}
            </p>

            {/* Content Preview */}
            <p className="text-sm text-noir-300 line-clamp-3 leading-relaxed">
              {citation.content}
            </p>

            {/* Metadata */}
            {citation.metadata && (
              <div className="mt-3 pt-2 border-t border-noir-700/30 flex flex-wrap gap-2">
                {citation.metadata.institution && (
                  <span className="text-2xs text-noir-500 flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                    {citation.metadata.institution}
                  </span>
                )}
                {citation.metadata.date && (
                  <span className="text-2xs text-noir-500 flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    {citation.metadata.date}
                  </span>
                )}
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
