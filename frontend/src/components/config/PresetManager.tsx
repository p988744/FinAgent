import { useState } from 'react'
import {
  Save,
  Trash2,
  Check,
  Play,
  Plus,
  RefreshCw,
} from 'lucide-react'
import type { PresetResponse, PresetCreate } from '../../types/config'

interface PresetManagerProps {
  presets: PresetResponse[]
  activePresets: Record<string, PresetResponse | null>
  onCreate: (preset: PresetCreate) => Promise<void>
  onActivate: (id: number) => Promise<void>
  onDelete: (id: number) => Promise<void>
  isLoading: boolean
}

function PresetCard({
  preset,
  isActive,
  onActivate,
  onDelete,
}: {
  preset: PresetResponse
  isActive: boolean
  onActivate: () => Promise<void>
  onDelete: () => Promise<void>
}) {
  const [isActivating, setIsActivating] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  const handleActivate = async () => {
    setIsActivating(true)
    try {
      await onActivate()
    } finally {
      setIsActivating(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm(`確定要刪除預設 "${preset.name}" 嗎？`)) return
    setIsDeleting(true)
    try {
      await onDelete()
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <div
      className={`border rounded-lg p-4 ${
        isActive ? 'border-green-500 bg-green-50' : 'border-gray-200'
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center">
          <h4 className="font-medium text-gray-900">{preset.name}</h4>
          {isActive && (
            <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
              <Check className="h-3 w-3 mr-1" />
              使用中
            </span>
          )}
        </div>
        <span className="text-xs text-gray-500 uppercase">
          {preset.config_type}
        </span>
      </div>

      <div className="text-sm text-gray-600 space-y-1">
        <p>模型: {preset.model}</p>
        <p>API 金鑰: {preset.api_key || '(未設定)'}</p>
        {preset.base_url && <p>Base URL: {preset.base_url}</p>}
        {preset.temperature !== null && (
          <p>溫度: {preset.temperature}</p>
        )}
        <p className="text-xs text-gray-400">
          建立時間: {new Date(preset.created_at).toLocaleString('zh-TW')}
        </p>
      </div>

      <div className="mt-3 flex items-center space-x-2">
        {!isActive && (
          <button
            onClick={handleActivate}
            disabled={isActivating}
            className="inline-flex items-center px-3 py-1 text-xs font-medium text-white bg-green-600 rounded hover:bg-green-700 disabled:opacity-50"
          >
            {isActivating ? (
              <RefreshCw className="h-3 w-3 animate-spin" />
            ) : (
              <>
                <Play className="h-3 w-3 mr-1" />
                啟用
              </>
            )}
          </button>
        )}
        <button
          onClick={handleDelete}
          disabled={isDeleting || isActive}
          className="inline-flex items-center px-3 py-1 text-xs font-medium text-red-600 bg-red-50 rounded hover:bg-red-100 disabled:opacity-50"
        >
          {isDeleting ? (
            <RefreshCw className="h-3 w-3 animate-spin" />
          ) : (
            <>
              <Trash2 className="h-3 w-3 mr-1" />
              刪除
            </>
          )}
        </button>
      </div>
    </div>
  )
}

function CreatePresetForm({
  onCreate,
}: {
  onCreate: (preset: PresetCreate) => Promise<void>
}) {
  const [isOpen, setIsOpen] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [formData, setFormData] = useState<PresetCreate>({
    name: '',
    config_type: 'llm',
    api_key: '',
    base_url: '',
    model: 'gpt-4o-mini',
    temperature: 0.0,
    set_active: false,
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name.trim()) return

    setIsCreating(true)
    try {
      await onCreate(formData)
      setIsOpen(false)
      setFormData({
        name: '',
        config_type: 'llm',
        api_key: '',
        base_url: '',
        model: 'gpt-4o-mini',
        temperature: 0.0,
        set_active: false,
      })
    } finally {
      setIsCreating(false)
    }
  }

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
      >
        <Plus className="h-4 w-4 mr-2" />
        建立新預設
      </button>
    )
  }

  return (
    <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
      <h4 className="font-medium text-gray-900 mb-4">建立新預設</h4>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            預設名稱
          </label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="mt-1 w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            placeholder="例如：Production LLM"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            配置類型
          </label>
          <select
            value={formData.config_type}
            onChange={(e) =>
              setFormData({
                ...formData,
                config_type: e.target.value as 'llm' | 'embedding',
              })
            }
            className="mt-1 w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="llm">LLM</option>
            <option value="embedding">Embedding</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            模型
          </label>
          <input
            type="text"
            value={formData.model}
            onChange={(e) => setFormData({ ...formData, model: e.target.value })}
            className="mt-1 w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            placeholder="例如：gpt-4o-mini"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            API 金鑰 (選填)
          </label>
          <input
            type="password"
            value={formData.api_key}
            onChange={(e) =>
              setFormData({ ...formData, api_key: e.target.value })
            }
            className="mt-1 w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            placeholder="留空以使用目前設定"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Base URL (選填)
          </label>
          <input
            type="text"
            value={formData.base_url}
            onChange={(e) =>
              setFormData({ ...formData, base_url: e.target.value })
            }
            className="mt-1 w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            placeholder="留空以使用 OpenAI"
          />
        </div>

        {formData.config_type === 'llm' && (
          <div>
            <label className="block text-sm font-medium text-gray-700">
              溫度
            </label>
            <input
              type="number"
              min="0"
              max="2"
              step="0.1"
              value={formData.temperature}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  temperature: parseFloat(e.target.value),
                })
              }
              className="mt-1 w-32 px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        )}

        <div className="flex items-center">
          <input
            type="checkbox"
            id="set_active"
            checked={formData.set_active}
            onChange={(e) =>
              setFormData({ ...formData, set_active: e.target.checked })
            }
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label
            htmlFor="set_active"
            className="ml-2 text-sm text-gray-700"
          >
            建立後立即啟用
          </label>
        </div>

        <div className="flex items-center space-x-2">
          <button
            type="submit"
            disabled={isCreating || !formData.name.trim()}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {isCreating ? (
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Save className="h-4 w-4 mr-2" />
            )}
            儲存預設
          </button>
          <button
            type="button"
            onClick={() => setIsOpen(false)}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            取消
          </button>
        </div>
      </form>
    </div>
  )
}

export function PresetManager({
  presets,
  activePresets,
  onCreate,
  onActivate,
  onDelete,
  isLoading,
}: PresetManagerProps) {
  const llmPresets = presets.filter((p) => p.config_type === 'llm')
  const embeddingPresets = presets.filter((p) => p.config_type === 'embedding')

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">預設管理</h3>
        <p className="text-sm text-gray-500 mt-1">
          儲存和切換配置預設
        </p>
      </div>

      <div className="p-4 space-y-6">
        <CreatePresetForm onCreate={onCreate} />

        {isLoading ? (
          <div className="text-center py-8 text-gray-500">
            <RefreshCw className="h-8 w-8 mx-auto mb-2 animate-spin" />
            載入預設中...
          </div>
        ) : (
          <>
            {/* LLM Presets */}
            <div>
              <h4 className="text-md font-medium text-gray-900 mb-3">
                LLM 預設
              </h4>
              {llmPresets.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {llmPresets.map((preset) => (
                    <PresetCard
                      key={preset.id}
                      preset={preset}
                      isActive={activePresets.llm?.id === preset.id}
                      onActivate={() => onActivate(preset.id)}
                      onDelete={() => onDelete(preset.id)}
                    />
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">尚無 LLM 預設</p>
              )}
            </div>

            {/* Embedding Presets */}
            <div>
              <h4 className="text-md font-medium text-gray-900 mb-3">
                Embedding 預設
              </h4>
              {embeddingPresets.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {embeddingPresets.map((preset) => (
                    <PresetCard
                      key={preset.id}
                      preset={preset}
                      isActive={activePresets.embedding?.id === preset.id}
                      onActivate={() => onActivate(preset.id)}
                      onDelete={() => onDelete(preset.id)}
                    />
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">尚無 Embedding 預設</p>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
