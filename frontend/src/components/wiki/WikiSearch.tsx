import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Search as SearchIcon,
  Loader2,
  AlertCircle,
  FileText,
  Filter,
  X,
  ChevronDown,
  Calendar,
  Building2,
} from 'lucide-react'
import type { SearchResponse, SearchFilters } from '../../types/wiki'

type SearchType = 'hybrid' | 'vector' | 'category' | 'entity' | 'file' | 'grep'

const SEARCH_TYPE_OPTIONS: { value: SearchType; label: string; description: string }[] = [
  { value: 'hybrid', label: '混合搜尋', description: '語意 + 精確匹配（推薦）' },
  { value: 'vector', label: '語意搜尋', description: '根據文件相似度' },
  { value: 'grep', label: '精確搜尋', description: '完全匹配關鍵字' },
  { value: 'entity', label: '機構搜尋', description: '搜尋金融機構或違規類型' },
  { value: 'category', label: '分類搜尋', description: '依分類名稱搜尋' },
  { value: 'file', label: '檔案搜尋', description: '依檔案名稱搜尋' },
]

interface WikiSearchProps {
  onDocumentSelect?: (docId: string) => void
}

export function WikiSearch({ onDocumentSelect }: WikiSearchProps) {
  const [query, setQuery] = useState('')
  const [searchType, setSearchType] = useState<SearchType>('hybrid')
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState<SearchFilters>({})
  const [isSearchTypeOpen, setIsSearchTypeOpen] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)

  // Search query
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery<SearchResponse>({
    queryKey: ['wiki-search', query, searchType, filters],
    queryFn: async () => {
      const params = new URLSearchParams({
        q: query,
        search_type: searchType,
        limit: '50',
      })

      // Add filters
      if (filters.document_type) params.append('document_type', filters.document_type)
      if (filters.authority) params.append('authority', filters.authority)
      if (filters.institution) params.append('institution', filters.institution)
      if (filters.violation) params.append('violation', filters.violation)
      if (filters.date_from) params.append('date_from', filters.date_from)
      if (filters.date_to) params.append('date_to', filters.date_to)
      if (filters.min_confidence !== undefined) {
        params.append('min_confidence', filters.min_confidence.toString())
      }

      const response = await fetch(`/api/v1/wiki/search?${params}`)
      if (!response.ok) {
        throw new Error('搜尋失敗')
      }
      return response.json()
    },
    enabled: false, // Only run when explicitly triggered
  })

  const handleSearch = () => {
    if (query.trim().length === 0) return
    setHasSearched(true)
    refetch()
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  const handleClearFilters = () => {
    setFilters({})
  }

  const activeFilterCount = Object.values(filters).filter((v) => v !== undefined && v !== null && v !== '').length

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
        <div className="space-y-3">
          {/* Search Input Row */}
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="輸入搜尋關鍵字..."
                className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <button
              onClick={handleSearch}
              disabled={query.trim().length === 0 || isLoading}
              className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
            >
              {isLoading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                '搜尋'
              )}
            </button>
          </div>

          {/* Search Type & Filters Row */}
          <div className="flex items-center gap-2">
            {/* Search Type Dropdown */}
            <div className="relative">
              <button
                onClick={() => setIsSearchTypeOpen(!isSearchTypeOpen)}
                className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-md text-sm font-medium text-gray-700 transition-colors"
              >
                <span>{SEARCH_TYPE_OPTIONS.find((o) => o.value === searchType)?.label}</span>
                <ChevronDown className="h-4 w-4" />
              </button>

              {isSearchTypeOpen && (
                <div className="absolute top-full mt-1 left-0 bg-white border border-gray-200 rounded-lg shadow-lg z-10 min-w-[280px]">
                  {SEARCH_TYPE_OPTIONS.map((option) => (
                    <button
                      key={option.value}
                      onClick={() => {
                        setSearchType(option.value)
                        setIsSearchTypeOpen(false)
                      }}
                      className={`w-full text-left px-4 py-2.5 hover:bg-blue-50 transition-colors ${
                        searchType === option.value ? 'bg-blue-50' : ''
                      }`}
                    >
                      <div className="font-medium text-sm text-gray-900">{option.label}</div>
                      <div className="text-xs text-gray-500 mt-0.5">{option.description}</div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Filter Toggle */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                showFilters || activeFilterCount > 0
                  ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Filter className="h-4 w-4" />
              <span>篩選條件</span>
              {activeFilterCount > 0 && (
                <span className="bg-blue-600 text-white text-xs px-1.5 py-0.5 rounded-full">
                  {activeFilterCount}
                </span>
              )}
            </button>

            {/* Clear Filters */}
            {activeFilterCount > 0 && (
              <button
                onClick={handleClearFilters}
                className="text-sm text-gray-600 hover:text-gray-800 underline"
              >
                清除篩選
              </button>
            )}
          </div>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">進階篩選</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {/* Document Type */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">文件類型</label>
                <input
                  type="text"
                  value={filters.document_type || ''}
                  onChange={(e) => setFilters({ ...filters, document_type: e.target.value })}
                  placeholder="例：裁罰書"
                  className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Authority */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">主管機關</label>
                <input
                  type="text"
                  value={filters.authority || ''}
                  onChange={(e) => setFilters({ ...filters, authority: e.target.value })}
                  placeholder="例：金管會銀行局"
                  className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Institution */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">金融機構</label>
                <input
                  type="text"
                  value={filters.institution || ''}
                  onChange={(e) => setFilters({ ...filters, institution: e.target.value })}
                  placeholder="例：玉山銀行"
                  className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Violation */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">違規類型</label>
                <input
                  type="text"
                  value={filters.violation || ''}
                  onChange={(e) => setFilters({ ...filters, violation: e.target.value })}
                  placeholder="例：洗錢防制"
                  className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Date From */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">起始日期</label>
                <input
                  type="date"
                  value={filters.date_from || ''}
                  onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
                  className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Date To */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">結束日期</label>
                <input
                  type="date"
                  value={filters.date_to || ''}
                  onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
                  className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Min Confidence */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  最低信心度 {filters.min_confidence !== undefined && `(${(filters.min_confidence * 100).toFixed(0)}%)`}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={filters.min_confidence || 0}
                  onChange={(e) => setFilters({ ...filters, min_confidence: parseFloat(e.target.value) })}
                  className="w-full"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Results */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <AlertCircle className="h-5 w-5 text-red-600 mr-2 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold text-red-800">搜尋失敗</h3>
              <p className="text-sm text-red-700 mt-1">
                {error instanceof Error ? error.message : '未知錯誤'}
              </p>
            </div>
          </div>
        </div>
      )}

      {isLoading && (
        <div className="bg-white rounded-lg shadow border border-gray-200 p-8">
          <div className="flex items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-blue-600 mr-2" />
            <span className="text-gray-600">搜尋中...</span>
          </div>
        </div>
      )}

      {!isLoading && !error && data && (
        <div className="bg-white rounded-lg shadow border border-gray-200">
          {/* Results Header */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">搜尋結果</h2>
                <p className="text-sm text-gray-600 mt-1">
                  找到 {data.total_results} 份文件
                  {data.query && <span className="text-gray-400"> · 關鍵字：{data.query}</span>}
                </p>
              </div>
              <div className="text-xs text-gray-500">
                {SEARCH_TYPE_OPTIONS.find((o) => o.value === searchType)?.label}
              </div>
            </div>
          </div>

          {/* Results List */}
          {data.results.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <FileText className="h-12 w-12 mx-auto mb-3 text-gray-400" />
              <p className="text-sm">沒有找到符合條件的文件</p>
              <p className="text-xs text-gray-400 mt-1">試試調整搜尋關鍵字或篩選條件</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {data.results.map((result) => (
                <SearchResultItem
                  key={result.doc_id}
                  result={result}
                  onClick={() => onDocumentSelect?.(result.doc_id)}
                  queryHighlight={data.query}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Initial State (No Search Yet) */}
      {!hasSearched && !isLoading && !data && (
        <div className="bg-white rounded-lg shadow border border-gray-200 p-8 text-center">
          <SearchIcon className="h-12 w-12 mx-auto text-gray-400 mb-3" />
          <p className="text-gray-600 mb-2">輸入關鍵字開始搜尋</p>
          <p className="text-sm text-gray-500">
            支援多種搜尋方式：語意搜尋、精確匹配、機構名稱等
          </p>
        </div>
      )}
    </div>
  )
}

interface SearchResultItemProps {
  result: SearchResponse['results'][0]
  onClick: () => void
  queryHighlight?: string
}

function SearchResultItem({ result, onClick, queryHighlight }: SearchResultItemProps) {
  const highlightText = (text: string, highlights: string[]) => {
    if (!highlights || highlights.length === 0) return text

    // Create regex pattern from all highlights
    const pattern = highlights.map((h) => h.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')
    const regex = new RegExp(`(${pattern})`, 'gi')

    const parts = text.split(regex)
    return parts.map((part, i) =>
      regex.test(part) ? (
        <mark key={i} className="bg-yellow-200 font-medium">
          {part}
        </mark>
      ) : (
        part
      )
    )
  }

  return (
    <button onClick={onClick} className="w-full text-left p-4 hover:bg-blue-50 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          {/* Filename with highlights */}
          <h3 className="text-sm font-medium text-gray-900 mb-2 truncate">
            {result.highlights.length > 0
              ? highlightText(result.filename, result.highlights)
              : result.filename}
          </h3>

          {/* Document Type */}
          {result.document_type && (
            <div className="mb-2">
              <span className="inline-flex items-center px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded font-medium">
                {result.document_type}
              </span>
            </div>
          )}

          {/* Snippet with highlights */}
          {result.snippet && (
            <p className="text-sm text-gray-700 line-clamp-2 mb-2">
              {result.highlights.length > 0
                ? highlightText(result.snippet, result.highlights)
                : result.snippet}
            </p>
          )}

          {/* Highlights badges */}
          {result.highlights.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {result.highlights.slice(0, 5).map((highlight, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center px-2 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded"
                >
                  {highlight}
                </span>
              ))}
              {result.highlights.length > 5 && (
                <span className="inline-flex items-center px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
                  +{result.highlights.length - 5} 更多
                </span>
              )}
            </div>
          )}
        </div>

        {/* Relevance Score */}
        <div className="flex-shrink-0 text-right">
          <div className="text-xs text-gray-500 mb-1">相關度</div>
          <div className="text-lg font-bold text-gray-900">
            {(result.relevance_score * 100).toFixed(0)}%
          </div>
          <div className="mt-1 w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full ${
                result.relevance_score >= 0.8
                  ? 'bg-green-500'
                  : result.relevance_score >= 0.5
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
              }`}
              style={{ width: `${result.relevance_score * 100}%` }}
            />
          </div>
        </div>
      </div>
    </button>
  )
}
