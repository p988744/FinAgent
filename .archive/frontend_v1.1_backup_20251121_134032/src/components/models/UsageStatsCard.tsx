import { BarChart3, DollarSign, MessageSquare, Clock } from 'lucide-react'
import type { UsageStats } from '../../types/models'

interface UsageStatsCardProps {
  stats: UsageStats | null
  isLoading: boolean
}

export function UsageStatsCard({ stats, isLoading }: UsageStatsCardProps) {
  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg p-4">
        <div className="text-center text-gray-500">載入使用統計中...</div>
      </div>
    )
  }

  if (!stats) {
    return null
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">使用統計</h3>
      </div>

      <div className="p-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="flex items-center">
              <BarChart3 className="h-5 w-5 text-blue-600 mr-2" />
              <span className="text-sm font-medium text-gray-700">
                總 Tokens
              </span>
            </div>
            <p className="mt-2 text-2xl font-bold text-gray-900">
              {stats.total_tokens.toLocaleString()}
            </p>
          </div>

          <div className="bg-green-50 rounded-lg p-4">
            <div className="flex items-center">
              <DollarSign className="h-5 w-5 text-green-600 mr-2" />
              <span className="text-sm font-medium text-gray-700">總成本</span>
            </div>
            <p className="mt-2 text-2xl font-bold text-gray-900">
              ${stats.total_cost.toFixed(4)}
            </p>
          </div>

          <div className="bg-purple-50 rounded-lg p-4">
            <div className="flex items-center">
              <MessageSquare className="h-5 w-5 text-purple-600 mr-2" />
              <span className="text-sm font-medium text-gray-700">
                查詢次數
              </span>
            </div>
            <p className="mt-2 text-2xl font-bold text-gray-900">
              {stats.queries_count}
            </p>
          </div>

          <div className="bg-orange-50 rounded-lg p-4">
            <div className="flex items-center">
              <Clock className="h-5 w-5 text-orange-600 mr-2" />
              <span className="text-sm font-medium text-gray-700">
                Session 開始
              </span>
            </div>
            <p className="mt-2 text-sm font-medium text-gray-900">
              {new Date(stats.session_start).toLocaleString('zh-TW')}
            </p>
          </div>
        </div>

        <div className="mt-4 border-t border-gray-200 pt-4">
          <div className="text-sm text-gray-600">
            <p>
              <span className="font-medium">目前 LLM:</span>{' '}
              {stats.current_llm_model}
            </p>
            <p className="mt-1">
              <span className="font-medium">目前嵌入模型:</span>{' '}
              {stats.current_embedding_model}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
