/**
 * DocumentContentModal Component
 *
 * Modal to display original document content for citations
 */

import React, { useState, useEffect } from 'react';

interface DocumentContentModalProps {
  isOpen: boolean;
  onClose: () => void;
  source: string;
  citationContent?: string;
  relevance?: number;
}

interface DocumentData {
  id: string;
  content: string;
  size_chars: number;
  file_path: string;
  document_type?: string;
  issuing_authority?: string;
  description?: string;
}

interface DocumentMetadata {
  id: string;
  name: string;
  document_type?: string;
  description?: string;
  issuing_authority?: string;
  related_institutions?: string[];
  violation_types?: string[];
  penalty_amount?: string;
  keywords?: string[];
}

export function DocumentContentModal({
  isOpen,
  onClose,
  source,
  citationContent,
  relevance,
}: DocumentContentModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentData, setDocumentData] = useState<DocumentData | null>(null);
  const [documentMeta, setDocumentMeta] = useState<DocumentMetadata | null>(null);

  // Fetch document content when modal opens
  useEffect(() => {
    if (isOpen && source) {
      fetchDocumentContent();
    }
  }, [isOpen, source]);

  const fetchDocumentContent = async () => {
    setLoading(true);
    setError(null);
    setDocumentData(null);
    setDocumentMeta(null);

    try {
      // First, find the document by filename
      const listResponse = await fetch('/api/v1/documents/');
      if (!listResponse.ok) {
        throw new Error('Failed to fetch document list');
      }

      const documents: DocumentMetadata[] = await listResponse.json();

      // Find document by matching source filename
      const doc = documents.find((d) => {
        // Match by exact name or by partial match (source might be truncated)
        return d.name === source || source.includes(d.name) || d.name.includes(source);
      });

      if (!doc) {
        throw new Error(`Document not found: ${source}`);
      }

      setDocumentMeta(doc);

      // Fetch full content
      const contentResponse = await fetch(`/api/v1/documents/${doc.id}/content`);
      if (!contentResponse.ok) {
        throw new Error('Failed to fetch document content');
      }

      const content: DocumentData = await contentResponse.json();
      setDocumentData(content);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm" />

      {/* Modal Content */}
      <div
        className="relative w-full max-w-4xl max-h-[85vh] mx-4 bg-slate-900 rounded-xl border border-slate-800 shadow-2xl flex flex-col animate-in"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800">
          <div className="flex items-center gap-3 min-w-0 flex-1">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center flex-shrink-0">
              <svg
                className="w-5 h-5 text-amber-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <div className="min-w-0">
              <h2 className="text-lg font-serif font-semibold text-slate-100 truncate">
                {source}
              </h2>
              {documentMeta?.document_type && (
                <p className="text-xs text-amber-400 mt-0.5">
                  {getDocumentTypeLabel(documentMeta.document_type)}
                </p>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-slate-800 transition-colors text-slate-400 hover:text-slate-200"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Citation Preview */}
        {citationContent && (
          <div className="px-5 py-3 bg-amber-500/5 border-b border-slate-800">
            <div className="flex items-start gap-2">
              <svg
                className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                />
              </svg>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">
                  引用片段
                  {relevance !== undefined && (
                    <span className="ml-2 text-amber-400">
                      相關度: {(relevance * 100).toFixed(0)}%
                    </span>
                  )}
                </p>
                <p className="text-sm text-slate-300 italic leading-relaxed">
                  "{citationContent}"
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Metadata */}
        {documentMeta && (
          <div className="px-5 py-3 border-b border-slate-800 bg-slate-800/30">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
              {documentMeta.issuing_authority && (
                <div>
                  <span className="text-slate-500 uppercase tracking-wider">發布機關</span>
                  <p className="text-slate-200 font-medium mt-0.5">
                    {documentMeta.issuing_authority}
                  </p>
                </div>
              )}
              {documentMeta.violation_types && documentMeta.violation_types.length > 0 && (
                <div>
                  <span className="text-slate-500 uppercase tracking-wider">違規類型</span>
                  <p className="text-slate-200 font-medium mt-0.5">
                    {documentMeta.violation_types.join(', ')}
                  </p>
                </div>
              )}
              {documentMeta.penalty_amount && (
                <div>
                  <span className="text-slate-500 uppercase tracking-wider">裁罰金額</span>
                  <p className="text-rose-400 font-medium mt-0.5">
                    {documentMeta.penalty_amount}
                  </p>
                </div>
              )}
              {documentData && (
                <div>
                  <span className="text-slate-500 uppercase tracking-wider">文件長度</span>
                  <p className="text-slate-200 font-mono mt-0.5">
                    {documentData.size_chars.toLocaleString()} 字
                  </p>
                </div>
              )}
            </div>
            {documentMeta.keywords && documentMeta.keywords.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {documentMeta.keywords.slice(0, 8).map((keyword, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 text-xs bg-slate-700/50 text-slate-300 rounded-full"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Content Area */}
        <div className="flex-1 overflow-auto p-5">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="flex items-center gap-3 text-slate-400">
                <svg
                  className="w-5 h-5 animate-spin"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                <span>載入文件內容...</span>
              </div>
            </div>
          )}

          {error && (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="w-12 h-12 mx-auto rounded-full bg-rose-500/10 flex items-center justify-center mb-3">
                  <svg
                    className="w-6 h-6 text-rose-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </div>
                <p className="text-sm text-rose-400">{error}</p>
              </div>
            </div>
          )}

          {documentData && !loading && !error && (
            <div className="prose prose-invert prose-sm max-w-none">
              <pre className="whitespace-pre-wrap font-sans text-sm text-slate-200 leading-relaxed bg-transparent p-0 overflow-x-auto">
                {documentData.content}
              </pre>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-5 py-3 border-t border-slate-800 bg-slate-800/30">
          <div className="text-xs text-slate-500">
            {documentMeta?.description || '金融監管文件'}
          </div>
          <button
            onClick={onClose}
            className="btn btn-secondary text-sm"
          >
            關閉
          </button>
        </div>
      </div>
    </div>
  );
}

function getDocumentTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    penalty: '裁罰書',
    legal_provision: '法條',
    court_judgment: '判決書',
    regulatory_notice: '監管公告',
    knowledge_base: '知識文件',
    '裁罰書': '裁罰書',
    '法規條文': '法條',
    '判決書': '判決書',
    '監管公告': '監管公告',
    '知識文件': '知識文件',
  };
  return labels[type] || type;
}
