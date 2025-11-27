import { useState, useEffect } from 'react'
import { Save, RefreshCw, Check, AlertCircle } from 'lucide-react'
import type { SettingResponse, SettingCategory } from '../../types/config'

interface SettingsFormProps {
  settings: Record<string, SettingResponse[]>
  onUpdate: (key: string, value: string) => Promise<void>
  onReload: () => Promise<void>
  isLoading: boolean
}

const CATEGORY_LABELS: Record<SettingCategory, string> = {
  llm: 'LLM 配置',
  embedding: '嵌入模型',
  vector_db: '向量資料庫',
  general: '一般設定',
}

const CATEGORY_ORDER: SettingCategory[] = ['llm', 'embedding', 'vector_db', 'general']

function SettingInput({
  setting,
  onSave,
}: {
  setting: SettingResponse
  onSave: (value: string) => Promise<void>
}) {
  const [value, setValue] = useState(setting.value)
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    setValue(setting.value)
    setIsEditing(false)
    setError(null)
    setSaved(false)
  }, [setting.value])

  const handleSave = async () => {
    if (value === setting.value) {
      setIsEditing(false)
      return
    }

    // Validation
    if (setting.key === 'llm_temperature') {
      const temp = parseFloat(value)
      if (isNaN(temp) || temp < 0 || temp > 2) {
        setError('溫度必須在 0.0 到 2.0 之間')
        return
      }
    }

    setIsSaving(true)
    setError(null)

    try {
      await onSave(value)
      setIsEditing(false)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (err) {
      setError('儲存失敗')
    } finally {
      setIsSaving(false)
    }
  }

  const isApiKey = setting.key.includes('api_key')
  const isTemperature = setting.key === 'llm_temperature'

  return (
    <div className="py-3">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700">
            {setting.key}
          </label>
          {setting.description && (
            <p className="text-xs text-gray-500 mt-0.5">{setting.description}</p>
          )}
        </div>
        <div className="flex items-center space-x-2">
          {saved && (
            <span className="text-green-600 text-xs flex items-center">
              <Check className="h-3 w-3 mr-1" />
              已儲存
            </span>
          )}
        </div>
      </div>

      <div className="mt-2 flex items-center space-x-2">
        {isApiKey ? (
          <input
            type="password"
            value={value}
            onChange={(e) => {
              setValue(e.target.value)
              setIsEditing(true)
            }}
            className="flex-1 px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            placeholder="API 金鑰"
          />
        ) : isTemperature ? (
          <input
            type="number"
            min="0"
            max="2"
            step="0.1"
            value={value}
            onChange={(e) => {
              setValue(e.target.value)
              setIsEditing(true)
            }}
            className="w-32 px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
        ) : (
          <input
            type="text"
            value={value}
            onChange={(e) => {
              setValue(e.target.value)
              setIsEditing(true)
            }}
            className="flex-1 px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
        )}

        {isEditing && (
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {isSaving ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <Save className="h-4 w-4 mr-1" />
                儲存
              </>
            )}
          </button>
        )}
      </div>

      {error && (
        <p className="mt-1 text-xs text-red-600 flex items-center">
          <AlertCircle className="h-3 w-3 mr-1" />
          {error}
        </p>
      )}
    </div>
  )
}

export function SettingsForm({
  settings,
  onUpdate,
  onReload,
  isLoading,
}: SettingsFormProps) {
  const [selectedCategory, setSelectedCategory] = useState<SettingCategory>('llm')
  const [isReloading, setIsReloading] = useState(false)

  const handleReload = async () => {
    setIsReloading(true)
    try {
      await onReload()
    } finally {
      setIsReloading(false)
    }
  }

  const categories = CATEGORY_ORDER.filter((cat) => settings[cat]?.length > 0)

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">設定管理</h3>
        <button
          onClick={handleReload}
          disabled={isReloading || isLoading}
          className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
        >
          <RefreshCw
            className={`h-4 w-4 mr-2 ${isReloading ? 'animate-spin' : ''}`}
          />
          從 .env 重新載入
        </button>
      </div>

      <div className="flex">
        {/* Category sidebar */}
        <div className="w-48 border-r border-gray-200 p-4">
          <nav className="space-y-1">
            {categories.map((category) => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`w-full text-left px-3 py-2 text-sm rounded-md ${
                  selectedCategory === category
                    ? 'bg-blue-50 text-blue-700 font-medium'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                {CATEGORY_LABELS[category]}
                <span className="ml-2 text-xs text-gray-400">
                  ({settings[category]?.length || 0})
                </span>
              </button>
            ))}
          </nav>
        </div>

        {/* Settings form */}
        <div className="flex-1 p-4">
          <h4 className="text-md font-medium text-gray-900 mb-4">
            {CATEGORY_LABELS[selectedCategory]}
          </h4>

          {isLoading ? (
            <div className="text-center py-8 text-gray-500">
              <RefreshCw className="h-8 w-8 mx-auto mb-2 animate-spin" />
              載入設定中...
            </div>
          ) : settings[selectedCategory]?.length > 0 ? (
            <div className="divide-y divide-gray-200">
              {settings[selectedCategory].map((setting) => (
                <SettingInput
                  key={setting.key}
                  setting={setting}
                  onSave={(value) => onUpdate(setting.key, value)}
                />
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">此類別沒有設定</p>
          )}
        </div>
      </div>
    </div>
  )
}
