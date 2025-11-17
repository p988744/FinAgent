import { useEffect, useRef } from 'react'
import { Info, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react'
import type { ActivityLogEntry } from '../../types/query'

interface ActivityLogProps {
  entries: ActivityLogEntry[]
}

function getLevelIcon(level: ActivityLogEntry['level']) {
  switch (level) {
    case 'success':
      return <CheckCircle2 className="h-4 w-4 text-green-500" />
    case 'warning':
      return <AlertTriangle className="h-4 w-4 text-yellow-500" />
    case 'error':
      return <XCircle className="h-4 w-4 text-red-500" />
    default:
      return <Info className="h-4 w-4 text-blue-500" />
  }
}

function getLevelColor(level: ActivityLogEntry['level']) {
  switch (level) {
    case 'success':
      return 'text-green-700'
    case 'warning':
      return 'text-yellow-700'
    case 'error':
      return 'text-red-700'
    default:
      return 'text-blue-700'
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
  const logEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new entries are added
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [entries])

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">活動日誌</h3>

      <div className="bg-gray-50 rounded-lg p-3 h-64 overflow-y-auto scrollbar-thin">
        {entries.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-8">
            等待查詢開始...
          </p>
        ) : (
          <div className="space-y-2">
            {entries.map((entry) => (
              <div
                key={entry.id}
                className="flex items-start space-x-2 text-sm"
              >
                <span className="text-xs text-gray-400 font-mono whitespace-nowrap">
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
            <div ref={logEndRef} />
          </div>
        )}
      </div>

      {entries.length > 0 && (
        <div className="mt-2 text-xs text-gray-500 text-right">
          {entries.length} 條記錄
        </div>
      )}
    </div>
  )
}
