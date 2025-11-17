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
      return <CheckCircle2 className="h-6 w-6 text-green-500" />
    case 'active':
      return <Loader2 className="h-6 w-6 text-blue-500 animate-spin" />
    case 'error':
      return <AlertCircle className="h-6 w-6 text-red-500" />
    default:
      return <Circle className="h-6 w-6 text-gray-300" />
  }
}

function getStatusColor(status: StepStatus) {
  switch (status) {
    case 'done':
      return 'text-green-700 bg-green-50'
    case 'active':
      return 'text-blue-700 bg-blue-50'
    case 'error':
      return 'text-red-700 bg-red-50'
    default:
      return 'text-gray-500 bg-gray-50'
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
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        代理工作流程
      </h3>
      <div className="space-y-4">
        {defaultSteps.map((step, index) => {
          const stepData = steps.get(step.id)
          const status = stepData?.status || 'pending'
          const description = stepData?.description || step.description
          const elapsed = stepData?.elapsed_ms || 0

          return (
            <div key={step.id} className="flex items-start">
              <div className="flex-shrink-0 mr-4">
                {getStatusIcon(status)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-900">
                    {step.name}
                  </p>
                  {status !== 'pending' && (
                    <span className="text-xs text-gray-500">
                      {formatTime(elapsed)}
                    </span>
                  )}
                </div>
                <p
                  className={`text-xs mt-1 px-2 py-1 rounded-md inline-block ${getStatusColor(status)}`}
                >
                  {description}
                </p>
              </div>
              {index < defaultSteps.length - 1 && (
                <div className="absolute left-7 mt-8 h-full w-0.5 bg-gray-200" />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
