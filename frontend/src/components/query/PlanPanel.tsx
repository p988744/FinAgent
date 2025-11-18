import { Search, Clock, Tag, Building, Calendar, Layers } from 'lucide-react'
import type { ResearchPlan } from '../../types/query'

interface PlanPanelProps {
  plan: ResearchPlan | null
}

function getComplexityColor(complexity: string) {
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

function getSearchMethodIcon(method: string) {
  switch (method) {
    case 'vector_search':
      return '🔍'
    case 'hard_search':
      return '⏱'
    case 'hybrid':
      return '🔄'
    default:
      return '📋'
  }
}

export function PlanPanel({ plan }: PlanPanelProps) {
  if (!plan) {
    return null
  }

  const { analysis, tasks, estimated_total_time, use_hard_search } = plan

  return (
    <div className="bg-white rounded-lg shadow border border-gray-200 p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <Layers className="h-4 w-4 text-navy-700" />
          <h3 className="text-sm font-bold text-gray-900">研究計畫</h3>
          <span className="text-xs text-gray-600 bg-gray-100 px-1.5 py-0.5 rounded">
            {tasks.length} 項任務・{estimated_total_time} 秒
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="space-y-3">
        {/* Query Analysis */}
        <div>
          <h4 className="text-xs font-bold text-gray-900 mb-2">查詢分析</h4>
          <div className="grid grid-cols-2 gap-3 text-sm">
            {/* Keywords */}
            <div className="flex items-start space-x-2">
              <Tag className="h-4 w-4 text-navy-600 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-gray-700 font-medium">關鍵字：</span>
                <div className="flex flex-wrap gap-1 mt-1.5">
                  {analysis.keywords.map((kw, i) => (
                    <span
                      key={i}
                      className="inline-block px-2 py-0.5 bg-navy-100 text-navy-800 rounded text-xs font-medium border border-navy-200"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Must-have keywords */}
            {analysis.must_have_keywords.length > 0 && (
              <div className="flex items-start space-x-2">
                <Tag className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                <div>
                  <span className="text-gray-700 font-medium">必要關鍵字：</span>
                  <div className="flex flex-wrap gap-1 mt-1.5">
                    {analysis.must_have_keywords.map((kw, i) => (
                      <span
                        key={i}
                        className="inline-block px-2 py-0.5 bg-red-100 text-red-800 rounded text-xs font-medium border border-red-200"
                      >
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Entity type */}
            <div className="flex items-center space-x-2">
              <Search className="h-4 w-4 text-gray-500 flex-shrink-0" />
              <div>
                <span className="text-gray-600">實體類型：</span>
                <span className="font-medium">{analysis.entity_type}</span>
              </div>
            </div>

            {/* Jurisdiction */}
            {analysis.jurisdiction && (
              <div className="flex items-center space-x-2">
                <Building className="h-4 w-4 text-gray-500 flex-shrink-0" />
                <div>
                  <span className="text-gray-600">管轄機關：</span>
                  <span className="font-medium">{analysis.jurisdiction}</span>
                </div>
              </div>
            )}

            {/* Time period */}
            {analysis.time_period && (
              <div className="flex items-center space-x-2">
                <Calendar className="h-4 w-4 text-gray-500 flex-shrink-0" />
                <div>
                  <span className="text-gray-600">時間範圍：</span>
                  <span className="font-medium">{analysis.time_period}</span>
                </div>
              </div>
            )}

            {/* Query type */}
            <div className="flex items-center space-x-2">
              <Layers className="h-4 w-4 text-gray-500 flex-shrink-0" />
              <div>
                <span className="text-gray-600">查詢類型：</span>
                <span className="font-medium">{analysis.query_type}</span>
              </div>
            </div>

            {/* Complexity */}
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4 text-gray-500 flex-shrink-0" />
              <div>
                <span className="text-gray-600">複雜度：</span>
                <span
                  className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${getComplexityColor(analysis.complexity)}`}
                >
                  {analysis.complexity}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Research Tasks */}
        <div className="border-t pt-3">
          <h4 className="text-xs font-bold text-gray-900 mb-2">研究任務</h4>
          <div className="space-y-2">
            {tasks.map((task) => (
              <div
                key={task.id}
                className="flex items-center justify-between p-2 bg-gray-50 rounded"
              >
                <div className="flex items-center space-x-2">
                  <span className="text-sm">{getSearchMethodIcon(task.search_method)}</span>
                  <span className="text-sm text-gray-900">
                    {task.id}. {task.task}
                  </span>
                </div>
                {task.estimated_time && (
                  <span className="text-xs text-gray-500">~{task.estimated_time}s</span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Summary */}
        <div className="border-t pt-3 flex items-center justify-between text-sm">
          <div className="text-gray-600">
            預估總時間：<span className="font-medium">{estimated_total_time} 秒</span>
          </div>
          {use_hard_search && (
            <span className="inline-block px-2 py-0.5 bg-orange-100 text-orange-700 rounded text-xs">
              使用深度搜索
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
