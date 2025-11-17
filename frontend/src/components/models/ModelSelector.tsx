import { Check, Star, Zap } from 'lucide-react'
import type { LLMModel, EmbeddingModel } from '../../types/models'

interface ModelSelectorProps<T extends LLMModel | EmbeddingModel> {
  models: T[]
  onSelect: (modelId: string) => Promise<void>
  isLoading: boolean
  title: string
}

export function ModelSelector<T extends LLMModel | EmbeddingModel>({
  models,
  onSelect,
  isLoading,
  title,
}: ModelSelectorProps<T>) {
  const isLLMModel = (model: T): model is LLMModel & T => {
    return 'cost_per_1k_input' in model
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      </div>

      {isLoading ? (
        <div className="p-8 text-center text-gray-500">載入模型列表中...</div>
      ) : (
        <div className="p-4 space-y-3">
          {models.map((model) => (
            <div
              key={model.id}
              className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                model.is_active
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50'
              }`}
              onClick={() => !model.is_active && onSelect(model.id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div>
                    <div className="flex items-center space-x-2">
                      <h4 className="font-medium text-gray-900">{model.name}</h4>
                      {model.recommended && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                          <Star className="h-3 w-3 mr-1" />
                          推薦
                        </span>
                      )}
                      {model.is_active && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                          <Check className="h-3 w-3 mr-1" />
                          使用中
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-500 mt-1">
                      {model.description}
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-3 flex items-center space-x-4 text-xs text-gray-600">
                {isLLMModel(model) ? (
                  <>
                    <span className="flex items-center">
                      <Zap className="h-3 w-3 mr-1 text-orange-500" />
                      最大 {(model.max_tokens / 1000).toFixed(0)}K tokens
                    </span>
                    <span>
                      輸入: ${model.cost_per_1k_input.toFixed(6)}/1K
                    </span>
                    <span>
                      輸出: ${model.cost_per_1k_output.toFixed(6)}/1K
                    </span>
                  </>
                ) : (
                  <>
                    <span>維度: {(model as EmbeddingModel).dimensions}</span>
                    <span>
                      成本: ${(model as EmbeddingModel).cost_per_1k_tokens.toFixed(6)}/1K tokens
                    </span>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
