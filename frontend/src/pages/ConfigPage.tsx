import { useState, useEffect, useCallback } from 'react'
import { AlertCircle, CheckCircle2 } from 'lucide-react'
import { SettingsForm } from '../components/config/SettingsForm'
import { PresetManager } from '../components/config/PresetManager'
import type {
  SettingResponse,
  PresetResponse,
  PresetCreate,
} from '../types/config'

export function ConfigPage() {
  const [settings, setSettings] = useState<Record<string, SettingResponse[]>>(
    {}
  )
  const [presets, setPresets] = useState<PresetResponse[]>([])
  const [activePresets, setActivePresets] = useState<
    Record<string, PresetResponse | null>
  >({})
  const [isLoadingSettings, setIsLoadingSettings] = useState(true)
  const [isLoadingPresets, setIsLoadingPresets] = useState(true)
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

  // Fetch all settings
  const fetchSettings = useCallback(async () => {
    setIsLoadingSettings(true)
    try {
      const response = await fetch('/api/v1/config/settings')
      if (!response.ok) throw new Error('Failed to fetch settings')
      const data = await response.json()
      setSettings(data)
    } catch (err) {
      showError('載入設定失敗')
      console.error('Failed to fetch settings:', err)
    } finally {
      setIsLoadingSettings(false)
    }
  }, [])

  // Fetch all presets
  const fetchPresets = useCallback(async () => {
    setIsLoadingPresets(true)
    try {
      const [presetsResponse, activeResponse] = await Promise.all([
        fetch('/api/v1/config/presets'),
        fetch('/api/v1/config/presets/active'),
      ])

      if (!presetsResponse.ok) throw new Error('Failed to fetch presets')
      if (!activeResponse.ok) throw new Error('Failed to fetch active presets')

      const presetsData = await presetsResponse.json()
      const activeData = await activeResponse.json()

      setPresets(presetsData)
      setActivePresets(activeData)
    } catch (err) {
      showError('載入預設失敗')
      console.error('Failed to fetch presets:', err)
    } finally {
      setIsLoadingPresets(false)
    }
  }, [])

  // Initial data fetch
  useEffect(() => {
    fetchSettings()
    fetchPresets()
  }, [fetchSettings, fetchPresets])

  // Update a single setting
  const handleUpdateSetting = async (key: string, value: string) => {
    const response = await fetch(`/api/v1/config/settings/${key}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ value }),
    })

    if (!response.ok) {
      throw new Error('Failed to update setting')
    }

    const updatedSetting = await response.json()

    // Update local state
    setSettings((prev) => {
      const newSettings = { ...prev }
      const category = updatedSetting.category
      if (newSettings[category]) {
        newSettings[category] = newSettings[category].map((s) =>
          s.key === key ? updatedSetting : s
        )
      }
      return newSettings
    })

    showSuccess(`設定 ${key} 已更新`)
  }

  // Reload from .env
  const handleReload = async () => {
    const response = await fetch('/api/v1/config/reload', {
      method: 'POST',
    })

    if (!response.ok) {
      throw new Error('Failed to reload configuration')
    }

    await fetchSettings()
    showSuccess('設定已從 .env 重新載入')
  }

  // Create a new preset
  const handleCreatePreset = async (preset: PresetCreate) => {
    const response = await fetch('/api/v1/config/presets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(preset),
    })

    if (!response.ok) {
      throw new Error('Failed to create preset')
    }

    await fetchPresets()
    showSuccess(`預設 "${preset.name}" 已建立`)
  }

  // Activate a preset
  const handleActivatePreset = async (id: number) => {
    const response = await fetch(`/api/v1/config/presets/${id}/activate`, {
      method: 'POST',
    })

    if (!response.ok) {
      throw new Error('Failed to activate preset')
    }

    const result = await response.json()
    await fetchPresets()
    showSuccess(`預設 "${result.preset.name}" 已啟用`)
  }

  // Delete a preset
  const handleDeletePreset = async (id: number) => {
    const response = await fetch(`/api/v1/config/presets/${id}`, {
      method: 'DELETE',
    })

    if (!response.ok) {
      throw new Error('Failed to delete preset')
    }

    await fetchPresets()
    showSuccess('預設已刪除')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">系統設定</h1>
        <p className="mt-1 text-sm text-gray-500">
          管理 LLM 參數、嵌入模型和系統配置
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

      {/* Settings Form */}
      <SettingsForm
        settings={settings}
        onUpdate={handleUpdateSetting}
        onReload={handleReload}
        isLoading={isLoadingSettings}
      />

      {/* Preset Manager */}
      <PresetManager
        presets={presets}
        activePresets={activePresets}
        onCreate={handleCreatePreset}
        onActivate={handleActivatePreset}
        onDelete={handleDeletePreset}
        isLoading={isLoadingPresets}
      />
    </div>
  )
}
