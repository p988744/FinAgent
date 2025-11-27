/**
 * ThinkingProcess - Shows the AI's thinking process with animated steps
 */

import { useState } from 'react';
import type { ThinkingState, ThinkingStep, GraphState, StepHistoryEntry } from '../../types';

interface ThinkingProcessProps {
  thinking: ThinkingState;
  defaultExpanded?: boolean;
}

export function ThinkingProcess({ thinking, defaultExpanded = true }: ThinkingProcessProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const getStepIcon = (status: ThinkingStep['status']) => {
    switch (status) {
      case 'active':
        return (
          <div className="w-5 h-5 rounded-full bg-brass-500/20 flex items-center justify-center">
            <div className="w-2 h-2 rounded-full bg-brass-400 animate-pulse-soft" />
          </div>
        );
      case 'complete':
        return (
          <div className="w-5 h-5 rounded-full bg-jade-500/20 flex items-center justify-center">
            <svg className="w-3 h-3 text-jade-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        );
      case 'error':
        return (
          <div className="w-5 h-5 rounded-full bg-vermilion-500/20 flex items-center justify-center">
            <svg className="w-3 h-3 text-vermilion-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
        );
      default:
        return (
          <div className="w-5 h-5 rounded-full bg-noir-700/50 flex items-center justify-center">
            <div className="w-2 h-2 rounded-full bg-noir-500" />
          </div>
        );
    }
  };

  const completedSteps = thinking.steps.filter(s => s.status === 'complete').length;
  const totalSteps = thinking.steps.length;
  const progress = totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0;

  return (
    <div className="thinking-container mb-4">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="thinking-header w-full text-left hover:bg-noir-800/40 transition-colors"
      >
        <div className="thinking-indicator">
          {thinking.isThinking ? (
            <div className="thinking-dots">
              <span className="thinking-dot" />
              <span className="thinking-dot" />
              <span className="thinking-dot" />
            </div>
          ) : (
            <svg className="w-4 h-4 text-jade-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )}
          <span className="text-xs font-medium text-noir-300">
            {thinking.isThinking ? '正在思考' : '思考完成'}
          </span>
        </div>

        {/* Progress indicator */}
        <div className="flex items-center gap-3 ml-auto">
          <span className="text-2xs text-noir-500">
            {completedSteps}/{totalSteps}
          </span>
          <div className="w-16 h-1 bg-noir-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-brass-600 to-brass-400 transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          <svg
            className={`w-4 h-4 text-noir-500 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {/* Steps List */}
      {isExpanded && (
        <div className="thinking-content">
          {thinking.steps.map((step, index) => (
            <div
              key={step.id}
              className={`thinking-step ${step.status === 'complete' ? 'thinking-step-completed' : ''}`}
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="thinking-step-icon">
                {getStepIcon(step.status)}
              </div>
              <div className="flex-1 min-w-0">
                <p className={`text-sm ${step.status === 'active' ? 'text-noir-200' : 'text-noir-400'}`}>
                  {step.description}
                </p>
                {step.result && step.status === 'complete' && (
                  <p className="mt-1 text-xs text-noir-500 line-clamp-2">
                    {step.result}
                  </p>
                )}
                {/* Substeps */}
                {step.substeps && step.substeps.length > 0 && (
                  <div className="mt-2 ml-2 space-y-1 border-l border-noir-700/50 pl-3">
                    {step.substeps.map(substep => (
                      <div key={substep.id} className="flex items-center gap-2 text-xs text-noir-500">
                        {substep.status === 'complete' ? (
                          <svg className="w-3 h-3 text-jade-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                        ) : substep.status === 'active' ? (
                          <div className="w-3 h-3 rounded-full bg-brass-500/50 animate-pulse" />
                        ) : (
                          <div className="w-3 h-3 rounded-full bg-noir-600" />
                        )}
                        <span>{substep.description}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Activity Log (collapsible) */}
          {thinking.logs.length > 0 && (
            <details className="mt-4 pt-3 border-t border-noir-700/30">
              <summary className="text-2xs text-noir-500 cursor-pointer hover:text-noir-400 transition-colors">
                查看詳細日誌 ({thinking.logs.length})
              </summary>
              <div className="mt-2 space-y-1 max-h-32 overflow-y-auto scrollbar-thin">
                {thinking.logs.slice(-10).map((log, index) => (
                  <div key={index} className="text-2xs font-mono">
                    <span className="text-noir-600">
                      {log.timestamp.toLocaleTimeString('zh-TW', { hour12: false })}
                    </span>
                    {log.agent && (
                      <span className="text-brass-500/70 ml-2">[{log.agent}]</span>
                    )}
                    <span className={`ml-2 ${
                      log.level === 'error' ? 'text-vermilion-400' :
                      log.level === 'warn' ? 'text-brass-400' :
                      'text-noir-500'
                    }`}>
                      {log.message}
                    </span>
                  </div>
                ))}
              </div>
            </details>
          )}

          {/* Step History Timeline (collapsible) */}
          {thinking.stepHistory && thinking.stepHistory.length > 0 && (
            <details className="mt-4 pt-3 border-t border-noir-700/30">
              <summary className="text-2xs text-noir-500 cursor-pointer hover:text-noir-400 transition-colors flex items-center gap-2">
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                思考歷程時間線 ({thinking.stepHistory.length} 個步驟)
              </summary>
              <div className="mt-3 relative">
                {/* Timeline line */}
                <div className="absolute left-2 top-0 bottom-0 w-0.5 bg-noir-700/50" />

                <div className="space-y-2">
                  {thinking.stepHistory.map((entry, index) => {
                    const nodeDescriptions: Record<string, string> = {
                      'query_analyzer': '分析查詢意圖',
                      'planner': '制定研究計畫',
                      'execute_task': '執行研究任務',
                      'replanner': '檢視並調整計畫',
                      'reporter': '生成研究報告',
                    };
                    const description = entry.data?.description || nodeDescriptions[entry.step] || entry.step;
                    const time = new Date(entry.timestamp).toLocaleTimeString('zh-TW', { hour12: false });

                    return (
                      <div key={`${entry.sequence}-${index}`} className="relative pl-6">
                        {/* Timeline dot */}
                        <div className={`absolute left-0.5 w-3 h-3 rounded-full border-2 ${
                          entry.status === 'completed' ? 'bg-jade-500 border-jade-400' :
                          entry.status === 'running' ? 'bg-brass-500 border-brass-400 animate-pulse' :
                          entry.status === 'error' ? 'bg-vermilion-500 border-vermilion-400' :
                          'bg-noir-600 border-noir-500'
                        }`} />

                        <div className="bg-noir-800/30 rounded px-2 py-1.5">
                          <div className="flex items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <span className="text-2xs font-mono text-brass-400">
                                #{entry.sequence}
                              </span>
                              <span className="text-2xs font-medium text-noir-300">
                                {description}
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className={`px-1.5 py-0.5 rounded text-2xs ${
                                entry.status === 'completed' ? 'bg-jade-500/20 text-jade-400' :
                                entry.status === 'running' ? 'bg-brass-500/20 text-brass-400' :
                                entry.status === 'error' ? 'bg-vermilion-500/20 text-vermilion-400' :
                                'bg-noir-700/50 text-noir-500'
                              }`}>
                                {entry.status}
                              </span>
                              <span className="text-2xs text-noir-600 font-mono">
                                {time}
                              </span>
                            </div>
                          </div>
                          {entry.data && Object.keys(entry.data).length > 0 && entry.data.description !== description && (
                            <div className="mt-1 text-2xs text-noir-500">
                              {Object.entries(entry.data)
                                .filter(([key]) => key !== 'description')
                                .map(([key, value]) => (
                                  <span key={key} className="mr-2">
                                    {key}: {typeof value === 'string' ? value.substring(0, 50) : JSON.stringify(value).substring(0, 50)}
                                    {(typeof value === 'string' ? value.length : JSON.stringify(value).length) > 50 ? '...' : ''}
                                  </span>
                                ))}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </details>
          )}

          {/* Graph State Viewer (collapsible) */}
          {thinking.graphState && (
            <details className="mt-4 pt-3 border-t border-noir-700/30">
              <summary className="text-2xs text-noir-500 cursor-pointer hover:text-noir-400 transition-colors flex items-center gap-2">
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                </svg>
                查看 Agent State
              </summary>
              <div className="mt-3 space-y-3">
                {/* Current Node */}
                {thinking.graphState.current_node && (
                  <div className="flex items-center gap-2">
                    <span className="text-2xs text-noir-500">當前節點:</span>
                    <span className="px-2 py-0.5 bg-brass-500/20 text-brass-400 rounded text-2xs font-mono">
                      {thinking.graphState.current_node}
                    </span>
                  </div>
                )}

                {/* Input Query */}
                {thinking.graphState.input && (
                  <div>
                    <span className="text-2xs text-noir-500 block mb-1">輸入查詢:</span>
                    <div className="bg-noir-800/50 rounded px-2 py-1 text-2xs text-noir-300 font-mono">
                      {thinking.graphState.input}
                    </div>
                  </div>
                )}

                {/* Plan Tasks */}
                {thinking.graphState.plan?.tasks && thinking.graphState.plan.tasks.length > 0 && (
                  <div>
                    <span className="text-2xs text-noir-500 block mb-1">
                      執行計畫 ({thinking.graphState.plan.tasks.length} 個任務):
                    </span>
                    <div className="space-y-1">
                      {thinking.graphState.plan.tasks.map((task, index) => (
                        <div
                          key={index}
                          className="flex items-start gap-2 bg-noir-800/30 rounded px-2 py-1"
                        >
                          <span className={`text-2xs font-mono ${
                            task.status === 'complete' ? 'text-jade-400' :
                            task.status === 'in_progress' ? 'text-brass-400' :
                            task.status === 'error' ? 'text-vermilion-400' :
                            'text-noir-500'
                          }`}>
                            [{task.id || index + 1}]
                          </span>
                          <div className="flex-1 min-w-0">
                            <p className="text-2xs text-noir-300 truncate">{task.description}</p>
                            {task.tool && (
                              <span className="text-2xs text-noir-500 font-mono">
                                tool: {task.tool}
                              </span>
                            )}
                            {task.result && (
                              <p className="text-2xs text-noir-500 truncate mt-0.5">
                                {task.result.substring(0, 100)}...
                              </p>
                            )}
                          </div>
                          <span className={`px-1.5 py-0.5 rounded text-2xs ${
                            task.status === 'complete' ? 'bg-jade-500/20 text-jade-400' :
                            task.status === 'in_progress' ? 'bg-brass-500/20 text-brass-400' :
                            task.status === 'error' ? 'bg-vermilion-500/20 text-vermilion-400' :
                            'bg-noir-700/50 text-noir-500'
                          }`}>
                            {task.status || 'pending'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Past Steps / Tool Executions */}
                {thinking.graphState.past_steps && thinking.graphState.past_steps.length > 0 && (
                  <div>
                    <span className="text-2xs text-noir-500 block mb-1">
                      工具執行記錄 ({thinking.graphState.past_steps.length}):
                    </span>
                    <div className="space-y-1 max-h-32 overflow-y-auto scrollbar-thin">
                      {thinking.graphState.past_steps.map((step, index) => (
                        <div key={index} className="bg-noir-800/30 rounded px-2 py-1">
                          <div className="flex items-center gap-2">
                            <span className="text-2xs text-brass-400 font-mono">
                              {step[0]?.tool || `Step ${index + 1}`}
                            </span>
                          </div>
                          <p className="text-2xs text-noir-500 mt-0.5 line-clamp-2">
                            {typeof step[1] === 'string' ? step[1].substring(0, 150) : JSON.stringify(step[1]).substring(0, 150)}...
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Raw State Debug (hidden by default) */}
                <details className="mt-2">
                  <summary className="text-2xs text-noir-600 cursor-pointer hover:text-noir-500">
                    原始 State JSON
                  </summary>
                  <pre className="mt-1 bg-noir-900 rounded p-2 text-2xs text-noir-400 font-mono overflow-x-auto max-h-40 overflow-y-auto scrollbar-thin">
                    {JSON.stringify(thinking.graphState, null, 2)}
                  </pre>
                </details>
              </div>
            </details>
          )}
        </div>
      )}
    </div>
  );
}
