/**
 * CitationInline - Inline citation marker with hover preview
 */

import { useState, useRef } from 'react';
import type { Citation } from '../../types';

interface CitationInlineProps {
  citation: Citation;
  onClick?: () => void;
}

export function CitationInline({ citation, onClick }: CitationInlineProps) {
  const [showPreview, setShowPreview] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const previewRef = useRef<HTMLDivElement>(null);

  const handleMouseEnter = () => {
    timeoutRef.current = setTimeout(() => setShowPreview(true), 300);
  };

  const handleMouseLeave = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setShowPreview(false);
  };

  return (
    <span className="relative inline-block">
      <button
        className="citation-inline"
        onClick={onClick}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        {citation.number}
      </button>

      {/* Hover Preview */}
      {showPreview && (
        <div
          ref={previewRef}
          className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 animate-scale-in"
          onMouseEnter={() => setShowPreview(true)}
          onMouseLeave={handleMouseLeave}
        >
          <div className="citation-card">
            <div className="citation-card-header">
              <span className="citation-card-number">{citation.number}</span>
              {citation.relevance && (
                <span className="text-2xs text-noir-500">
                  相關度: {Math.round(citation.relevance * 100)}%
                </span>
              )}
            </div>
            <p className="citation-card-content line-clamp-3">
              {citation.content}
            </p>
            <div className="citation-card-meta">
              <span className="font-mono">{citation.source}</span>
              {citation.metadata?.date && (
                <span>{citation.metadata.date}</span>
              )}
            </div>
          </div>
          {/* Arrow */}
          <div className="absolute left-1/2 -translate-x-1/2 -bottom-1.5 w-3 h-3 bg-noir-900 border-r border-b border-noir-700/50 transform rotate-45" />
        </div>
      )}
    </span>
  );
}
