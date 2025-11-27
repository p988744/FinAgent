import { CheckCircle2, Circle, Loader2, AlertCircle } from 'lucide-react'
import type { TodoItem } from '../../types/research'

interface TodoPanelProps {
  todos: TodoItem[]
}

function getStatusIcon(status: TodoItem['status']) {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className="h-4 w-4 text-success-600" />
    case 'in_progress':
      return <Loader2 className="h-4 w-4 text-navy-600 animate-spin" />
    case 'failed':
      return <AlertCircle className="h-4 w-4 text-red-600" />
    default:
      return <Circle className="h-4 w-4 text-gray-400" />
  }
}

function getStatusBadge(status: TodoItem['status']) {
  const baseClass = 'text-xs px-2 py-0.5 rounded font-semibold border'
  switch (status) {
    case 'completed':
      return `${baseClass} bg-success-100 text-success-800 border-success-200`
    case 'in_progress':
      return `${baseClass} bg-navy-100 text-navy-800 border-navy-200`
    case 'failed':
      return `${baseClass} bg-red-100 text-red-800 border-red-200`
    default:
      return `${baseClass} bg-gray-100 text-gray-700 border-gray-200`
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
    <div className="bg-white rounded-lg shadow-md border border-gray-200 p-5">
      <div className="flex items-center justify-between mb-4 pb-2 border-b border-gray-200">
        <h3 className="text-base font-bold text-primary-900">任務清單</h3>
        <span className="text-xs font-semibold text-gray-600 bg-gray-100 px-2 py-1 rounded">
          {completedCount}/{totalCount}
        </span>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-gray-300 rounded-full h-2.5 mb-4">
        <div
          className="bg-navy-600 h-2.5 rounded-full transition-all duration-300"
          style={{ width: `${progressPercentage}%` }}
        />
      </div>

      {/* Todo list */}
      <div className="space-y-3 max-h-60 overflow-y-auto">
        {todos.length === 0 ? (
          <p className="text-sm font-medium text-gray-500 text-center py-4">
            尚無任務
          </p>
        ) : (
          todos.map((todo) => (
            <div
              key={todo.id}
              className="flex items-start space-x-3 p-2.5 rounded hover:bg-gray-50 border border-gray-200 bg-white transition-colors"
            >
              <div className="flex-shrink-0 mt-0.5">
                {getStatusIcon(todo.status)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-primary-900">{todo.description}</p>
                {todo.message && (
                  <p className="text-xs font-medium text-gray-600 mt-1">{todo.message}</p>
                )}
                {todo.error && (
                  <p className="text-xs font-medium text-red-700 mt-1">{todo.error}</p>
                )}
                {todo.progress !== undefined && todo.status === 'in_progress' && (
                  <div className="w-full bg-gray-300 rounded-full h-1.5 mt-2">
                    <div
                      className="bg-navy-600 h-1.5 rounded-full transition-all"
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
          <p className="text-sm font-bold text-gray-700">
            進度: <span className="text-navy-700">{progressPercentage}%</span>
          </p>
        </div>
      )}
    </div>
  )
}
