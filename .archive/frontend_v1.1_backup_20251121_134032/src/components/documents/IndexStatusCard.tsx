import { Database, RefreshCw } from 'lucide-react'
import type { IndexStatus } from '../../types/documents'

interface IndexStatusCardProps {
  status: IndexStatus | null
  onReindexAll: () => Promise<void>
  isReindexing: boolean
}

export function IndexStatusCard({
  status,
  onReindexAll,
  isReindexing,
}: IndexStatusCardProps) {
  if (!status) {
    return (
      <div className="bg-white shadow rounded-lg p-4 text-center text-gray-500">
        載入索引狀態中...
      </div>
    )
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '從未'
    return new Date(dateStr).toLocaleString('zh-TW')
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Database className="h-5 w-5 text-gray-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">索引狀態</h3>
          </div>

          <button
            onClick={onReindexAll}
            disabled={isReindexing || status.total_documents === 0}
            className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50"
          >
            {isReindexing ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                重新索引中...
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4 mr-2" />
                全部重新索引
              </>
            )}
          </button>
        </div>
      </div>

      <div className="p-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-2xl font-bold text-gray-900">
              {status.total_documents}
            </div>
            <div className="text-sm text-gray-600">總文件數</div>
          </div>

          <div className="bg-green-50 rounded-lg p-3">
            <div className="text-2xl font-bold text-green-700">
              {status.indexed_documents}
            </div>
            <div className="text-sm text-gray-600">已索引</div>
          </div>

          <div className="bg-yellow-50 rounded-lg p-3">
            <div className="text-2xl font-bold text-yellow-700">
              {status.pending_documents}
            </div>
            <div className="text-sm text-gray-600">待索引</div>
          </div>

          <div className="bg-blue-50 rounded-lg p-3">
            <div className="text-2xl font-bold text-blue-700">
              {status.total_chunks}
            </div>
            <div className="text-sm text-gray-600">總區塊數</div>
          </div>
        </div>

        <div className="mt-4 text-sm text-gray-500">
          最後索引時間: {formatDate(status.last_indexed_at)}
        </div>
      </div>
    </div>
  )
}
