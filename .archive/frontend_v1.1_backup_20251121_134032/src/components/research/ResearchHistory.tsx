import { useState, useEffect } from 'react'
import { History, Search, Clock, CheckCircle, XCircle, Loader2, Bookmark, BookmarkCheck } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { zhTW } from 'date-fns/locale'

interface ResearchSession {
  session_id: string
  query_text: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  celery_task_id: string
  started_at: string
  completed_at?: string
  processing_time_seconds?: number
  is_bookmarked: boolean
  created_at: string
}

interface ResearchHistoryResponse {
  sessions: ResearchSession[]
  total: number
}

interface ResearchHistoryProps {
  onSelectSession?: (sessionId: string) => void
}

export function ResearchHistory({ onSelectSession }: ResearchHistoryProps) {
  const [sessions, setSessions] = useState<ResearchSession[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')
  const [page, setPage] = useState(0)
  const limit = 10

  // Fetch history from API
  const fetchHistory = async () => {
    setLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: (page * limit).toString(),
      })

      if (statusFilter) {
        params.append('status', statusFilter)
      }

      const response = await fetch(`/api/v1/research/history?${params}`)
      if (!response.ok) {
        throw new Error('無法載入研究歷史')
      }

      const data: ResearchHistoryResponse = await response.json()
      setSessions(data.sessions)
      setTotal(data.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : '載入失敗')
    } finally {
      setLoading(false)
    }
  }

  // Fetch on mount and when filters change
  useEffect(() => {
    fetchHistory()
  }, [page, statusFilter])

  // Filter sessions by search query (client-side)
  const filteredSessions = sessions.filter((session) =>
    session.query_text.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Get status badge
  const getStatusBadge = (status: ResearchSession['status']) => {
    switch (status) {
      case 'completed':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
            <CheckCircle className="h-3 w-3 mr-1" />
            已完成
          </span>
        )
      case 'failed':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
            <XCircle className="h-3 w-3 mr-1" />
            失敗
          </span>
        )
      case 'in_progress':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
            <Loader2 className="h-3 w-3 mr-1 animate-spin" />
            處理中
          </span>
        )
      case 'pending':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
            <Clock className="h-3 w-3 mr-1" />
            等待中
          </span>
        )
    }
  }

  // Format time ago
  const formatTimeAgo = (dateString: string) => {
    try {
      return formatDistanceToNow(new Date(dateString), {
        addSuffix: true,
        locale: zhTW,
      })
    } catch {
      return dateString
    }
  }

  return (
    <div className="bg-white rounded-lg shadow border border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <History className="h-5 w-5 text-gray-600" />
            <h2 className="text-lg font-semibold text-gray-900">研究歷史</h2>
            {total > 0 && (
              <span className="text-sm text-gray-500">({total} 筆)</span>
            )}
          </div>
          <button
            onClick={fetchHistory}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            重新整理
          </button>
        </div>

        {/* Filters */}
        <div className="flex space-x-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="搜尋查詢內容..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value)
              setPage(0)
            }}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">全部狀態</option>
            <option value="completed">已完成</option>
            <option value="in_progress">處理中</option>
            <option value="failed">失敗</option>
          </select>
        </div>
      </div>

      {/* Session List */}
      <div className="divide-y divide-gray-200">
        {loading ? (
          <div className="p-8 text-center">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400 mx-auto mb-2" />
            <p className="text-sm text-gray-500">載入中...</p>
          </div>
        ) : error ? (
          <div className="p-8 text-center">
            <XCircle className="h-8 w-8 text-red-400 mx-auto mb-2" />
            <p className="text-sm text-red-600">{error}</p>
          </div>
        ) : filteredSessions.length === 0 ? (
          <div className="p-8 text-center">
            <History className="h-8 w-8 text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-500">
              {searchQuery ? '沒有符合的結果' : '尚無研究歷史'}
            </p>
          </div>
        ) : (
          filteredSessions.map((session) => (
            <div
              key={session.session_id}
              className="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
              onClick={() => onSelectSession?.(session.session_id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    {getStatusBadge(session.status)}
                    {session.is_bookmarked && (
                      <BookmarkCheck className="h-4 w-4 text-yellow-500" />
                    )}
                  </div>
                  <p className="text-sm font-medium text-gray-900 mb-1 truncate">
                    {session.query_text}
                  </p>
                  <div className="flex items-center space-x-3 text-xs text-gray-500">
                    <span className="flex items-center">
                      <Clock className="h-3 w-3 mr-1" />
                      {formatTimeAgo(session.created_at)}
                    </span>
                    {session.processing_time_seconds && (
                      <span>
                        耗時 {session.processing_time_seconds.toFixed(1)} 秒
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      {!loading && !error && total > limit && (
        <div className="p-4 border-t border-gray-200 flex items-center justify-between">
          <button
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
            className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            上一頁
          </button>
          <span className="text-sm text-gray-600">
            第 {page + 1} 頁，共 {Math.ceil(total / limit)} 頁
          </span>
          <button
            onClick={() => setPage(page + 1)}
            disabled={(page + 1) * limit >= total}
            className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            下一頁
          </button>
        </div>
      )}
    </div>
  )
}
