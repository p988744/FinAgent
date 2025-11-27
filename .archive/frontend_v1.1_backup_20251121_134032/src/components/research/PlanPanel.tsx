import { useState } from 'react'
import {
  Search,
  Clock,
  Tag,
  Building,
  Calendar,
  Layers,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  XCircle,
  Loader2,
  Database,
  Globe,
  Cpu
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import clsx from 'clsx'
import type { ResearchPlan } from '../../types/research'

interface PlanPanelProps {
  plan: ResearchPlan | null
}

function getComplexityColor(complexity: string) {
  switch (complexity) {
    case 'simple':
      return 'text-success-400 bg-success-500/10 border-success-500/20'
    case 'medium':
      return 'text-warning-400 bg-warning-500/10 border-warning-500/20'
    case 'complex':
      return 'text-red-400 bg-red-500/10 border-red-500/20'
    default:
      return 'text-slate-400 bg-slate-500/10 border-slate-500/20'
  }
}

function getSearchMethodIcon(method: string) {
  switch (method) {
    case 'vector_search':
      return <Database className="w-3 h-3" />
    case 'hard_search':
      return <Globe className="w-3 h-3" />
    case 'hybrid':
      return <Cpu className="w-3 h-3" />
    default:
      return <Search className="w-3 h-3" />
  }
}

function getTaskStatusIcon(status: string) {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className="h-5 w-5 text-success-500" />
    case 'in_progress':
      return <Loader2 className="h-5 w-5 text-primary-500 animate-spin" />
    case 'failed':
      return <XCircle className="h-5 w-5 text-red-500" />
    case 'pending':
    default:
      return <div className="h-2 w-2 rounded-full bg-slate-600" />
  }
}

export function PlanPanel({ plan }: PlanPanelProps) {
  const [expandedTasks, setExpandedTasks] = useState<Set<number>>(new Set())

  if (!plan) return null

  const { analysis, tasks, estimated_total_time } = plan

  const toggleTask = (taskId: number) => {
    setExpandedTasks((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(taskId)) {
        newSet.delete(taskId)
      } else {
        newSet.add(taskId)
      }
      return newSet
    })
  }

  return (
    <div className="glass-card rounded-xl overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-slate-700/50 bg-slate-800/30 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-primary-500/10 rounded-lg">
            <Layers className="h-5 w-5 text-primary-400" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Research Strategy</h3>
            <div className="flex items-center space-x-2 mt-0.5">
              <span className="text-xs text-slate-400">
                {tasks.length} Steps
              </span>
              <span className="text-slate-600">•</span>
              <span className="text-xs text-slate-400">
                ~{estimated_total_time}s estimated
              </span>
            </div>
          </div>
        </div>
        <div className={clsx(
          'px-2.5 py-1 rounded-full text-xs font-medium border',
          getComplexityColor(analysis.complexity)
        )}>
          {analysis.complexity.toUpperCase()}
        </div>
      </div>

      {/* Analysis Tags */}
      <div className="p-4 border-b border-slate-700/50 bg-slate-900/20 space-y-3">
        <div className="flex flex-wrap gap-2">
          {analysis.keywords.map((kw, i) => (
            <span key={i} className="inline-flex items-center px-2 py-1 rounded-md bg-slate-800 border border-slate-700 text-xs text-slate-300">
              <Tag className="w-3 h-3 mr-1.5 text-slate-500" />
              {kw}
            </span>
          ))}
          {analysis.must_have_keywords.map((kw, i) => (
            <span key={`must-${i}`} className="inline-flex items-center px-2 py-1 rounded-md bg-red-500/10 border border-red-500/20 text-xs text-red-400">
              <Tag className="w-3 h-3 mr-1.5" />
              {kw}
            </span>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-4 text-xs text-slate-400">
          <div className="flex items-center space-x-2">
            <Search className="w-3.5 h-3.5" />
            <span>Type: <span className="text-slate-300">{analysis.query_type}</span></span>
          </div>
          {analysis.jurisdiction && (
            <div className="flex items-center space-x-2">
              <Building className="w-3.5 h-3.5" />
              <span>Jurisdiction: <span className="text-slate-300">{analysis.jurisdiction}</span></span>
            </div>
          )}
          {analysis.time_period && (
            <div className="flex items-center space-x-2">
              <Calendar className="w-3.5 h-3.5" />
              <span>Period: <span className="text-slate-300">{analysis.time_period}</span></span>
            </div>
          )}
        </div>
      </div>

      {/* Timeline */}
      <div className="p-4 relative">
        {/* Vertical Line */}
        <div className="absolute left-8 top-6 bottom-6 w-px bg-slate-800" />

        <div className="space-y-6">
          {tasks.map((task, index) => {
            const isExpanded = expandedTasks.has(task.id)
            const hasToolUsage = !!task.tool_usage
            const isLast = index === tasks.length - 1

            return (
              <motion.div
                key={task.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="relative pl-12"
              >
                {/* Status Node */}
                <div className={clsx(
                  "absolute left-2 top-0 w-5 h-5 -ml-2.5 flex items-center justify-center bg-slate-950 z-10",
                  task.status === 'pending' && "pl-1.5 pt-1.5" // Center the dot
                )}>
                  {getTaskStatusIcon(task.status)}
                </div>

                {/* Content */}
                <div className="space-y-2">
                  <div
                    className={clsx(
                      "flex items-start justify-between group",
                      hasToolUsage && "cursor-pointer"
                    )}
                    onClick={() => hasToolUsage && toggleTask(task.id)}
                  >
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className={clsx(
                          "text-sm font-medium transition-colors",
                          task.status === 'completed' ? "text-slate-300" :
                            task.status === 'in_progress' ? "text-primary-400" : "text-slate-500"
                        )}>
                          {task.task}
                        </span>
                        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-400 border border-slate-700">
                          {getSearchMethodIcon(task.search_method)}
                          <span className="ml-1 uppercase">{task.search_method.replace('_', ' ')}</span>
                        </span>
                      </div>
                      {task.estimated_time && (
                        <div className="flex items-center text-xs text-slate-500">
                          <Clock className="w-3 h-3 mr-1" />
                          ~{task.estimated_time}s
                        </div>
                      )}
                    </div>

                    {hasToolUsage && (
                      <div className="p-1 rounded hover:bg-slate-800 text-slate-500 transition-colors">
                        {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                      </div>
                    )}
                  </div>

                  {/* Expanded Details */}
                  <AnimatePresence>
                    {isExpanded && task.tool_usage && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                      >
                        <div className="mt-2 p-3 bg-slate-900/50 rounded-lg border border-slate-800 text-xs space-y-3">
                          {/* Tool Header */}
                          <div className="flex items-center justify-between">
                            <span className="font-mono text-primary-400">
                              {task.tool_usage.tool_name}()
                            </span>
                            {task.tool_usage.execution_time_ms && (
                              <span className="text-slate-500">
                                {task.tool_usage.execution_time_ms}ms
                              </span>
                            )}
                          </div>

                          {/* Params */}
                          <div className="space-y-1">
                            <div className="text-slate-500 font-medium">Parameters</div>
                            <pre className="font-mono text-slate-400 bg-slate-950 p-2 rounded overflow-x-auto">
                              {JSON.stringify(task.tool_usage.request_params, null, 2)}
                            </pre>
                          </div>

                          {/* Results */}
                          {task.tool_usage.result_count !== undefined && (
                            <div className="space-y-1">
                              <div className="flex items-center justify-between text-slate-500 font-medium">
                                <span>Results ({task.tool_usage.result_count})</span>
                              </div>
                              {task.tool_usage.sample_results?.slice(0, 2).map((res, idx) => (
                                <div key={idx} className="p-2 bg-slate-800/50 rounded border border-slate-700/50">
                                  <div className="flex justify-between mb-1">
                                    <span className="text-slate-300 truncate max-w-[200px]">{res.source}</span>
                                    {res.relevance && (
                                      <span className="text-primary-400">{(res.relevance * 100).toFixed(0)}%</span>
                                    )}
                                  </div>
                                  <p className="text-slate-500 line-clamp-2">{res.snippet}</p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </motion.div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
