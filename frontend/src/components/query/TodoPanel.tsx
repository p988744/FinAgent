import { CheckCircle2, Circle, Loader2, AlertCircle } from 'lucide-react'
import type { TodoItem } from '../../types/query'

interface TodoPanelProps {
  todos: TodoItem[]
}

function getStatusIcon(status: TodoItem['status']) {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className="h-4 w-4 text-green-500" />
    case 'in_progress':
      return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
    case 'failed':
      return <AlertCircle className="h-4 w-4 text-red-500" />
    default:
      return <Circle className="h-4 w-4 text-gray-300" />
  }
}

function getStatusBadge(status: TodoItem['status']) {
  const baseClass = 'text-xs px-2 py-0.5 rounded-full'
  switch (status) {
    case 'completed':
      return `${baseClass} bg-green-100 text-green-700`
    case 'in_progress':
      return `${baseClass} bg-blue-100 text-blue-700`
    case 'failed':
      return `${baseClass} bg-red-100 text-red-700`
    default:
      return `${baseClass} bg-gray-100 text-gray-600`
  }
}

function getStatusText(status: TodoItem['status']) {
  switch (status) {
    case 'completed':
      return '完成'
    case 'in_progress':
      return '進行中'
    case 'failed':
      return '失敗'
    default:
      return '待處理'
  }
}

export function TodoPanel({ todos }: TodoPanelProps) {
  const completedCount = todos.filter((t) => t.status === 'completed').length
  const totalCount = todos.length
  const progressPercentage =
    totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">任務清單</h3>
        <span className="text-sm text-gray-500">
          {completedCount}/{totalCount}
        </span>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
        <div
          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${progressPercentage}%` }}
        />
      </div>

      {/* Todo list */}
      <div className="space-y-3 max-h-60 overflow-y-auto">
        {todos.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-4">
            尚無任務
          </p>
        ) : (
          todos.map((todo) => (
            <div
              key={todo.id}
              className="flex items-start space-x-3 p-2 rounded hover:bg-gray-50"
            >
              <div className="flex-shrink-0 mt-0.5">
                {getStatusIcon(todo.status)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-900">{todo.description}</p>
                {todo.message && (
                  <p className="text-xs text-gray-500 mt-1">{todo.message}</p>
                )}
                {todo.error && (
                  <p className="text-xs text-red-600 mt-1">{todo.error}</p>
                )}
                {todo.progress !== undefined && todo.status === 'in_progress' && (
                  <div className="w-full bg-gray-200 rounded-full h-1 mt-2">
                    <div
                      className="bg-blue-600 h-1 rounded-full"
                      style={{ width: `${todo.progress}%` }}
                    />
                  </div>
                )}
              </div>
              <div className="flex-shrink-0">
                <span className={getStatusBadge(todo.status)}>
                  {getStatusText(todo.status)}
                </span>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Summary */}
      {totalCount > 0 && (
        <div className="mt-4 pt-3 border-t border-gray-200">
          <p className="text-sm text-gray-600">
            進度: <span className="font-medium">{progressPercentage}%</span>
          </p>
        </div>
      )}
    </div>
  )
}
