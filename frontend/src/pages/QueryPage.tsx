import { useState, useCallback, useEffect, useRef } from 'react'
import { Send, Loader2 } from 'lucide-react'
import { AgentStepper } from '../components/query/AgentStepper'
import { TodoPanel } from '../components/query/TodoPanel'
import { ActivityLog } from '../components/query/ActivityLog'
import { ResultsPanel } from '../components/query/ResultsPanel'
import type {
  StepUpdate,
  TodoItem,
  ActivityLogEntry,
  QueryResult,
  WSMessage,
} from '../types/query'

export function QueryPage() {
  const [queryText, setQueryText] = useState('')
  const [isQuerying, setIsQuerying] = useState(false)
  const [steps, setSteps] = useState<Map<string, StepUpdate>>(new Map())
  const [todos, setTodos] = useState<TodoItem[]>([])
  const [activityLog, setActivityLog] = useState<ActivityLogEntry[]>([])
  const [result, setResult] = useState<QueryResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected')

  const wsRef = useRef<WebSocket | null>(null)
  const logIdCounter = useRef(0)

  // Connect to WebSocket
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    setConnectionStatus('connecting')
    const ws = new WebSocket(`ws://${window.location.host}/ws/query`)

    ws.onopen = () => {
      console.log('WebSocket connected')
      setConnectionStatus('connected')
    }

    ws.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data)
        handleWSMessage(message)
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err)
      }
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setConnectionStatus('disconnected')
      wsRef.current = null
    }

    ws.onerror = (err) => {
      console.error('WebSocket error:', err)
      setConnectionStatus('disconnected')
    }

    wsRef.current = ws
  }, [])

  // Handle incoming WebSocket messages
  const handleWSMessage = useCallback((message: WSMessage) => {
    const { type, timestamp, payload } = message

    switch (type) {
      case 'query_started':
        setIsQuerying(true)
        setError(null)
        setResult(null)
        setSteps(new Map())
        setTodos([])
        break

      case 'step_update':
        const stepUpdate = payload as StepUpdate
        setSteps((prev) => {
          const newSteps = new Map(prev)
          newSteps.set(stepUpdate.step, stepUpdate)
          return newSteps
        })
        break

      case 'todo_update':
        const todoUpdate = payload as { todos: TodoItem[] }
        setTodos(todoUpdate.todos)
        break

      case 'todo_item_update':
        const todoItemUpdate = payload as TodoItem
        setTodos((prev) =>
          prev.map((todo) =>
            todo.id === todoItemUpdate.id
              ? { ...todo, ...todoItemUpdate }
              : todo
          )
        )
        break

      case 'activity_log':
        const logEntry = payload as { level: ActivityLogEntry['level']; message: string }
        setActivityLog((prev) => [
          ...prev,
          {
            id: `log-${logIdCounter.current++}`,
            timestamp,
            level: logEntry.level,
            message: logEntry.message,
          },
        ])
        break

      case 'query_complete':
        setResult(payload as QueryResult)
        setIsQuerying(false)
        break

      case 'query_failed':
        const errorPayload = payload as { error: string }
        setError(errorPayload.error)
        setIsQuerying(false)
        break

      case 'error':
        const errMsg = payload as { message: string }
        setError(errMsg.message)
        break

      default:
        console.log('Unknown message type:', type)
    }
  }, [])

  // Submit query
  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault()
      if (!queryText.trim() || isQuerying) return

      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        connectWebSocket()
        // Wait for connection then send
        setTimeout(() => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'query', text: queryText }))
          }
        }, 1000)
      } else {
        wsRef.current.send(JSON.stringify({ type: 'query', text: queryText }))
      }

      // Reset state
      setActivityLog([])
      setSteps(new Map())
      setTodos([])
      setResult(null)
      setError(null)
    },
    [queryText, isQuerying, connectWebSocket]
  )

  // Export results to JSON
  const handleExport = useCallback(() => {
    if (!result) return

    const exportData = {
      query: queryText,
      timestamp: new Date().toISOString(),
      result,
      activity_log: activityLog,
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `finagent-query-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }, [result, queryText, activityLog])

  // Connect WebSocket on mount
  useEffect(() => {
    connectWebSocket()
    return () => {
      wsRef.current?.close()
    }
  }, [connectWebSocket])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">法律研究查詢</h1>
        <p className="mt-1 text-sm text-gray-500">
          輸入您的法律研究問題，系統將分析相關裁罰案例與判決書
        </p>
      </div>

      {/* Query Input */}
      <div className="bg-white shadow rounded-lg p-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="query"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              查詢內容
            </label>
            <textarea
              id="query"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              placeholder="例如：玉山銀行洗錢防制裁罰案件"
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              disabled={isQuerying}
            />
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  connectionStatus === 'connected'
                    ? 'bg-green-500'
                    : connectionStatus === 'connecting'
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
                }`}
              />
              <span className="text-xs text-gray-500">
                {connectionStatus === 'connected'
                  ? 'WebSocket 已連線'
                  : connectionStatus === 'connecting'
                  ? '連線中...'
                  : '未連線'}
              </span>
            </div>
            <button
              type="submit"
              disabled={!queryText.trim() || isQuerying}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isQuerying ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  處理中...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  送出查詢
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Error display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Monitoring Panels */}
      {(isQuerying || result) && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <AgentStepper steps={steps} />
          <TodoPanel todos={todos} />
          <ActivityLog entries={activityLog} />
        </div>
      )}

      {/* Results */}
      <ResultsPanel result={result} onExport={handleExport} />
    </div>
  )
}
