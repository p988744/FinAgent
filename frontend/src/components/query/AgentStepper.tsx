import { CheckCircle2, Circle, Loader2, AlertCircle } from 'lucide-react'
import type { StepUpdate, StepStatus } from '../../types/query'

interface Step {
  id: 'planning' | 'action' | 'validation' | 'answer'
  name: string
  description: string
}

const defaultSteps: Step[] = [
  { id: 'planning', name: '規劃', description: '分析查詢意圖' },
  { id: 'action', name: '執行', description: 'RAG 檢索' },
  { id: 'validation', name: '驗證', description: '引用完整性檢查' },
  { id: 'answer', name: '答案', description: '生成最終答案' },
]

interface AgentStepperProps {
  steps: Map<string, StepUpdate>
}

function getStatusIcon(status: StepStatus) {
  switch (status) {
    case 'done':
      return <CheckCircle2 className="h-6 w-6 text-success-600" />
    case 'active':
      return <Loader2 className="h-6 w-6 text-navy-600 animate-spin" />
    case 'error':
      return <AlertCircle className="h-6 w-6 text-red-600" />
    default:
      return <Circle className="h-6 w-6 text-gray-400" />
  }
}

function getStatusColor(status: StepStatus) {
  switch (status) {
    case 'done':
      return 'text-success-800 bg-success-50 border border-success-200'
    case 'active':
      return 'text-navy-800 bg-navy-50 border border-navy-200'
    case 'error':
      return 'text-red-800 bg-red-50 border border-red-200'
    default:
      return 'text-gray-600 bg-gray-50 border border-gray-200'
  }
}

function formatTime(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`
  }
  return `${(ms / 1000).toFixed(1)}s`
}

export function AgentStepper({ steps }: AgentStepperProps) {
  return (
    <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
      <h3 className="text-sm font-bold text-gray-900 mb-3 pb-2 border-b border-gray-200">
        工作流程
      </h3>
      <div className="space-y-3">
        {defaultSteps.map((step, index) => {
          const stepData = steps.get(step.id)
          const status = stepData?.status || 'pending'
          const description = stepData?.description || step.description
          const elapsed = stepData?.elapsed_ms || 0

          return (
            <div key={step.id} className="flex items-start">
              <div className="flex-shrink-0 mr-2">
                {getStatusIcon(status)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-sm font-semibold text-gray-900">
                    {step.name}
                  </p>
                  {status !== 'pending' && (
                    <span className="text-xs text-gray-600 bg-gray-100 px-1.5 py-0.5 rounded">
                      {formatTime(elapsed)}
                    </span>
                  )}
                </div>
                <p
                  className={`text-xs px-2 py-0.5 rounded inline-block font-medium ${getStatusColor(status)}`}
                >
                  {description}
                </p>
              </div>
              {index < defaultSteps.length - 1 && (
                <div className="absolute left-6 mt-7 h-full w-0.5 bg-gray-300" />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
