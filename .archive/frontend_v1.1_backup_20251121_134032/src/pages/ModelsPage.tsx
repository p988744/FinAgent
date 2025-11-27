import { useState, useEffect, useCallback } from 'react'
import { AlertCircle, CheckCircle2 } from 'lucide-react'
import { ModelSelector } from '../components/models/ModelSelector'
import { ConnectionTester } from '../components/models/ConnectionTester'
import { UsageStatsCard } from '../components/models/UsageStatsCard'
import { CostCalculator } from '../components/models/CostCalculator'
import type {
  LLMModel,
  EmbeddingModel,
  ConnectionTestResult,
  UsageStats,
  CostEstimate,
} from '../types/models'

export function ModelsPage() {
  const [llmModels, setLLMModels] = useState<LLMModel[]>([])
  const [embeddingModels, setEmbeddingModels] = useState<EmbeddingModel[]>([])
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null)
  const [isLoadingLLM, setIsLoadingLLM] = useState(true)
  const [isLoadingEmbedding, setIsLoadingEmbedding] = useState(true)
  const [isLoadingStats, setIsLoadingStats] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const showSuccess = (message: string) => {
    setSuccessMessage(message)
    setTimeout(() => setSuccessMessage(null), 3000)
  }

  const showError = (message: string) => {
    setError(message)
    setTimeout(() => setError(null), 5000)
  }

  // Fetch LLM models
  const fetchLLMModels = useCallback(async () => {
    setIsLoadingLLM(true)
    try {
      const response = await fetch('/api/v1/models/llm/available')
      if (!response.ok) throw new Error('Failed to fetch LLM models')
      const data = await response.json()
      setLLMModels(data)
    } catch (err) {
      showError('載入 LLM 模型失敗')
      console.error('Failed to fetch LLM models:', err)
    } finally {
      setIsLoadingLLM(false)
    }
  }, [])

  // Fetch embedding models
  const fetchEmbeddingModels = useCallback(async () => {
    setIsLoadingEmbedding(true)
    try {
      const response = await fetch('/api/v1/models/embedding/available')
      if (!response.ok) throw new Error('Failed to fetch embedding models')
      const data = await response.json()
      setEmbeddingModels(data)
    } catch (err) {
      showError('載入嵌入模型失敗')
      console.error('Failed to fetch embedding models:', err)
    } finally {
      setIsLoadingEmbedding(false)
    }
  }, [])

  // Fetch usage stats
  const fetchUsageStats = useCallback(async () => {
    setIsLoadingStats(true)
    try {
      const response = await fetch('/api/v1/models/stats')
      if (!response.ok) throw new Error('Failed to fetch usage stats')
      const data = await response.json()
      setUsageStats(data)
    } catch (err) {
      console.error('Failed to fetch usage stats:', err)
    } finally {
      setIsLoadingStats(false)
    }
  }, [])

  // Initial data fetch
  useEffect(() => {
    fetchLLMModels()
    fetchEmbeddingModels()
    fetchUsageStats()
  }, [fetchLLMModels, fetchEmbeddingModels, fetchUsageStats])

  // Select LLM model
  const handleSelectLLM = async (modelId: string) => {
    try {
      const response = await fetch('/api/v1/models/llm/active', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId }),
      })

      if (!response.ok) throw new Error('Failed to select LLM model')

      const result = await response.json()
      await fetchLLMModels()
      await fetchUsageStats()
      showSuccess(result.message || `已切換到 ${modelId}`)
    } catch (err) {
      showError('切換 LLM 模型失敗')
      console.error('Failed to select LLM:', err)
    }
  }

  // Select embedding model
  const handleSelectEmbedding = async (modelId: string) => {
    try {
      const response = await fetch('/api/v1/models/embedding/active', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId }),
      })

      if (!response.ok) throw new Error('Failed to select embedding model')

      const result = await response.json()
      await fetchEmbeddingModels()
      await fetchUsageStats()
      showSuccess(result.message || `已切換到 ${modelId}`)
    } catch (err) {
      showError('切換嵌入模型失敗')
      console.error('Failed to select embedding:', err)
    }
  }

  // Test LLM connection
  const handleTestConnection = async (): Promise<ConnectionTestResult> => {
    const response = await fetch('/api/v1/models/llm/test', {
      method: 'POST',
    })

    if (!response.ok) {
      throw new Error('Connection test failed')
    }

    return await response.json()
  }

  // Calculate cost
  const handleCalculateCost = async (
    inputTokens: number,
    outputTokens: number,
    model: string
  ): Promise<CostEstimate> => {
    const params = new URLSearchParams({
      input_tokens: inputTokens.toString(),
      output_tokens: outputTokens.toString(),
      model: model,
    })

    const response = await fetch(`/api/v1/models/cost/estimate?${params}`, {
      method: 'POST',
    })

    if (!response.ok) {
      throw new Error('Cost calculation failed')
    }

    return await response.json()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">模型管理</h1>
        <p className="mt-1 text-sm text-gray-500">
          選擇 LLM 模型、測試連線和監控使用量
        </p>
      </div>

      {/* Status messages */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 flex items-center">
          <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {successMessage && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4 flex items-center">
          <CheckCircle2 className="h-5 w-5 text-green-500 mr-2" />
          <p className="text-sm text-green-700">{successMessage}</p>
        </div>
      )}

      {/* Connection Tester */}
      <ConnectionTester onTest={handleTestConnection} />

      {/* Usage Stats */}
      <UsageStatsCard stats={usageStats} isLoading={isLoadingStats} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* LLM Models */}
        <ModelSelector
          models={llmModels}
          onSelect={handleSelectLLM}
          isLoading={isLoadingLLM}
          title="LLM 模型選擇"
        />

        {/* Embedding Models */}
        <ModelSelector
          models={embeddingModels}
          onSelect={handleSelectEmbedding}
          isLoading={isLoadingEmbedding}
          title="嵌入模型選擇"
        />
      </div>

      {/* Cost Calculator */}
      {llmModels.length > 0 && (
        <CostCalculator models={llmModels} onCalculate={handleCalculateCost} />
      )}
    </div>
  )
}
