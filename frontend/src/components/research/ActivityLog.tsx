import { Info, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react'
import type { ActivityLogEntry } from '../../types/query'

interface ActivityLogProps {
  entries: ActivityLogEntry[]
}

function getLevelIcon(level: ActivityLogEntry['level']) {
  switch (level) {
    case 'success':
      return <CheckCircle2 className="h-4 w-4 text-success-600" />
    case 'warning':
      return <AlertTriangle className="h-4 w-4 text-warning-600" />
    case 'error':
      return <XCircle className="h-4 w-4 text-red-600" />
    default:
      return <Info className="h-4 w-4 text-navy-600" />
  }
}

function getLevelColor(level: ActivityLogEntry['level']) {
  switch (level) {
    case 'success':
      return 'text-success-800'
    case 'warning':
      return 'text-warning-800'
    case 'error':
      return 'text-red-800'
    default:
      return 'text-navy-800'
  }
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-TW', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

export function ActivityLog({ entries }: ActivityLogProps) {
  return (
    <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
      <h3 className="text-sm font-bold text-gray-900 mb-3 pb-2 border-b border-gray-200">活動日誌</h3>

      <div className="bg-gray-50 rounded-lg p-2 h-64 overflow-y-auto scrollbar-thin border border-gray-200">
        {entries.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-8">
            等待查詢開始...
          </p>
        ) : (
          <div className="space-y-1.5">
            {entries.map((entry) => (
              <div
                key={entry.id}
                className="flex items-start space-x-2 text-sm bg-white p-1.5 rounded border border-gray-200"
              >
                <span className="text-xs text-gray-600 font-mono whitespace-nowrap">
                  {formatTimestamp(entry.timestamp)}
                </span>
                <div className="flex-shrink-0 mt-0.5">
                  {getLevelIcon(entry.level)}
                </div>
                <p className={`flex-1 ${getLevelColor(entry.level)}`}>
                  {entry.message}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {entries.length > 0 && (
        <div className="mt-2 text-xs text-gray-600 text-right bg-gray-100 px-2 py-0.5 rounded">
          {entries.length} 條記錄
        </div>
      )}
    </div>
  )
}
