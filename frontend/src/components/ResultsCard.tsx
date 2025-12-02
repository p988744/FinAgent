/**
 * ResultsCard Component
 *
 * Research results display with editorial-style typography
 */

import { useState } from 'react';
import type { QueryResult, Citation } from '../types/async-api';
import { DocumentContentModal } from './DocumentContentModal';

interface ResultsCardProps {
  sessionId: string;
  queryText: string;
  result: QueryResult;
}

export function ResultsCard({ sessionId, queryText, result }: ResultsCardProps) {
  const [copied, setCopied] = useState(false);
  const [showAllCitations, setShowAllCitations] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);

  const handleCopyToClipboard = () => {
    const textToCopy = `# 查詢問題\n${queryText}\n\n# 研究結果\n${result.response}\n\n# 處理時間\n${result.processing_time.toFixed(1)} 秒`;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const visibleCitations = showAllCitations
    ? result.citations
    : result.citations?.slice(0, 3);

  return (
    <div className="card animate-in">
      {/* Header */}
      <div className="p-6 border-b border-slate-800/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center">
              <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-serif font-semibold text-slate-100">研究結果</h2>
              <p className="text-xs text-slate-500">分析完成</p>
            </div>
          </div>
          <button
            onClick={handleCopyToClipboard}
            className="btn btn-ghost text-sm"
            title="複製到剪貼簿"
          >
            {copied ? (
              <>
                <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-emerald-400">已複製</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                複製
              </>
            )}
          </button>
        </div>
      </div>

      {/* Query Recap */}
      <div className="px-6 py-4 bg-slate-800/30 border-b border-slate-800/50">
        <div className="flex items-start gap-3">
          <svg className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">查詢問題</p>
            <p className="text-sm text-slate-200 leading-relaxed">{queryText}</p>
          </div>
        </div>
      </div>

      {/* Response Content */}
      <div className="p-6 border-b border-slate-800/50">
        <div className="flex items-center gap-2 mb-4">
          <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="text-sm text-slate-400 uppercase tracking-wider">研究分析</h3>
        </div>
        <div className="prose prose-invert prose-sm max-w-none">
          <div className="text-slate-200 leading-relaxed whitespace-pre-wrap font-sans">
            {result.response}
          </div>
        </div>
      </div>

      {/* Citations */}
      {result.citations && result.citations.length > 0 && (
        <div className="p-6 border-b border-slate-800/50">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
              <h3 className="text-sm text-slate-400 uppercase tracking-wider">引用來源</h3>
            </div>
            <span className="badge badge-slate">{result.citations.length} 筆</span>
          </div>

          <div className="space-y-3">
            {visibleCitations?.map((citation, index) => (
              <div
                key={index}
                className="group p-4 rounded-lg bg-slate-800/30 border border-slate-700/30 hover:border-amber-500/30 hover:bg-slate-800/50 transition-all duration-200 cursor-pointer"
                onClick={() => setSelectedCitation(citation)}
              >
                <div className="flex items-start gap-3">
                  <span className="inline-flex items-center justify-center w-6 h-6 text-xs font-mono font-semibold bg-amber-500/10 text-amber-400 rounded border border-amber-500/20">
                    {index + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <p className="text-sm font-medium text-slate-200 truncate flex-1">
                        {citation.source}
                      </p>
                      <span className="text-xs text-amber-400 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 flex-shrink-0">
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                        查看原文
                      </span>
                    </div>
                    {citation.content && (
                      <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                        {citation.content}
                      </p>
                    )}
                    {citation.relevance !== undefined && (
                      <div className="flex items-center gap-2 mt-2">
                        <div className="flex-1 h-1 bg-slate-700 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-amber-500 to-amber-400 rounded-full"
                            style={{ width: `${citation.relevance * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-xs font-mono text-slate-500">
                          {(citation.relevance * 100).toFixed(0)}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {result.citations.length > 3 && (
            <button
              onClick={() => setShowAllCitations(!showAllCitations)}
              className="w-full mt-4 py-2 text-sm text-slate-400 hover:text-slate-200 transition-colors"
            >
              {showAllCitations
                ? '收起引用'
                : `顯示全部 ${result.citations.length} 筆引用`}
            </button>
          )}
        </div>
      )}

      {/* Metadata Footer */}
      <div className="p-6">
        <div className="meta-grid">
          <div className="meta-item">
            <span className="meta-label">處理時間</span>
            <span className="meta-value">{result.processing_time.toFixed(1)}s</span>
          </div>
          {result.metadata?.total_tokens && (
            <div className="meta-item">
              <span className="meta-label">Token 用量</span>
              <span className="meta-value">{result.metadata.total_tokens.toLocaleString()}</span>
            </div>
          )}
          {result.metadata?.llm_cost_usd !== undefined && (
            <div className="meta-item">
              <span className="meta-label">估計成本</span>
              <span className="meta-value">${result.metadata.llm_cost_usd.toFixed(4)}</span>
            </div>
          )}
          <div className="meta-item">
            <span className="meta-label">Session</span>
            <span className="meta-value">{sessionId.slice(0, 8)}</span>
          </div>
        </div>
      </div>

      {/* Document Content Modal */}
      <DocumentContentModal
        isOpen={!!selectedCitation}
        onClose={() => setSelectedCitation(null)}
        source={selectedCitation?.source || ''}
        citationContent={selectedCitation?.content}
        relevance={selectedCitation?.relevance}
      />
    </div>
  );
}
