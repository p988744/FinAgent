import { useState } from 'react'
import { Calculator, RefreshCw } from 'lucide-react'
import type { CostEstimate, LLMModel } from '../../types/models'

interface CostCalculatorProps {
  models: LLMModel[]
  onCalculate: (
    inputTokens: number,
    outputTokens: number,
    model: string
  ) => Promise<CostEstimate>
}

export function CostCalculator({ models, onCalculate }: CostCalculatorProps) {
  const [inputTokens, setInputTokens] = useState(1000)
  const [outputTokens, setOutputTokens] = useState(500)
  const [selectedModel, setSelectedModel] = useState(
    models.find((m) => m.is_active)?.id || models[0]?.id || 'gpt-4o-mini'
  )
  const [isCalculating, setIsCalculating] = useState(false)
  const [estimate, setEstimate] = useState<CostEstimate | null>(null)

  const handleCalculate = async () => {
    setIsCalculating(true)
    try {
      const result = await onCalculate(inputTokens, outputTokens, selectedModel)
      setEstimate(result)
    } catch (err) {
      console.error('Failed to calculate cost:', err)
    } finally {
      setIsCalculating(false)
    }
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center">
          <Calculator className="h-5 w-5 text-gray-600 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">成本計算器</h3>
        </div>
      </div>

      <div className="p-4 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            模型
          </label>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
          >
            {models.map((model) => (
              <option key={model.id} value={model.id}>
                {model.name}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              輸入 Tokens
            </label>
            <input
              type="number"
              min="0"
              value={inputTokens}
              onChange={(e) => setInputTokens(parseInt(e.target.value) || 0)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              輸出 Tokens
            </label>
            <input
              type="number"
              min="0"
              value={outputTokens}
              onChange={(e) => setOutputTokens(parseInt(e.target.value) || 0)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
        </div>

        <button
          onClick={handleCalculate}
          disabled={isCalculating}
          className="w-full inline-flex justify-center items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {isCalculating ? (
            <>
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              計算中...
            </>
          ) : (
            <>
              <Calculator className="h-4 w-4 mr-2" />
              計算成本
            </>
          )}
        </button>

        {estimate && (
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">預估成本</h4>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">輸入成本:</span>
                <span className="font-medium">${estimate.input_cost.toFixed(6)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">輸出成本:</span>
                <span className="font-medium">${estimate.output_cost.toFixed(6)}</span>
              </div>
              <div className="border-t border-gray-200 pt-1 mt-1">
                <div className="flex justify-between">
                  <span className="text-gray-900 font-medium">總成本:</span>
                  <span className="font-bold text-green-600">
                    ${estimate.total_cost.toFixed(6)}
                  </span>
                </div>
              </div>
              <div className="text-xs text-gray-500 mt-2">
                模型: {estimate.model}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
