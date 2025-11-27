import { useState, useCallback, useEffect, useRef } from 'react'
import { Loader2, Sparkles, ArrowRight, Search } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import clsx from 'clsx'
import { AgentStepper } from '../components/research/AgentStepper'
import { ActivityLog } from '../components/research/ActivityLog'
import { ResultsPanel } from '../components/research/ResultsPanel'
import { PlanPanel } from '../components/research/PlanPanel'
import { DynamicPlanPanel } from '../components/research/DynamicPlanPanel'
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
  const [usePlanExecute, setUsePlanExecute] = useState(false)
  const [useWikiSearch, setUseWikiSearch] = useState(false)
  const [steps, setSteps] = useState<Map<string, StepUpdate>>(new Map())
  const [todos, setTodos] = useState<TodoItem[]>([])
  const [activityLog, setActivityLog] = useState<ActivityLogEntry[]>([])
  const [result, setResult] = useState<QueryResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [plan, setPlan] = useState<ResearchPlan | null>(null)
  const [dynamicPlan, setDynamicPlan] = useState<DynamicPlanAnalysis | null>(null)
  const [toolExecutions, setToolExecutions] = useState<Map<string, ToolExecutionStatus>>(new Map())
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected')
  const [hasSearched, setHasSearched] = useState(false)

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
        // Note: We don't clear state here because handleSubmit already does it.
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

      setHasSearched(true)
      setIsQuerying(true)
      setActivityLog([])
      setSteps(new Map())
      setTodos([])
      setResult(null)
      setError(null)
      setPlan(null)
      setDynamicPlan(null)
      setToolExecutions(new Map())

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
        setTimeout(() => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
              type: 'query',
              text: queryText,
              use_plan_execute: usePlanExecute,
              use_wiki_search: useWikiSearch
            }))
          } else {
            setError('WebSocket 連線失敗，請重試')
            setIsQuerying(false)
          }
        }, 1000)
      } else {
        wsRef.current.send(JSON.stringify({
          type: 'query',
          text: queryText,
          use_plan_execute: usePlanExecute,
          use_wiki_search: useWikiSearch
        }))
      }
    },
    [queryText, isQuerying, connectWebSocket, usePlanExecute, useWikiSearch]
  )

  const handleExport = useCallback(() => {
    if (!result) return
    const exportData = {
      query: queryText,
      timestamp: new Date().toISOString(),
      result,
      activity_log: activityLog,
    }
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `finagent-query-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }, [result, queryText, activityLog])

  useEffect(() => {
    connectWebSocket()
    return () => {
      wsRef.current?.close()
    }
  }, [connectWebSocket])

  return (
    <div className="relative min-h-[calc(100vh-4rem)]">
      {/* Hero / Search Section */}
      <motion.div
        layout
        initial={false}
        animate={{
          height: hasSearched ? 'auto' : '80vh',
          marginBottom: hasSearched ? '2rem' : '0',
        }}
        className={clsx(
          'flex flex-col items-center transition-all duration-500',
          hasSearched ? 'justify-start pt-0' : 'justify-center'
        )}
      >
        <motion.div
          layout
          className={clsx(
            'w-full max-w-3xl text-center space-y-6',
            hasSearched ? 'scale-90 origin-top' : ''
          )}
        >
          {!hasSearched && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-4"
            >
              <div className="inline-flex items-center px-3 py-1 rounded-full bg-primary-500/10 border border-primary-500/20 text-primary-400 text-sm font-medium">
                <Sparkles className="w-4 h-4 mr-2" />
                FinAgent V2.0
              </div>
              <h1 className="text-5xl font-bold tracking-tight text-white">
                Intelligent Legal Research
              </h1>
              <p className="text-xl text-slate-400 max-w-2xl mx-auto">
                Advanced AI agent for analyzing Taiwan's financial regulations and enforcement actions.
              </p>
            </motion.div>
          )}

          <form onSubmit={handleSubmit} className="relative w-full max-w-2xl mx-auto">
            <div className="relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-primary-600 to-accent-600 rounded-xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200" />
              <div className="relative flex items-center bg-slate-900 rounded-xl border border-slate-700 shadow-2xl overflow-hidden">
                <div className="pl-4 text-slate-400">
                  <Search className="w-6 h-6" />
                </div>
                <input
                  type="text"
                  value={queryText}
                  onChange={(e) => setQueryText(e.target.value)}
                  disabled={isQuerying}
                  placeholder="Describe your legal research query..."
                  className="w-full px-4 py-4 bg-transparent text-lg text-white placeholder-slate-500 focus:outline-none"
                />
                <button
                  type="submit"
                  disabled={!queryText.trim() || isQuerying}
                  className="mr-2 p-2 rounded-lg bg-primary-600 text-white hover:bg-primary-500 disabled:opacity-50 disabled:hover:bg-primary-600 transition-colors"
                >
                  {isQuerying ? (
                    <Loader2 className="w-6 h-6 animate-spin" />
                  ) : (
                    <ArrowRight className="w-6 h-6" />
                  )}
                </button>
              </div>
            </div>

            {/* Options */}
            <div className="flex items-center justify-center space-x-6 mt-4">
              <label className="flex items-center space-x-2 cursor-pointer group">
                <div className={clsx(
                  "w-5 h-5 rounded border flex items-center justify-center transition-colors",
                  usePlanExecute ? "bg-primary-600 border-primary-600" : "border-slate-600 group-hover:border-slate-500"
                )}>
                  <input
                    type="checkbox"
                    checked={usePlanExecute}
                    onChange={(e) => {
                      setUsePlanExecute(e.target.checked)
                      if (e.target.checked) setUseWikiSearch(false)
                    }}
                    className="hidden"
                  />
                  {usePlanExecute && <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} className="w-2.5 h-2.5 bg-white rounded-sm" />}
                </div>
                <span className={clsx("text-sm transition-colors", usePlanExecute ? "text-primary-400" : "text-slate-400 group-hover:text-slate-300")}>
                  Plan-and-Execute
                </span>
              </label>

              <label className="flex items-center space-x-2 cursor-pointer group">
                <div className={clsx(
                  "w-5 h-5 rounded border flex items-center justify-center transition-colors",
                  useWikiSearch ? "bg-accent-600 border-accent-600" : "border-slate-600 group-hover:border-slate-500"
                )}>
                  <input
                    type="checkbox"
                    checked={useWikiSearch}
                    onChange={(e) => {
                      setUseWikiSearch(e.target.checked)
                      if (e.target.checked) setUsePlanExecute(false)
                    }}
                    className="hidden"
                  />
                  {useWikiSearch && <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} className="w-2.5 h-2.5 bg-white rounded-sm" />}
                </div>
                <span className={clsx("text-sm transition-colors", useWikiSearch ? "text-accent-400" : "text-slate-400 group-hover:text-slate-300")}>
                  Wiki Search
                </span>
              </label>
            </div>
          </form>
        </motion.div>
      </motion.div>

      {/* Dashboard Content */}
      <AnimatePresence>
        {hasSearched && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="grid grid-cols-1 lg:grid-cols-12 gap-6 pb-12"
          >
            {/* Left Column: Live Agent Feed */}
            <div className="lg:col-span-4 space-y-6">
              <div className="glass-card rounded-xl p-4">
                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Live Activity</h3>
                <div className="space-y-4">
                  <AgentStepper steps={steps} />
                  <div className="h-64 overflow-y-auto custom-scrollbar">
                    <ActivityLog entries={activityLog} />
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Workspace */}
            <div className="lg:col-span-8 space-y-6">
              {error && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-red-400"
                >
                  {error}
                </motion.div>
              )}

              {/* Plan Panel */}
              {(isQuerying || plan) && (
                <motion.div layout>
                  <PlanPanel plan={plan} />
                </motion.div>
              )}

              {/* Dynamic Plan */}
              {(isQuerying || dynamicPlan) && (
                <motion.div layout>
                  <DynamicPlanPanel analysis={dynamicPlan} toolExecutions={toolExecutions} />
                </motion.div>
              )}

              {/* Results */}
              {result && (
                <motion.div layout>
                  <ResultsPanel result={result} onExport={handleExport} />
                </motion.div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
