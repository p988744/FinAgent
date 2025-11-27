import { Search, Tag, Clock, Wrench, CheckCircle2, Info, Loader2, XCircle, PlayCircle } from 'lucide-react'
import type { DynamicPlanAnalysis, ToolExecutionStatus } from '../../types/research'

interface DynamicPlanPanelProps {
  analysis: DynamicPlanAnalysis | null
  toolExecutions?: Map<string, ToolExecutionStatus>
}

function getIntentLabel(intent: string): string {
  const intentLabels: Record<string, string> = {
    general_search: '一般搜尋',
    temporal: '時間查詢',
    comprehensive: '完整列表',
    specific_file: '特定檔案',
    comparison: '比較分析',
    entity_specific: '特定實體',
  }
  return intentLabels[intent] || intent
}

function getIntentColor(intent: string): string {
  switch (intent) {
    case 'temporal':
      return 'text-blue-800 bg-blue-50 border border-blue-200'
    case 'comprehensive':
      return 'text-purple-800 bg-purple-50 border border-purple-200'
    case 'specific_file':
      return 'text-green-800 bg-green-50 border border-green-200'
    case 'comparison':
      return 'text-orange-800 bg-orange-50 border border-orange-200'
    case 'entity_specific':
      return 'text-indigo-800 bg-indigo-50 border border-indigo-200'
    default:
      return 'text-gray-800 bg-gray-50 border border-gray-200'
  }
}

function getComplexityColor(complexity: string): string {
  switch (complexity) {
    case 'simple':
      return 'text-success-800 bg-success-50 border border-success-200'
    case 'medium':
      return 'text-warning-800 bg-warning-50 border border-warning-200'
    case 'complex':
      return 'text-red-800 bg-red-50 border border-red-200'
    default:
      return 'text-gray-700 bg-gray-50 border border-gray-200'
  }
}

function getToolIcon(toolName: string): string {
  const toolIcons: Record<string, string> = {
    vector_search: '🔍',
    metadata_search: '⏱',
    list_documents: '📋',
    read_file: '📄',
    hybrid_search: '🔄',
    multi_entity_search: '🔀',
  }
  return toolIcons[toolName] || '🔧'
}

function getToolLabel(toolName: string): string {
  const toolLabels: Record<string, string> = {
    vector_search: '向量搜尋',
    metadata_search: '元數據搜尋',
    list_documents: '文件列表',
    read_file: '讀取檔案',
    hybrid_search: '混合搜尋',
    multi_entity_search: '多實體搜尋',
  }
  return toolLabels[toolName] || toolName
}

function getExecutionStatusIcon(status: string) {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className="h-4 w-4 text-success-600" />
    case 'executing':
      return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
    case 'failed':
      return <XCircle className="h-4 w-4 text-red-600" />
    case 'planned':
    default:
      return <PlayCircle className="h-4 w-4 text-gray-400" />
  }
}

function getExecutionStatusBadge(status: string) {
  switch (status) {
    case 'completed':
      return 'bg-success-50 text-success-700 border-success-200'
    case 'executing':
      return 'bg-blue-50 text-blue-700 border-blue-200'
    case 'failed':
      return 'bg-red-50 text-red-700 border-red-200'
    case 'planned':
    default:
      return 'bg-gray-50 text-gray-600 border-gray-200'
  }
}

function getExecutionStatusLabel(status: string): string {
  const statusLabels: Record<string, string> = {
    planned: '計劃中',
    executing: '執行中',
    completed: '已完成',
    failed: '失敗',
  }
  return statusLabels[status] || status
}

export function DynamicPlanPanel({ analysis, toolExecutions }: DynamicPlanPanelProps) {
  if (!analysis) {
    return null
  }

  const { query_analysis, selected_tools } = analysis

  return (
    <div className="bg-white rounded-lg shadow border border-gray-200 p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <Search className="h-4 w-4 text-navy-700" />
          <h3 className="text-sm font-bold text-gray-900">動態規劃分析</h3>
          <span className="text-xs text-gray-600 bg-gray-100 px-1.5 py-0.5 rounded">
            {selected_tools.length} 個工具
          </span>
        </div>
      </div>

      {/* Query Analysis */}
      <div>
        <h4 className="text-xs font-bold text-gray-900 mb-2 flex items-center space-x-1">
          <Info className="h-3.5 w-3.5" />
          <span>查詢分析</span>
        </h4>
        <div className="grid grid-cols-2 gap-2 text-sm">
          {/* Intent */}
          <div className="flex items-center space-x-2">
            <Tag className="h-4 w-4 text-gray-500 flex-shrink-0" />
            <div>
              <span className="text-gray-600">意圖：</span>
              <span
                className={`inline-block ml-1 px-2 py-0.5 rounded text-xs font-medium ${getIntentColor(query_analysis.intent)}`}
              >
                {getIntentLabel(query_analysis.intent)}
              </span>
            </div>
          </div>

          {/* Complexity */}
          <div className="flex items-center space-x-2">
            <Clock className="h-4 w-4 text-gray-500 flex-shrink-0" />
            <div>
              <span className="text-gray-600">複雜度：</span>
              <span
                className={`inline-block ml-1 px-2 py-0.5 rounded text-xs font-medium ${getComplexityColor(query_analysis.complexity)}`}
              >
                {query_analysis.complexity}
              </span>
            </div>
          </div>

          {/* Entities */}
          {query_analysis.entities.length > 0 && (
            <div className="col-span-2 flex items-start space-x-2">
              <Tag className="h-4 w-4 text-navy-600 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-gray-700 font-medium">實體：</span>
                <div className="flex flex-wrap gap-1 mt-1.5">
                  {query_analysis.entities.map((entity, i) => (
                    <span
                      key={i}
                      className="inline-block px-2 py-0.5 bg-navy-100 text-navy-800 rounded text-xs font-medium border border-navy-200"
                    >
                      {entity}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Features */}
          <div className="col-span-2 flex flex-wrap gap-2">
            {query_analysis.has_temporal_constraint && (
              <span className="inline-flex items-center px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs border border-blue-200">
                <Clock className="h-3 w-3 mr-1" />
                時間限制 ({query_analysis.temporal_type})
              </span>
            )}
            {query_analysis.requires_multi_entity && (
              <span className="inline-flex items-center px-2 py-0.5 bg-orange-50 text-orange-700 rounded text-xs border border-orange-200">
                <Tag className="h-3 w-3 mr-1" />
                多實體
              </span>
            )}
            {query_analysis.requires_exhaustive_search && (
              <span className="inline-flex items-center px-2 py-0.5 bg-purple-50 text-purple-700 rounded text-xs border border-purple-200">
                <Search className="h-3 w-3 mr-1" />
                完整搜尋
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Selected Tools */}
      <div className="border-t pt-3">
        <h4 className="text-xs font-bold text-gray-900 mb-2 flex items-center space-x-1">
          <Wrench className="h-3.5 w-3.5" />
          <span>選擇的工具</span>
        </h4>
        <div className="space-y-2">
          {selected_tools.map((tool, index) => {
            const execution = toolExecutions?.get(tool.tool_name)
            const status = execution?.status || 'planned'

            return (
              <div
                key={index}
                className="p-2 bg-gray-50 rounded border border-gray-200"
              >
                <div className="flex items-start justify-between mb-1">
                  <div className="flex items-center space-x-2">
                    {getExecutionStatusIcon(status)}
                    <span className="text-sm">{getToolIcon(tool.tool_name)}</span>
                    <span className="text-sm font-medium text-gray-900">
                      {getToolLabel(tool.tool_name)}
                    </span>
                    <span className="text-xs text-gray-500 bg-white px-1.5 py-0.5 rounded border border-gray-200">
                      #{tool.execution_order}
                    </span>
                    <span className={`text-xs px-1.5 py-0.5 rounded border font-medium ${getExecutionStatusBadge(status)}`}>
                      {getExecutionStatusLabel(status)}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-gray-600 ml-6">{tool.reason}</p>

                {/* Execution Results */}
                {execution && execution.status === 'completed' && (
                  <div className="ml-6 mt-1.5 text-xs text-success-700">
                    ✓ {execution.result_count} 個結果 ({execution.execution_time_ms}ms)
                  </div>
                )}

                {execution && execution.status === 'failed' && execution.error && (
                  <div className="ml-6 mt-1.5 text-xs text-red-700">
                    ✗ {execution.error}
                  </div>
                )}

                {/* Parameters */}
                {Object.keys(tool.parameters).length > 0 && (
                  <div className="ml-6 mt-1.5 flex flex-wrap gap-1">
                    {Object.entries(tool.parameters).map(([key, value]) => (
                      <span
                        key={key}
                        className="inline-block px-1.5 py-0.5 bg-white text-gray-700 rounded text-xs border border-gray-300"
                      >
                        {key}: {Array.isArray(value) ? value.join(', ') : String(value)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
