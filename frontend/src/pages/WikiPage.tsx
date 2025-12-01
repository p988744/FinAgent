/**
 * WikiPage v2.0 - Financial Legal Knowledge Base
 *
 * A clean, streamlined knowledge explorer for:
 * - Document browsing with search & filters
 * - Category-based navigation
 * - Document detail viewer
 */

import { useState, useEffect, useCallback } from 'react';

// ============================================
// Types (aligned with backend API schemas)
// ============================================

interface DocumentSummary {
  doc_id: string;
  filename: string;
  document_type: string | null;
  issuing_authority: string | null;
  date: string | null;
  related_institutions: string[];
  violation_types: string[];
  extraction_confidence: number | null;
}

interface DocumentDetail extends DocumentSummary {
  file_path: string;
  case_number: string | null;
  penalty_amount: string | null;
  keywords: string[];
  full_content: string | null;
  chunk_count: number;
  indexed: boolean;
  file_size: number | null;
  created_at: string;
  updated_at: string;
}

interface CategorySummary {
  id: number;
  name: string;
  type: string;
  document_count: number;
  description: string | null;
  keywords: string[];
}

interface TopEntity {
  name: string;
  count: number;
  percentage: number;
}

interface WikiOverview {
  total_documents: number;
  total_categories: number;
  categories_by_type: Record<string, number>;
  document_stats: {
    total_documents: number;
    with_metadata: number;
    without_metadata: number;
    by_type: Record<string, number>;
    by_authority: Record<string, number>;
    avg_confidence: number | null;
  };
  recent_documents: DocumentSummary[];
  top_entities: {
    institutions: TopEntity[];
    violations: TopEntity[];
    authorities: TopEntity[];
  };
}

interface SearchResult {
  doc_id: string;
  filename: string;
  document_type: string | null;
  relevance_score: number;
  snippet: string | null;
  highlights: string[];
}

// ============================================
// API Functions
// ============================================

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function fetchOverview(): Promise<WikiOverview> {
  const res = await fetch(`${API_BASE}/api/v1/wiki/overview`);
  if (!res.ok) throw new Error(`Failed to fetch overview: ${res.status}`);
  return res.json();
}

async function fetchDocuments(params: {
  categoryId?: number;
  limit?: number;
  offset?: number;
}): Promise<{ total: number; documents: DocumentSummary[] }> {
  const searchParams = new URLSearchParams();
  if (params.categoryId) searchParams.set('category_id', params.categoryId.toString());
  if (params.limit) searchParams.set('limit', params.limit.toString());
  if (params.offset) searchParams.set('offset', params.offset.toString());

  const res = await fetch(`${API_BASE}/api/v1/wiki/documents?${searchParams}`);
  if (!res.ok) throw new Error(`Failed to fetch documents: ${res.status}`);
  return res.json();
}

async function fetchDocumentDetail(docId: string): Promise<DocumentDetail> {
  const res = await fetch(`${API_BASE}/api/v1/wiki/document/${docId}`);
  if (!res.ok) throw new Error(`Failed to fetch document: ${res.status}`);
  return res.json();
}

async function fetchCategories(type: string): Promise<{ categories: CategorySummary[] }> {
  const res = await fetch(`${API_BASE}/api/v1/wiki/categories?type=${type}`);
  if (!res.ok) throw new Error(`Failed to fetch categories: ${res.status}`);
  return res.json();
}

async function searchDocuments(query: string, searchType: string = 'hybrid'): Promise<{
  results: SearchResult[];
  total_results: number;
}> {
  const params = new URLSearchParams({ q: query, search_type: searchType, limit: '20' });
  const res = await fetch(`${API_BASE}/api/v1/wiki/search?${params}`);
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  return res.json();
}

// ============================================
// Main Component
// ============================================

type ViewMode = 'overview' | 'documents' | 'categories' | 'search';
type CategoryType = 'authority' | 'institution' | 'violation' | 'doc_type';

export default function WikiPage() {
  // State
  const [viewMode, setViewMode] = useState<ViewMode>('overview');
  const [overview, setOverview] = useState<WikiOverview | null>(null);
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [categories, setCategories] = useState<CategorySummary[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<DocumentDetail | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [activeCategory, setActiveCategory] = useState<CategoryType>('authority');
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalDocs, setTotalDocs] = useState(0);
  const [currentPage, setCurrentPage] = useState(0);
  const DOCS_PER_PAGE = 20;

  // Load overview on mount
  useEffect(() => {
    loadOverview();
  }, []);

  const loadOverview = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchOverview();
      setOverview(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load overview');
    } finally {
      setLoading(false);
    }
  };

  const loadDocuments = useCallback(async (categoryId?: number, page = 0) => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchDocuments({
        categoryId,
        limit: DOCS_PER_PAGE,
        offset: page * DOCS_PER_PAGE,
      });
      setDocuments(data.documents);
      setTotalDocs(data.total);
      setCurrentPage(page);
      setSelectedCategoryId(categoryId ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadCategories = useCallback(async (type: CategoryType) => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchCategories(type);
      setCategories(data.categories);
      setActiveCategory(type);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load categories');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadDocumentDetail = async (docId: string) => {
    try {
      setLoading(true);
      const doc = await fetchDocumentDetail(docId);
      setSelectedDoc(doc);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load document');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    try {
      setLoading(true);
      setError(null);
      setViewMode('search');
      const data = await searchDocuments(searchQuery);
      setSearchResults(data.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const navigateToDocuments = (categoryId?: number) => {
    setViewMode('documents');
    loadDocuments(categoryId);
  };

  const navigateToCategories = (type: CategoryType) => {
    setViewMode('categories');
    loadCategories(type);
  };

  // ============================================
  // Render Functions
  // ============================================

  const renderHeader = () => (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-display font-bold text-noir-100 flex items-center gap-3">
            <span className="w-10 h-10 rounded-xl bg-brass-500/20 flex items-center justify-center">
              <svg className="w-5 h-5 text-brass-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
              </svg>
            </span>
            金融法規知識庫
          </h1>
          <p className="text-noir-400 text-sm mt-1">Financial Legal Knowledge Base</p>
        </div>

        {/* Search Bar */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="搜尋文件..."
              className="w-64 bg-noir-800 border border-noir-700 rounded-lg px-4 py-2 text-sm text-noir-200 placeholder-noir-500 focus:outline-none focus:border-brass-500/50"
            />
            <button
              onClick={handleSearch}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-noir-400 hover:text-brass-400 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => { setViewMode('overview'); loadOverview(); }}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            viewMode === 'overview'
              ? 'bg-brass-500/20 text-brass-400 border border-brass-500/30'
              : 'text-noir-400 hover:text-noir-200 hover:bg-noir-800'
          }`}
        >
          總覽
        </button>
        <button
          onClick={() => navigateToDocuments()}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            viewMode === 'documents'
              ? 'bg-brass-500/20 text-brass-400 border border-brass-500/30'
              : 'text-noir-400 hover:text-noir-200 hover:bg-noir-800'
          }`}
        >
          文件庫
        </button>
        <button
          onClick={() => navigateToCategories('authority')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            viewMode === 'categories'
              ? 'bg-brass-500/20 text-brass-400 border border-brass-500/30'
              : 'text-noir-400 hover:text-noir-200 hover:bg-noir-800'
          }`}
        >
          分類瀏覽
        </button>
        {viewMode === 'search' && (
          <span className="px-4 py-2 rounded-lg text-sm font-medium bg-jade-500/20 text-jade-400 border border-jade-500/30">
            搜尋結果
          </span>
        )}
      </div>
    </div>
  );

  const renderOverview = () => {
    if (!overview) return null;

    return (
      <div className="space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-4 gap-4">
          <div className="card p-4">
            <div className="text-3xl font-bold text-brass-400">{overview.total_documents}</div>
            <div className="text-sm text-noir-400 mt-1">總文件數</div>
          </div>
          <div className="card p-4">
            <div className="text-3xl font-bold text-jade-400">{overview.total_categories}</div>
            <div className="text-sm text-noir-400 mt-1">分類數量</div>
          </div>
          <div className="card p-4">
            <div className="text-3xl font-bold text-noir-200">{overview.document_stats.with_metadata}</div>
            <div className="text-sm text-noir-400 mt-1">已標註文件</div>
          </div>
          <div className="card p-4">
            <div className="text-3xl font-bold text-noir-300">
              {overview.document_stats.avg_confidence
                ? `${(overview.document_stats.avg_confidence * 100).toFixed(0)}%`
                : 'N/A'}
            </div>
            <div className="text-sm text-noir-400 mt-1">平均信心度</div>
          </div>
        </div>

        {/* Category Quick Access */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-noir-100 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-brass-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
            </svg>
            分類瀏覽
          </h2>
          <div className="grid grid-cols-4 gap-4">
            {[
              { type: 'authority' as CategoryType, label: '主管機關', count: overview.categories_by_type.authority || 0, icon: '🏛️' },
              { type: 'institution' as CategoryType, label: '金融機構', count: overview.categories_by_type.institution || 0, icon: '🏦' },
              { type: 'violation' as CategoryType, label: '違規類型', count: overview.categories_by_type.violation || 0, icon: '⚠️' },
              { type: 'doc_type' as CategoryType, label: '文件類型', count: overview.categories_by_type.doc_type || 0, icon: '📄' },
            ].map((cat) => (
              <button
                key={cat.type}
                onClick={() => navigateToCategories(cat.type)}
                className="p-4 bg-noir-800/50 rounded-lg border border-noir-700 hover:border-brass-500/30 hover:bg-noir-800 transition-all text-left"
              >
                <div className="text-2xl mb-2">{cat.icon}</div>
                <div className="text-noir-200 font-medium">{cat.label}</div>
                <div className="text-sm text-noir-500">{cat.count} 個分類</div>
              </button>
            ))}
          </div>
        </div>

        {/* Top Entities */}
        <div className="grid grid-cols-3 gap-6">
          {/* Top Authorities */}
          <div className="card p-6">
            <h3 className="text-base font-semibold text-noir-100 mb-4">熱門主管機關</h3>
            <div className="space-y-3">
              {overview.top_entities.authorities.slice(0, 5).map((entity, idx) => (
                <div key={entity.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-noir-500 w-4">{idx + 1}</span>
                    <span className="text-sm text-noir-300">{entity.name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-noir-500">{entity.count}</span>
                    <div className="w-16 h-1.5 bg-noir-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-brass-500 rounded-full"
                        style={{ width: `${entity.percentage}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Top Institutions */}
          <div className="card p-6">
            <h3 className="text-base font-semibold text-noir-100 mb-4">熱門金融機構</h3>
            <div className="space-y-3">
              {overview.top_entities.institutions.slice(0, 5).map((entity, idx) => (
                <div key={entity.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-noir-500 w-4">{idx + 1}</span>
                    <span className="text-sm text-noir-300 truncate max-w-32">{entity.name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-noir-500">{entity.count}</span>
                    <div className="w-16 h-1.5 bg-noir-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-jade-500 rounded-full"
                        style={{ width: `${entity.percentage}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Top Violations */}
          <div className="card p-6">
            <h3 className="text-base font-semibold text-noir-100 mb-4">熱門違規類型</h3>
            <div className="space-y-3">
              {overview.top_entities.violations.slice(0, 5).map((entity, idx) => (
                <div key={entity.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-noir-500 w-4">{idx + 1}</span>
                    <span className="text-sm text-noir-300 truncate max-w-32">{entity.name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-noir-500">{entity.count}</span>
                    <div className="w-16 h-1.5 bg-noir-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-vermilion-500 rounded-full"
                        style={{ width: `${entity.percentage}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Recent Documents */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-noir-100 flex items-center gap-2">
              <svg className="w-5 h-5 text-brass-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              最新文件
            </h2>
            <button
              onClick={() => navigateToDocuments()}
              className="text-sm text-brass-400 hover:text-brass-300 transition-colors"
            >
              查看全部 →
            </button>
          </div>
          <div className="space-y-2">
            {overview.recent_documents.slice(0, 5).map((doc) => (
              <button
                key={doc.doc_id}
                onClick={() => loadDocumentDetail(doc.doc_id)}
                className="w-full p-3 bg-noir-800/50 rounded-lg border border-noir-700 hover:border-brass-500/30 transition-all text-left"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-noir-200 font-medium truncate">{doc.filename}</div>
                    <div className="flex items-center gap-3 mt-1 text-xs text-noir-500">
                      {doc.issuing_authority && <span>{doc.issuing_authority}</span>}
                      {doc.date && <span>{doc.date}</span>}
                      {doc.document_type && (
                        <span className="badge badge-neutral">{doc.document_type}</span>
                      )}
                    </div>
                  </div>
                  {doc.extraction_confidence && (
                    <div className="text-xs text-noir-500">
                      {(doc.extraction_confidence * 100).toFixed(0)}%
                    </div>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderDocuments = () => (
    <div className="space-y-4">
      {/* Header with filter info */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-noir-400">
          共 {totalDocs} 筆文件
          {selectedCategoryId && (
            <button
              onClick={() => loadDocuments()}
              className="ml-2 text-brass-400 hover:text-brass-300"
            >
              清除篩選
            </button>
          )}
        </div>
        <div className="flex items-center gap-2">
          {currentPage > 0 && (
            <button
              onClick={() => loadDocuments(selectedCategoryId ?? undefined, currentPage - 1)}
              className="px-3 py-1 text-sm bg-noir-800 text-noir-300 rounded hover:bg-noir-700"
            >
              ← 上一頁
            </button>
          )}
          <span className="text-sm text-noir-500">
            第 {currentPage + 1} / {Math.ceil(totalDocs / DOCS_PER_PAGE)} 頁
          </span>
          {(currentPage + 1) * DOCS_PER_PAGE < totalDocs && (
            <button
              onClick={() => loadDocuments(selectedCategoryId ?? undefined, currentPage + 1)}
              className="px-3 py-1 text-sm bg-noir-800 text-noir-300 rounded hover:bg-noir-700"
            >
              下一頁 →
            </button>
          )}
        </div>
      </div>

      {/* Document List */}
      <div className="space-y-2">
        {documents.map((doc) => (
          <button
            key={doc.doc_id}
            onClick={() => loadDocumentDetail(doc.doc_id)}
            className="w-full card p-4 hover:border-brass-500/30 transition-all text-left"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="text-noir-200 font-medium">{doc.filename}</div>
                <div className="flex items-center gap-3 mt-2 text-sm text-noir-500">
                  {doc.issuing_authority && (
                    <span className="flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-brass-500" />
                      {doc.issuing_authority}
                    </span>
                  )}
                  {doc.date && <span>{doc.date}</span>}
                </div>
                {doc.violation_types.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {doc.violation_types.slice(0, 3).map((viol) => (
                      <span key={viol} className="badge badge-neutral text-2xs">{viol}</span>
                    ))}
                    {doc.violation_types.length > 3 && (
                      <span className="text-2xs text-noir-500">+{doc.violation_types.length - 3}</span>
                    )}
                  </div>
                )}
              </div>
              <div className="flex flex-col items-end gap-2">
                {doc.document_type && (
                  <span className="badge badge-brass text-xs">{doc.document_type}</span>
                )}
                {doc.extraction_confidence && (
                  <span className="text-xs text-noir-500">
                    信心度: {(doc.extraction_confidence * 100).toFixed(0)}%
                  </span>
                )}
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );

  const renderCategories = () => (
    <div className="space-y-4">
      {/* Category Type Tabs */}
      <div className="flex items-center gap-2 mb-4">
        {[
          { type: 'authority' as CategoryType, label: '主管機關' },
          { type: 'institution' as CategoryType, label: '金融機構' },
          { type: 'violation' as CategoryType, label: '違規類型' },
          { type: 'doc_type' as CategoryType, label: '文件類型' },
        ].map((tab) => (
          <button
            key={tab.type}
            onClick={() => loadCategories(tab.type)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeCategory === tab.type
                ? 'bg-brass-500/20 text-brass-400 border border-brass-500/30'
                : 'text-noir-400 hover:text-noir-200 hover:bg-noir-800'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Category List */}
      <div className="grid grid-cols-2 gap-4">
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => navigateToDocuments(cat.id)}
            className="card p-4 hover:border-brass-500/30 transition-all text-left"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="text-noir-200 font-medium">{cat.name}</div>
                {cat.description && (
                  <div className="text-sm text-noir-500 mt-1 line-clamp-2">{cat.description}</div>
                )}
                {cat.keywords.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {cat.keywords.slice(0, 3).map((kw) => (
                      <span key={kw} className="text-2xs px-1.5 py-0.5 bg-noir-700 text-noir-400 rounded">
                        {kw}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <div className="flex items-center gap-1 text-brass-400">
                <span className="text-lg font-bold">{cat.document_count}</span>
                <span className="text-xs text-noir-500">筆</span>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );

  const renderSearchResults = () => (
    <div className="space-y-4">
      <div className="text-sm text-noir-400 mb-4">
        搜尋「<span className="text-brass-400">{searchQuery}</span>」共找到 {searchResults.length} 筆結果
      </div>

      <div className="space-y-2">
        {searchResults.map((result) => (
          <button
            key={result.doc_id}
            onClick={() => loadDocumentDetail(result.doc_id)}
            className="w-full card p-4 hover:border-brass-500/30 transition-all text-left"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="text-noir-200 font-medium">{result.filename}</div>
                {result.snippet && (
                  <div className="text-sm text-noir-500 mt-1 line-clamp-2">{result.snippet}</div>
                )}
                {result.highlights.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {result.highlights.map((hl, idx) => (
                      <span key={idx} className="badge badge-jade text-2xs">{hl}</span>
                    ))}
                  </div>
                )}
              </div>
              <div className="flex flex-col items-end gap-2">
                {result.document_type && (
                  <span className="badge badge-brass text-xs">{result.document_type}</span>
                )}
                <span className="text-xs text-noir-500">
                  相關度: {(result.relevance_score * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );

  const renderDocumentModal = () => {
    if (!selectedDoc) return null;

    return (
      <div className="fixed inset-0 bg-noir-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-8">
        <div className="bg-noir-900 border border-noir-700 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
          {/* Modal Header */}
          <div className="p-6 border-b border-noir-700 flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-semibold text-noir-100 truncate">{selectedDoc.filename}</h2>
              <div className="flex items-center gap-3 mt-2 text-sm text-noir-400">
                {selectedDoc.issuing_authority && <span>{selectedDoc.issuing_authority}</span>}
                {selectedDoc.date && <span>{selectedDoc.date}</span>}
                {selectedDoc.case_number && <span>案號: {selectedDoc.case_number}</span>}
              </div>
            </div>
            <button
              onClick={() => setSelectedDoc(null)}
              className="p-2 text-noir-400 hover:text-noir-200 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Modal Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Metadata Grid */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-noir-800/50 rounded-lg p-4">
                <div className="text-xs text-noir-500 mb-1">文件類型</div>
                <div className="text-sm text-noir-200">{selectedDoc.document_type || '未分類'}</div>
              </div>
              <div className="bg-noir-800/50 rounded-lg p-4">
                <div className="text-xs text-noir-500 mb-1">信心度</div>
                <div className="text-sm text-noir-200">
                  {selectedDoc.extraction_confidence
                    ? `${(selectedDoc.extraction_confidence * 100).toFixed(0)}%`
                    : 'N/A'}
                </div>
              </div>
              {selectedDoc.penalty_amount && (
                <div className="bg-noir-800/50 rounded-lg p-4">
                  <div className="text-xs text-noir-500 mb-1">裁罰金額</div>
                  <div className="text-sm text-brass-400">{selectedDoc.penalty_amount}</div>
                </div>
              )}
              <div className="bg-noir-800/50 rounded-lg p-4">
                <div className="text-xs text-noir-500 mb-1">向量索引</div>
                <div className="text-sm text-noir-200">
                  {selectedDoc.indexed ? (
                    <span className="text-jade-400">已索引 ({selectedDoc.chunk_count} chunks)</span>
                  ) : (
                    <span className="text-noir-500">未索引</span>
                  )}
                </div>
              </div>
            </div>

            {/* Related Institutions */}
            {selectedDoc.related_institutions.length > 0 && (
              <div>
                <div className="text-sm font-medium text-noir-300 mb-2">相關機構</div>
                <div className="flex flex-wrap gap-2">
                  {selectedDoc.related_institutions.map((inst) => (
                    <span key={inst} className="badge badge-neutral">{inst}</span>
                  ))}
                </div>
              </div>
            )}

            {/* Violation Types */}
            {selectedDoc.violation_types.length > 0 && (
              <div>
                <div className="text-sm font-medium text-noir-300 mb-2">違規類型</div>
                <div className="flex flex-wrap gap-2">
                  {selectedDoc.violation_types.map((viol) => (
                    <span key={viol} className="badge badge-vermilion">{viol}</span>
                  ))}
                </div>
              </div>
            )}

            {/* Keywords */}
            {selectedDoc.keywords.length > 0 && (
              <div>
                <div className="text-sm font-medium text-noir-300 mb-2">關鍵詞</div>
                <div className="flex flex-wrap gap-2">
                  {selectedDoc.keywords.map((kw) => (
                    <span key={kw} className="text-xs px-2 py-1 bg-noir-700 text-noir-300 rounded">{kw}</span>
                  ))}
                </div>
              </div>
            )}

            {/* Full Content */}
            {selectedDoc.full_content && (
              <div>
                <div className="text-sm font-medium text-noir-300 mb-2">文件內容</div>
                <div className="bg-noir-800/50 rounded-lg p-4 max-h-96 overflow-y-auto">
                  <pre className="text-sm text-noir-300 whitespace-pre-wrap font-sans leading-relaxed">
                    {selectedDoc.full_content}
                  </pre>
                </div>
              </div>
            )}
          </div>

          {/* Modal Footer */}
          <div className="p-4 border-t border-noir-700 flex items-center justify-between text-xs text-noir-500">
            <span>建立時間: {selectedDoc.created_at}</span>
            <span>更新時間: {selectedDoc.updated_at}</span>
          </div>
        </div>
      </div>
    );
  };

  // ============================================
  // Main Render
  // ============================================

  return (
    <div className="min-h-screen bg-noir-950 p-6">
      <div className="max-w-6xl mx-auto">
        {renderHeader()}

        {/* Error State */}
        {error && (
          <div className="mb-6 p-4 bg-vermilion-500/10 border border-vermilion-500/30 rounded-lg text-vermilion-400">
            {error}
          </div>
        )}

        {/* Loading State */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="flex items-center gap-3 text-noir-400">
              <div className="w-5 h-5 border-2 border-brass-500 border-t-transparent rounded-full animate-spin" />
              載入中...
            </div>
          </div>
        ) : (
          <>
            {viewMode === 'overview' && renderOverview()}
            {viewMode === 'documents' && renderDocuments()}
            {viewMode === 'categories' && renderCategories()}
            {viewMode === 'search' && renderSearchResults()}
          </>
        )}

        {/* Document Detail Modal */}
        {renderDocumentModal()}
      </div>
    </div>
  );
}
