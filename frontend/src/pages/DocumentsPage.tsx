/**
 * DocumentsPage - Document Management Console
 *
 * Upload, view, and manage legal documents
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';

interface Document {
  id: string;
  name: string;
  file_path: string;
  size_bytes: number;
  created_at: string;
  updated_at: string;
  chunk_count: number;
  status: string;
  indexed: boolean;
  issuing_authority: string | null;
  related_institutions: string[];
  violation_types: string[];
  penalty_amount: number | null;
  keywords: string[];
  document_type: string | null;
}

interface IndexStatus {
  total_documents: number;
  total_chunks: number;
  last_indexed: string | null;
}

interface DocumentType {
  category: string;
  name_zh: string;
  name_en: string;
  description: string;
  allowed: boolean;
  requires_authority: boolean;
  requires_date: boolean;
  example_filename_pattern: string | null;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [indexStatus, setIndexStatus] = useState<IndexStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Document type selection state
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([]);
  const [selectedDocumentType, setSelectedDocumentType] = useState<string>('penalty');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [pendingFiles, setPendingFiles] = useState<FileList | null>(null);

  const fetchDocuments = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/documents/`);
      if (!response.ok) throw new Error('Failed to fetch documents');
      const data = await response.json();
      // API returns array directly, not {documents: [...]}
      setDocuments(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents');
    }
  }, []);

  const fetchIndexStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/documents/status`);
      if (!response.ok) throw new Error('Failed to fetch index status');
      const data = await response.json();
      setIndexStatus(data);
    } catch (err) {
      console.error('Failed to fetch index status:', err);
    }
  }, []);

  const fetchDocumentTypes = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/documents/types/allowed`);
      if (!response.ok) throw new Error('Failed to fetch document types');
      const data = await response.json();
      setDocumentTypes(data.allowed_types || []);
      // Set default to first allowed type
      if (data.allowed_types && data.allowed_types.length > 0) {
        setSelectedDocumentType(data.allowed_types[0].category);
      }
    } catch (err) {
      console.error('Failed to fetch document types:', err);
    }
  }, []);

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      await Promise.all([fetchDocuments(), fetchIndexStatus(), fetchDocumentTypes()]);
      setIsLoading(false);
    };
    loadData();
  }, [fetchDocuments, fetchIndexStatus, fetchDocumentTypes]);

  // Handle file selection - show modal for document type selection
  const handleFileSelect = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setPendingFiles(files);
    setShowUploadModal(true);
  };

  // Confirm upload with selected document type
  const handleConfirmUpload = async () => {
    if (!pendingFiles || pendingFiles.length === 0) return;

    setShowUploadModal(false);
    setIsUploading(true);
    setUploadProgress('上傳中...');
    setError(null);

    try {
      // Upload files one by one with document type using upload-with-progress
      for (let i = 0; i < pendingFiles.length; i++) {
        const file = pendingFiles[i];
        setUploadProgress(`上傳中 (${i + 1}/${pendingFiles.length}): ${file.name}`);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('document_type', selectedDocumentType);
        formData.append('auto_index', 'true');
        formData.append('extract_metadata', 'true');
        formData.append('duplicate_action', 'version');

        const response = await fetch(`${API_BASE_URL}/api/v1/documents/upload-with-progress`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || `上傳失敗: ${file.name}`);
        }

        const result = await response.json();

        // Check if duplicate detected
        if (result.status === 'duplicate_detected') {
          // For now, skip duplicates - could show a dialog here
          console.log('Duplicate detected:', result.message);
          continue;
        }

        // Poll for progress if we got a job_id
        if (result.job_id) {
          let attempts = 0;
          const maxAttempts = 60; // 30 seconds max wait

          while (attempts < maxAttempts) {
            await new Promise((resolve) => setTimeout(resolve, 500));

            const progressResponse = await fetch(
              `${API_BASE_URL}/api/v1/documents/upload-progress/${result.job_id}`
            );

            if (progressResponse.ok) {
              const progress = await progressResponse.json();
              setUploadProgress(`處理中 (${i + 1}/${pendingFiles.length}): ${progress.message}`);

              if (progress.stage === 'complete' || progress.stage === 'error') {
                if (progress.error) {
                  throw new Error(progress.error);
                }
                break;
              }
            }

            attempts++;
          }
        }
      }

      setUploadProgress('處理完成');
      await new Promise((resolve) => setTimeout(resolve, 500));
      await fetchDocuments();
      await fetchIndexStatus();
      setUploadProgress(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '上傳失敗');
    } finally {
      setIsUploading(false);
      setPendingFiles(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // Cancel upload
  const handleCancelUpload = () => {
    setShowUploadModal(false);
    setPendingFiles(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (documentId: string) => {
    if (!confirm('確定要刪除此文件嗎？')) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/documents/${documentId}`, {
        method: 'DELETE',
      });

      if (!response.ok) throw new Error('Failed to delete document');

      await fetchDocuments();
      await fetchIndexStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed');
    }
  };

  const handleReindexAll = async () => {
    if (!confirm('確定要重新索引所有文件嗎？此操作可能需要幾分鐘。')) return;

    setIsUploading(true);
    setUploadProgress('Reindexing all documents...');

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/documents/reindex-all`, {
        method: 'POST',
      });

      if (!response.ok) throw new Error('Reindex failed');

      await fetchDocuments();
      await fetchIndexStatus();
      setUploadProgress(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Reindex failed');
    } finally {
      setIsUploading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const filteredDocuments = documents.filter((doc) =>
    doc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    doc.related_institutions?.some(inst => inst.toLowerCase().includes(searchQuery.toLowerCase())) ||
    doc.issuing_authority?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-slate-950 bg-grid">
      {/* Navigation */}
      <nav className="border-b border-slate-800/50 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <a href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center">
                  <svg className="w-5 h-5 text-slate-950" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div>
                  <h1 className="text-lg font-serif font-semibold text-slate-50">FinAgent</h1>
                  <p className="text-xs text-slate-500">文件管理</p>
                </div>
              </a>
            </div>
            <div className="flex items-center gap-3">
              <a href="/" className="btn btn-ghost text-sm">研究查詢</a>
              <a href="/wiki" className="btn btn-ghost text-sm">知識庫</a>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <h2 className="text-3xl font-serif font-bold text-slate-50 mb-3">
            文件<span className="text-gradient">管理中心</span>
          </h2>
          <p className="text-slate-400">
            上傳、管理與索引您的法律文件。支援 TXT 格式的裁罰書與判決文件。
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="card p-5">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center">
                <svg className="w-6 h-6 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">文件數量</p>
                <p className="text-2xl font-mono font-semibold text-slate-100">
                  {indexStatus?.total_documents ?? documents.length}
                </p>
              </div>
            </div>
          </div>
          <div className="card p-5">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                <svg className="w-6 h-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                </svg>
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">向量區塊</p>
                <p className="text-2xl font-mono font-semibold text-slate-100">
                  {indexStatus?.total_chunks ?? 0}
                </p>
              </div>
            </div>
          </div>
          <div className="card p-5">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-sky-500/10 flex items-center justify-center">
                <svg className="w-6 h-6 text-sky-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">最後索引</p>
                <p className="text-sm font-medium text-slate-100">
                  {indexStatus?.last_indexed ? formatDate(indexStatus.last_indexed) : '尚未索引'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Action Bar */}
        <div className="card p-4 mb-6">
          <div className="flex flex-col md:flex-row items-stretch md:items-center gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                placeholder="搜尋文件名稱、機構..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="input pl-10"
              />
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3">
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt"
                multiple
                onChange={(e) => handleFileSelect(e.target.files)}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className={`btn btn-primary cursor-pointer ${isUploading ? 'opacity-50 pointer-events-none' : ''}`}
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
                上傳文件
              </label>
              <button
                onClick={handleReindexAll}
                disabled={isUploading}
                className="btn btn-secondary"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                重新索引
              </button>
            </div>
          </div>

          {/* Upload Progress */}
          {uploadProgress && (
            <div className="mt-4 flex items-center gap-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
              <svg className="w-4 h-4 text-amber-400 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <span className="text-sm text-amber-200">{uploadProgress}</span>
            </div>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="card p-4 mb-6 border-rose-500/30 bg-rose-500/5">
            <div className="flex items-center gap-3">
              <svg className="w-5 h-5 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-sm text-rose-200">{error}</p>
              <button onClick={() => setError(null)} className="ml-auto text-rose-400 hover:text-rose-300">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* Document List */}
        <div className="card">
          <div className="p-5 border-b border-slate-800/50">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-serif font-semibold text-slate-100">文件列表</h3>
              <span className="badge badge-slate">{filteredDocuments.length} 筆</span>
            </div>
          </div>

          {isLoading ? (
            <div className="p-12 flex flex-col items-center justify-center">
              <svg className="w-8 h-8 text-amber-400 animate-spin mb-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <p className="text-slate-400">載入中...</p>
            </div>
          ) : filteredDocuments.length === 0 ? (
            <div className="p-12 flex flex-col items-center justify-center">
              <div className="w-16 h-16 rounded-full bg-slate-800/50 flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <p className="text-slate-400 mb-2">尚無文件</p>
              <p className="text-sm text-slate-500">點擊上方「上傳文件」按鈕新增文件</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-800/50">
              {filteredDocuments.map((doc) => (
                <div key={doc.id} className="p-4 hover:bg-slate-800/20 transition-colors group">
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center flex-shrink-0">
                      <svg className="w-5 h-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-medium text-slate-200 truncate">{doc.name}</h4>
                      <div className="flex items-center gap-4 mt-1 text-xs text-slate-500">
                        <span>{formatFileSize(doc.size_bytes)}</span>
                        <span>{doc.chunk_count} 區塊</span>
                        <span>{formatDate(doc.created_at)}</span>
                        {doc.indexed && <span className="text-emerald-500">已索引</span>}
                      </div>
                      <div className="flex flex-wrap items-center gap-2 mt-2">
                        {doc.document_type && (
                          <span className="badge badge-sky">
                            {documentTypes.find(dt => dt.category === doc.document_type)?.name_zh || doc.document_type}
                          </span>
                        )}
                        {doc.issuing_authority && (
                          <span className="badge badge-amber">{doc.issuing_authority}</span>
                        )}
                        {doc.related_institutions?.slice(0, 2).map((inst, i) => (
                          <span key={i} className="badge badge-slate">{inst}</span>
                        ))}
                        {doc.violation_types?.slice(0, 1).map((vt, i) => (
                          <span key={i} className="badge badge-rose">{vt}</span>
                        ))}
                      </div>
                    </div>
                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="opacity-0 group-hover:opacity-100 transition-opacity p-2 text-slate-500 hover:text-rose-400"
                      title="刪除文件"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Document Type Selection Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="card w-full max-w-lg mx-4 p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-serif font-semibold text-slate-100">選擇文件類型</h3>
              <button
                onClick={handleCancelUpload}
                className="text-slate-400 hover:text-slate-200 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Selected Files Info */}
            <div className="mb-6 p-3 rounded-lg bg-slate-800/50 border border-slate-700">
              <p className="text-sm text-slate-400 mb-2">選取的文件:</p>
              <div className="space-y-1 max-h-24 overflow-y-auto">
                {pendingFiles && Array.from(pendingFiles).map((file, i) => (
                  <p key={i} className="text-sm text-slate-200 truncate">{file.name}</p>
                ))}
              </div>
            </div>

            {/* Document Type Selector */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-slate-300 mb-3">
                文件類型 <span className="text-rose-400">*</span>
              </label>
              <p className="text-xs text-slate-500 mb-3">
                請選擇正確的文件類型，以確保文件能被正確分類與索引。
              </p>
              <div className="space-y-2">
                {documentTypes.map((docType) => (
                  <label
                    key={docType.category}
                    className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                      selectedDocumentType === docType.category
                        ? 'border-amber-500/50 bg-amber-500/10'
                        : 'border-slate-700 bg-slate-800/30 hover:border-slate-600'
                    }`}
                  >
                    <input
                      type="radio"
                      name="documentType"
                      value={docType.category}
                      checked={selectedDocumentType === docType.category}
                      onChange={(e) => setSelectedDocumentType(e.target.value)}
                      className="mt-1 w-4 h-4 text-amber-500 border-slate-600 focus:ring-amber-500 focus:ring-offset-slate-900"
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-slate-200">{docType.name_zh}</span>
                        <span className="text-xs text-slate-500">({docType.name_en})</span>
                      </div>
                      <p className="text-xs text-slate-400 mt-1">{docType.description}</p>
                      {docType.example_filename_pattern && (
                        <p className="text-xs text-slate-500 mt-1">
                          範例: <code className="text-amber-400">{docType.example_filename_pattern}</code>
                        </p>
                      )}
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-end gap-3">
              <button
                onClick={handleCancelUpload}
                className="btn btn-ghost"
              >
                取消
              </button>
              <button
                onClick={handleConfirmUpload}
                className="btn btn-primary"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
                確認上傳
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
