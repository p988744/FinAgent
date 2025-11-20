import { useState, useCallback, useEffect, useRef } from 'react'
import { Send, Loader2 } from 'lucide-react'
import { AgentStepper } from '../components/research/AgentStepper'
import { TodoPanel } from '../components/research/TodoPanel'
import { ActivityLog } from '../components/research/ActivityLog'
import { ResultsPanel } from '../components/research/ResultsPanel'
import { PlanPanel } from '../components/research/PlanPanel'
import { DynamicPlanPanel } from '../components/research/DynamicPlanPanel'
import { ResearchHistory } from '../components/research/ResearchHistory'
import type {
  StepUpdate,
  TodoItem,
  ActivityLogEntry,
  QueryResult,
  WSMessage,
  ResearchPlan,
  DynamicPlanAnalysis,
  ToolExecutionStatus,
} from '../types/research'

export function ResearchPage() {
  const [queryText, setQueryText] = useState('')
  const [isQuerying, setIsQuerying] = useState(false)
  const [steps, setSteps] = useState<Map<string, StepUpdate>>(new Map())
  const [todos, setTodos] = useState<TodoItem[]>([])
  const [activityLog, setActivityLog] = useState<ActivityLogEntry[]>([])
  const [result, setResult] = useState<QueryResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [plan, setPlan] = useState<ResearchPlan | null>(null)
  const [dynamicPlan, setDynamicPlan] = useState<DynamicPlanAnalysis | null>(null)
  const [toolExecutions, setToolExecutions] = useState<Map<string, ToolExecutionStatus>>(new Map())
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
        setPlan(null)
        setDynamicPlan(null)
        setToolExecutions(new Map())
        break

      case 'plan_created':
        const planData = payload as ResearchPlan
        setPlan(planData)
        break

      case 'task_tool_usage':
        const taskToolUsage = payload as { task_id: number; tool_usage: any }
        setPlan((prevPlan) => {
          if (!prevPlan) return prevPlan
          return {
            ...prevPlan,
            tasks: prevPlan.tasks.map((task) =>
              task.id === taskToolUsage.task_id
                ? { ...task, tool_usage: taskToolUsage.tool_usage }
                : task
            ),
          }
        })
        break

      case 'dynamic_plan_analysis':
        const dynamicPlanData = payload as DynamicPlanAnalysis
        setDynamicPlan(dynamicPlanData)
        // Initialize tool execution statuses
        setToolExecutions(new Map())
        break

      case 'tool_execution_update':
        const toolUpdate = payload as ToolExecutionStatus
        setToolExecutions((prev) => {
          const newExecutions = new Map(prev)
          newExecutions.set(toolUpdate.tool_name, toolUpdate)
          return newExecutions
        })
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

      // Show monitoring panels immediately
      setIsQuerying(true)
      setActivityLog([])
      setSteps(new Map())
      setTodos([])
      setResult(null)
      setError(null)
      setPlan(null)
      setDynamicPlan(null)
      setToolExecutions(new Map())

      // Add initial activity log entry
      setActivityLog([
        {
          id: `log-${logIdCounter.current++}`,
          timestamp: new Date().toISOString(),
          level: 'info',
          message: `開始處理查詢: ${queryText.substring(0, 50)}${queryText.length > 50 ? '...' : ''}`,
        },
      ])

      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        connectWebSocket()
        // Wait for connection then send
        setTimeout(() => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'query', text: queryText }))
          } else {
            setError('WebSocket 連線失敗，請重試')
            setIsQuerying(false)
          }
        }, 1000)
      } else {
        wsRef.current.send(JSON.stringify({ type: 'query', text: queryText }))
      }
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

  // Load session from history
  const handleSelectSession = useCallback(async (sessionId: string) => {
    try {
      // Fetch session status
      const response = await fetch(`/api/v1/research/status/${sessionId}`)
      if (!response.ok) {
        throw new Error('無法載入研究記錄')
      }

      const sessionData = await response.json()

      // Restore session state
      setQueryText(sessionData.query_text)
      setIsQuerying(sessionData.status === 'in_progress')

      if (sessionData.agent_steps) {
        const stepsMap = new Map()
        sessionData.agent_steps.forEach((step: any) => {
          stepsMap.set(step.step, step)
        })
        setSteps(stepsMap)
      }

      if (sessionData.todos) {
        setTodos(sessionData.todos)
      }

      if (sessionData.activity_log) {
        setActivityLog(sessionData.activity_log)
      }

      if (sessionData.research_plan) {
        setPlan(sessionData.research_plan)
      }

      if (sessionData.dynamic_plan) {
        setDynamicPlan(sessionData.dynamic_plan)
      }

      if (sessionData.tool_executions) {
        const toolMap = new Map()
        Object.entries(sessionData.tool_executions).forEach(([key, value]) => {
          toolMap.set(key, value as any)
        })
        setToolExecutions(toolMap)
      }

      if (sessionData.result) {
        setResult(sessionData.result)
      }

      if (sessionData.error_message) {
        setError(sessionData.error_message)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '載入研究記錄失敗')
    }
  }, [])

  // Connect WebSocket on mount
  useEffect(() => {
    connectWebSocket()
    return () => {
      wsRef.current?.close()
    }
  }, [connectWebSocket])

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
        <h1 className="text-xl font-bold text-gray-900">金融法律研究系統</h1>
        <p className="mt-1 text-xs text-gray-600">
          專業的法律研究工具，提供準確的裁罰案例與判決書分析
        </p>
      </div>

      {/* Query Input */}
      <div className="bg-white shadow rounded-lg p-4 border border-gray-200">
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label
              htmlFor="query"
              className="block text-sm font-semibold text-gray-900 mb-1.5"
            >
              查詢內容
            </label>
            <textarea
              id="query"
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-navy-500 focus:border-navy-500 bg-white text-gray-900 placeholder-gray-500"
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
              <span className="text-xs text-gray-600">
                {connectionStatus === 'connected'
                  ? '已連線'
                  : connectionStatus === 'connecting'
                  ? '連線中...'
                  : '未連線'}
              </span>
            </div>
            <button
              type="submit"
              disabled={!queryText.trim() || isQuerying}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-semibold rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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
        <div className="bg-red-50 border border-red-300 rounded-md p-3">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Monitoring Panels */}
      {(isQuerying || result) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <AgentStepper steps={steps} />
          <ActivityLog entries={activityLog} />
        </div>
      )}

      {/* Research Plan Panel */}
      {(isQuerying || plan) && <PlanPanel plan={plan} />}

      {/* Dynamic Plan Analysis Panel */}
      {(isQuerying || dynamicPlan) && <DynamicPlanPanel analysis={dynamicPlan} toolExecutions={toolExecutions} />}

      {/* Results - Only show after query completes */}
      {result && <ResultsPanel result={result} onExport={handleExport} />}

      {/* Research History */}
      <ResearchHistory onSelectSession={handleSelectSession} />
    </div>
  )
}
